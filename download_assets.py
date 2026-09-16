import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
COUNTRY_DIR = ROOT / "ülkeler"
SITE_DIR = ROOT / "unesco dünya mirasları"
DATA_DIR = ROOT / "data"

UNESCO_XML = "https://whc.unesco.org/en/list/xml/"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

UA = (
    "PieceOfPast/1.0 "
    "(https://github.com/mgagames23/PIECE-OF-PAST)"
)

ALIASES = {
    "Türkiye": "Turkey",
    "Turkey": "Turkey",
    "Czechia": "Czech Republic",
    "Viet Nam": "Vietnam",
    "Republic of Korea": "South Korea",
    "Korea, Republic of": "South Korea",
    "Russian Federation": "Russia",
    "United States of America": "United States",
    "United Republic of Tanzania": "Tanzania",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Iran (Islamic Republic of)": "Iran",
    "Lao People's Democratic Republic": "Laos",
    "Moldova, Republic of": "Moldova",
    "Syrian Arab Republic": "Syria",
    "Democratic People's Republic of Korea": "North Korea",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    "Brunei Darussalam": "Brunei",
    "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "Eswatini": "Eswatini",
    "Türkiye*": "Turkey",
}


def clean(value):
    value = re.sub(r'[<>:"/\\|?*]', "-", str(value).strip())
    value = re.sub(r"\s+", " ", value)
    return value.strip(" .")


def local_name(tag):
    """
    XML namespace varsa namespace'i kaldırır.

    Örnek:
        {http://example.com}row
    ->
        row
    """
    if not tag:
        return ""

    if "}" in tag:
        tag = tag.split("}", 1)[1]

    if ":" in tag:
        tag = tag.split(":", 1)[1]

    return tag.strip().lower()


def text_value(node):
    if node is None:
        return ""

    text = "".join(node.itertext())
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def child_text(node, *names):
    """
    Verilen alan adlarından herhangi birini bulur.

    Hem doğrudan çocuklarda hem de alt elemanlarda arama yapar.
    """
    wanted = {str(x).strip().lower() for x in names}

    for child in node.iter():
        if child is node:
            continue

        name = local_name(child.tag)

        if name in wanted:
            value = text_value(child)

            if value:
                return value

    return ""


def find_site_name(row):
    return child_text(
        row,
        "site",
        "name",
        "property",
        "propertyname",
        "site_name",
        "sitename",
    )


def find_site_id(row):
    value = child_text(
        row,
        "id_number",
        "id",
        "idnumber",
        "site_id",
        "siteid",
    )

    if value:
        return value

    for key in (
        "id_number",
        "id",
        "site_id",
        "siteid",
    ):
        if key in row.attrib:
            value = str(row.attrib[key]).strip()

            if value:
                return value

    return ""


def find_year(row):
    return child_text(
        row,
        "year",
        "date",
        "inscription_year",
        "inscriptionyear",
    )


def find_category(row):
    return child_text(
        row,
        "category",
        "type",
    )


def find_region(row):
    return child_text(
        row,
        "region",
    )


def countries(row):
    """
    UNESCO XML'inin farklı sürümlerinde ülke bilgisi
    farklı alanlarda bulunabildiği için birkaç formatı destekler.
    """

    result = []

    def add(value):
        if not value:
            return

        value = re.sub(r"\s+", " ", str(value)).strip()

        if not value:
            return

        # Bazı XML alanlarında ülkeler virgül veya noktalı virgülle gelir.
        parts = re.split(r"\s*[,;/]\s*", value)

        for part in parts:
            part = part.strip()

            if part and part not in result:
                result.append(part)

    # 1) states/state yapısı
    for element in row.iter():
        name = local_name(element.tag)

        if name in (
            "state",
            "statesparty",
            "stateparty",
            "country",
            "countryname",
        ):
            value = text_value(element)

            if value:
                add(value)

    # 2) doğrudan country alanı
    if not result:
        value = child_text(
            row,
            "country",
            "countries",
            "states",
            "state",
            "states_parties",
            "statesparties",
        )

        add(value)

    # 3) attribute üzerinden
    if not result:
        for key, value in row.attrib.items():
            key_name = str(key).lower()

            if key_name in (
                "country",
                "countries",
                "state",
                "states",
            ):
                add(value)

    return result


def parse_unesco_xml(content):
    """
    UNESCO XML'ini mümkün olduğunca toleranslı biçimde parse eder.
    """

    root = ET.fromstring(content)

    rows = []

    # Öncelikle row elemanlarını ara.
    for element in root.iter():
        if local_name(element.tag) == "row":
            rows.append(element)

    # row bulunamazsa property/site elemanlarını dene.
    if not rows:
        candidates = []

        for element in root.iter():
            name = local_name(element.tag)

            if name in (
                "property",
                "site",
                "worldheritagesite",
                "worldheritage",
            ):
                candidates.append(element)

        rows = candidates

    if not rows:
        raise RuntimeError(
            "UNESCO XML icinde veri kaydi bulunamadi. "
            "XML yapisi degismis olabilir."
        )

    return rows


def commons(query):
    try:
        response = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 6,
                "gsrlimit": 10,
                "prop": "imageinfo",
                "iiprop": "url|mime|extmetadata",
                "iiurlwidth": 800,
                "format": "json",
            },
            headers={
                "User-Agent": UA
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        for page in pages.values():
            info_list = page.get("imageinfo", [])

            if not info_list:
                continue

            info = info_list[0]

            mime = info.get("mime", "")

            if mime not in (
                "image/jpeg",
                "image/png",
                "image/webp",
            ):
                continue

            metadata = info.get("extmetadata", {})

            return {
                "url": info.get("thumburl") or info.get("url"),
                "title": page.get("title", ""),
                "license": (
                    metadata
                    .get("LicenseShortName", {})
                    .get("value", "")
                ),
                "artist": (
                    metadata
                    .get("Artist", {})
                    .get("value", "")
                ),
            }

    except Exception as exc:
        print(f"Commons arama hatasi: {query}")
        print(f"  {exc}")

    return None


def save_jpg(url, path):
    response = requests.get(
        url,
        headers={
            "User-Agent": UA
        },
        timeout=60,
    )

    response.raise_for_status()

    image = ImageOps.exif_transpose(
        Image.open(
            io.BytesIO(response.content)
        )
    )

    if image.mode != "RGB":
        background = Image.new(
            "RGB",
            image.size,
            "white",
        )

        if "A" in image.getbands():
            background.paste(
                image,
                mask=image.getchannel("A"),
            )
        else:
            background.paste(image)

        image = background

    image.thumbnail(
        (800, 800),
        Image.Resampling.LANCZOS,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(
        path,
        "JPEG",
        quality=78,
        optimize=True,
    )


def download_country_images(all_countries, sources):
    country_images = {}

    total = len(all_countries)

    for index, country in enumerate(
        all_countries,
        start=1,
    ):
        path = COUNTRY_DIR / f"{clean(country)}.jpg"

        if path.exists():
            country_images[country] = (
                str(path.relative_to(ROOT))
                .replace("\\", "/")
            )
            continue

        query_country = ALIASES.get(
            country,
            country,
        )

        query = f"{query_country} flag"

        print(
            f"[Ulke {index}/{total}] {country}"
        )

        info = commons(query)

        if info and info.get("url"):
            try:
                save_jpg(
                    info["url"],
                    path,
                )

                sources[
                    str(path.relative_to(ROOT))
                ] = info

            except Exception as exc:
                print(
                    f"  Bayrak indirilemedi: {exc}"
                )

        if path.exists():
            country_images[country] = (
                str(path.relative_to(ROOT))
                .replace("\\", "/")
            )

    return country_images


def download_site_images(
    sites,
    sources,
):
    site_images = {}

    total = len(sites)

    for index, site in enumerate(
        sites,
        start=1,
    ):
        countries_list = site["countries"]

        first_country = (
            countries_list[0]
            if countries_list
            else ""
        )

        search_country = ALIASES.get(
            first_country,
            first_country,
        )

        filename = clean(
            f"{first_country} - {site['name']}.jpg"
        )

        path = SITE_DIR / filename

        if path.exists():
            site_images[site["id"]] = (
                str(path.relative_to(ROOT))
                .replace("\\", "/")
            )
            continue

        query = (
            f"{site['name']} "
            f"{search_country} "
            f"UNESCO World Heritage"
        )

        print(
            f"[UNESCO {index}/{total}] "
            f"{site['name']}"
        )

        info = commons(query)

        if info and info.get("url"):
            try:
                save_jpg(
                    info["url"],
                    path,
                )

                sources[
                    str(path.relative_to(ROOT))
                ] = info

            except Exception as exc:
                print(
                    f"  Gorsel indirilemedi: {exc}"
                )

        if path.exists():
            site_images[site["id"]] = (
                str(path.relative_to(ROOT))
                .replace("\\", "/")
            )
        else:
            site_images[site["id"]] = None

    return site_images


def main():
    COUNTRY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SITE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("UNESCO World Heritage List indiriliyor...")

    response = requests.get(
        UNESCO_XML,
        headers={
            "User-Agent": UA
        },
        timeout=60,
    )

    response.raise_for_status()

    print(
        f"UNESCO HTTP durumu: "
        f"{response.status_code}"
    )

    print(
        f"UNESCO XML boyutu: "
        f"{len(response.content)} byte"
    )

    rows = parse_unesco_xml(
        response.content
    )

    print(
        f"XML kayitlari: {len(rows)}"
    )

    sites = []
    all_countries = []

    for row in rows:
        name = find_site_name(row)

        country_list = countries(row)

        if not name:
            continue

        if not country_list:
            print(
                f"  Ulke bulunamadi, atlaniyor: "
                f"{name}"
            )
            continue

        site_id = find_site_id(row)

        if not site_id:
            # ID bulunamazsa site adından güvenli
            # bir fallback ID oluştur.
            site_id = clean(name)

        item = {
            "id": site_id,
            "name": name,
            "countries": country_list,
            "year": find_year(row),
            "category": find_category(row),
            "region": find_region(row),
        }

        sites.append(item)

        for country in country_list:
            if country not in all_countries:
                all_countries.append(country)

    print(
        f"UNESCO alanlari: {len(sites)}"
    )

    print(
        f"Ulkeler: {len(all_countries)}"
    )

    # En kritik kontrol:
    # UNESCO verisi okunamadıysa boş JSON üretme.
    if not sites:
        raise RuntimeError(
            "UNESCO alanlari 0. "
            "Veri okunamadi; bos veri dosyasi "
            "olusturulmayacak."
        )

    if not all_countries:
        raise RuntimeError(
            "Ulke sayisi 0. "
            "UNESCO ulke verileri okunamadi."
        )

    sources = {}

    print("")
    print("Ulke gorselleri indiriliyor...")

    country_images = download_country_images(
        all_countries,
        sources,
    )

    print("")
    print("UNESCO alan gorselleri indiriliyor...")

    site_images = download_site_images(
        sites,
        sources,
    )

    data = {
        "source": "UNESCO World Heritage List",
        "source_url": (
            "https://whc.unesco.org/en/list/"
        ),
        "generated_at": (
            datetime.now(timezone.utc)
            .isoformat()
        ),
        "countries": {},
    }

    for site in sites:
        for country in site["countries"]:
            data["countries"].setdefault(
                country,
                {
                    "image": country_images.get(
                        country
                    ),
                    "sites": [],
                },
            )

            data["countries"][country][
                "sites"
            ].append(
                {
                    "id": site["id"],
                    "name": site["name"],
                    "year": site["year"],
                    "category": site["category"],
                    "region": site["region"],
                    "image": site_images.get(
                        site["id"]
                    ),
                }
            )

    unesco_file = DATA_DIR / "unesco.json"

    sources_file = (
        DATA_DIR / "image_sources.json"
    )

    unesco_file.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    sources_file.write_text(
        json.dumps(
            sources,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("")
    print("==============================")
    print(
        f"UNESCO alanlari: {len(sites)}"
    )
    print(
        f"Ulkeler: {len(all_countries)}"
    )
    print(
        f"Ulke gorselleri: "
        f"{len(country_images)}"
    )
    print(
        f"Kaynaklanan gorseller: "
        f"{len(sources)}"
    )
    print("==============================")
    print("")
    print(
        f"Olusturuldu: {unesco_file}"
    )
    print(
        f"Olusturuldu: {sources_file}"
    )


if __name__ == "__main__":
    main()
