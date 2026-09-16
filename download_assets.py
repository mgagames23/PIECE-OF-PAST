import io
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageOps


# ============================================================
# AYARLAR
# ============================================================

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

REQUEST_TIMEOUT = 30
IMAGE_TIMEOUT = 60

# Wikimedia API'ye iki istek arasında minimum bekleme.
# Paralel istek YOK.
API_DELAY = 1.0

# 429 / 503 / maxlag durumunda en fazla kaç kez denenecek.
MAX_RETRIES = 6

# UNESCO parçaları
PART_RANGES = {
    "unesco-1": (0, 424),
    "unesco-2": (424, 848),
    "unesco-3": (848, 1273),
}


# ============================================================
# ÜLKE İSİM ALIAŞLARI
# ============================================================

ALIASES = {
    "Türkiye": "Turkey",
    "Turkey": "Turkey",

    "Czechia": "Czech Republic",

    "Viet Nam": "Vietnam",
    "Vietnam": "Vietnam",

    "Republic of Korea": "South Korea",
    "Korea, Republic of": "South Korea",

    "Democratic People's Republic of Korea": "North Korea",

    "Russian Federation": "Russia",
    "Russia": "Russia",

    "United States of America": "United States",

    "United Republic of Tanzania": "Tanzania",

    "Bolivia (Plurinational State of)": "Bolivia",

    "Venezuela (Bolivarian Republic of)": "Venezuela",

    "Iran (Islamic Republic of)": "Iran",

    "Lao People's Democratic Republic": "Laos",

    "Moldova, Republic of": "Moldova",

    "Syrian Arab Republic": "Syria",

    "United Kingdom of Great Britain and Northern Ireland":
        "United Kingdom",

    "Brunei Darussalam": "Brunei",

    "Côte d'Ivoire": "Ivory Coast",

    "Cabo Verde": "Cape Verde",

    "Eswatini": "Eswatini",

    "Türkiye": "Turkey",
}


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": UA,
    "Accept-Encoding": "gzip",
})


_last_api_request = 0.0


def wait_before_api():
    global _last_api_request

    now = time.monotonic()

    elapsed = now - _last_api_request

    if elapsed < API_DELAY:
        time.sleep(
            API_DELAY - elapsed
        )

    _last_api_request = time.monotonic()


# ============================================================
# GENEL YARDIMCILAR
# ============================================================

def clean(value):

    value = re.sub(
        r'[<>:"/\\|?*]',
        "-",
        str(value).strip()
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip(" .")


def local_name(tag):

    if not tag:
        return ""

    if "}" in tag:
        tag = tag.split(
            "}",
            1
        )[1]

    if ":" in tag:
        tag = tag.split(
            ":",
            1
        )[1]

    return tag.strip().lower()


def text_value(node):

    if node is None:
        return ""

    text = "".join(
        node.itertext()
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def child_text(node, *names):

    wanted = {
        str(x).strip().lower()
        for x in names
    }

    for child in node.iter():

        if child is node:
            continue

        name = local_name(
            child.tag
        )

        if name in wanted:

            value = text_value(
                child
            )

            if value:
                return value

    return ""


# ============================================================
# UNESCO XML PARSER
# ============================================================

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

            value = str(
                row.attrib[key]
            ).strip()

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

    result = []

    def add(value):

        if not value:
            return

        value = re.sub(
            r"\s+",
            " ",
            str(value)
        ).strip()

        if not value:
            return

        parts = re.split(
            r"\s*[,;/]\s*",
            value
        )

        for part in parts:

            part = part.strip()

            if (
                part
                and part not in result
            ):
                result.append(part)

    for element in row.iter():

        name = local_name(
            element.tag
        )

        if name in (
            "state",
            "statesparty",
            "stateparty",
            "country",
            "countryname",
        ):

            value = text_value(
                element
            )

            if value:
                add(value)

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

    if not result:

        for key, value in row.attrib.items():

            key_name = str(
                key
            ).lower()

            if key_name in (
                "country",
                "countries",
                "state",
                "states",
            ):

                add(value)

    return result


def parse_unesco_xml(content):

    root = ET.fromstring(
        content
    )

    rows = []

    for element in root.iter():

        if local_name(
            element.tag
        ) == "row":

            rows.append(
                element
            )

    if not rows:

        candidates = []

        for element in root.iter():

            name = local_name(
                element.tag
            )

            if name in (
                "property",
                "site",
                "worldheritagesite",
                "worldheritage",
            ):

                candidates.append(
                    element
                )

        rows = candidates

    if not rows:

        raise RuntimeError(
            "UNESCO XML icinde veri kaydi bulunamadi."
        )

    return rows


def download_unesco():

    print("")
    print(
        "UNESCO World Heritage List indiriliyor..."
    )

    response = SESSION.get(
        UNESCO_XML,
        timeout=60,
    )

    response.raise_for_status()

    print(
        f"UNESCO HTTP: {response.status_code}"
    )

    print(
        f"XML boyutu: {len(response.content):,} byte"
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

        name = find_site_name(
            row
        )

        country_list = countries(
            row
        )

        if not name:
            continue

        if not country_list:
            continue

        site_id = find_site_id(
            row
        )

        if not site_id:
            site_id = clean(
                name
            )

        item = {
            "id": site_id,
            "name": name,
            "countries": country_list,
            "year": find_year(row),
            "category": find_category(row),
            "region": find_region(row),
        }

        sites.append(
            item
        )

        for country in country_list:

            if country not in all_countries:

                all_countries.append(
                    country
                )

    if not sites:

        raise RuntimeError(
            "UNESCO alanlari 0. Veri okunamadi."
        )

    if not all_countries:

        raise RuntimeError(
            "Ulke sayisi 0. Veri okunamadi."
        )

    print(
        f"UNESCO alanlari: {len(sites)}"
    )

    print(
        f"Ulkeler: {len(all_countries)}"
    )

    return sites, all_countries


# ============================================================
# DOSYA / JSON YARDIMCILARI
# ============================================================

def load_json(path, default):

    if not path.exists():
        return default

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception as exc:

        print(
            f"JSON okunamadi: {path}"
        )

        print(
            f"  {exc}"
        )

        return default


def load_existing_sources():

    return load_json(
        DATA_DIR / "image_sources.json",
        {}
    )


# ============================================================
# COMMONS API
# ============================================================

def commons_request(query):

    global _last_api_request

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        wait_before_api()

        try:

            response = SESSION.get(
                COMMONS_API,
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": query,
                    "gsrnamespace": 6,
                    "gsrlimit": 5,
                    "prop": "imageinfo",
                    "iiprop": (
                        "url|mime|extmetadata"
                    ),
                    "iiurlwidth": 800,
                    "maxlag": 5,
                    "format": "json",
                },
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code in (
                429,
                503,
            ):

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:
                        delay = max(
                            5,
                            int(float(retry_after))
                        )

                    except ValueError:

                        delay = min(
                            60,
                            5 * attempt
                        )

                else:

                    delay = min(
                        120,
                        5 * (2 ** (attempt - 1))
                    )

                print("")
                print(
                    f"Commons {response.status_code}: "
                    f"{query}"
                )

                print(
                    f"Bekleniyor: {delay} saniye"
                )

                time.sleep(
                    delay
                )

                continue

            response.raise_for_status()

            data = response.json()

            error = data.get(
                "error"
            )

            if error:

                code = error.get(
                    "code",
                    ""
                )

                if code in (
                    "maxlag",
                    "ratelimited",
                ):

                    delay = min(
                        120,
                        5 * (2 ** (attempt - 1))
                    )

                    print("")
                    print(
                        f"Commons API {code}: "
                        f"{query}"
                    )

                    print(
                        f"Bekleniyor: {delay} saniye"
                    )

                    time.sleep(
                        delay
                    )

                    continue

                return None

            pages = (
                data
                .get("query", {})
                .get("pages", {})
            )

            for page in pages.values():

                imageinfo = page.get(
                    "imageinfo",
                    []
                )

                if not imageinfo:
                    continue

                info = imageinfo[0]

                mime = info.get(
                    "mime",
                    ""
                )

                if mime not in (
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                ):
                    continue

                url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                if not url:
                    continue

                metadata = info.get(
                    "extmetadata",
                    {}
                )

                return {
                    "url": url,
                    "title": page.get(
                        "title",
                        ""
                    ),
                    "license": (
                        metadata
                        .get(
                            "LicenseShortName",
                            {}
                        )
                        .get(
                            "value",
                            ""
                        )
                    ),
                    "artist": (
                        metadata
                        .get(
                            "Artist",
                            {}
                        )
                        .get(
                            "value",
                            ""
                        )
                    ),
                }

            return None

        except requests.RequestException as exc:

            if attempt >= MAX_RETRIES:

                print("")
                print(
                    f"Commons hata: {query}"
                )

                print(
                    f"  {exc}"
                )

                return None

            delay = min(
                120,
                5 * (2 ** (attempt - 1))
            )

            print("")
            print(
                f"Commons baglanti hatasi: "
                f"{query}"
            )

            print(
                f"  {exc}"
            )

            print(
                f"Tekrar denenecek: "
                f"{delay} saniye"
            )

            time.sleep(
                delay
            )

        except Exception as exc:

            print("")
            print(
                f"Commons hata: {query}"
            )

            print(
                f"  {exc}"
            )

            return None

    return None


def commons_search(queries):

    for query in queries:

        if not query:
            continue

        info = commons_request(
            query
        )

        if info:
            return info

    return None


# ============================================================
# GÖRSEL KAYDETME
# ============================================================

def save_jpg(url, path):

    for attempt in range(
        1,
        4
    ):

        try:

            response = SESSION.get(
                url,
                timeout=IMAGE_TIMEOUT,
            )

            if response.status_code in (
                429,
                503,
            ):

                retry_after = response.headers.get(
                    "Retry-After"
                )

                try:
                    delay = max(
                        5,
                        int(float(retry_after))
                    ) if retry_after else 10

                except ValueError:

                    delay = 10

                print(
                    f"  Görsel {response.status_code}, "
                    f"{delay} sn bekleniyor..."
                )

                time.sleep(
                    delay
                )

                continue

            response.raise_for_status()

            image = ImageOps.exif_transpose(
                Image.open(
                    io.BytesIO(
                        response.content
                    )
                )
            )

            if image.mode != "RGB":

                background = Image.new(
                    "RGB",
                    image.size,
                    "white"
                )

                if "A" in image.getbands():

                    background.paste(
                        image,
                        mask=image.getchannel(
                            "A"
                        ),
                    )

                else:

                    background.paste(
                        image
                    )

                image = background

            image.thumbnail(
                (800, 800),
                Image.Resampling.LANCZOS
            )

            path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            image.save(
                path,
                "JPEG",
                quality=78,
                optimize=True
            )

            return True

        except Exception as exc:

            if attempt >= 3:

                print(
                    f"  Görsel indirilemedi: "
                    f"{exc}"
                )

                return False

            time.sleep(
                3 * attempt
            )

    return False


# ============================================================
# ÜLKE GÖRSELLERİ
# ============================================================

def country_task(country):

    path = (
        COUNTRY_DIR
        / f"{clean(country)}.jpg"
    )

    if path.exists():

        return {
            "country": country,
            "path": str(
                path.relative_to(ROOT)
            ).replace("\\", "/"),
            "source": None,
            "existing": True,
        }

    search_name = ALIASES.get(
        country,
        country
    )

    queries = [
        f"{search_name} flag",
        f"flag of {search_name}",
    ]

    info = commons_search(
        queries
    )

    if not info:

        return {
            "country": country,
            "path": None,
            "source": None,
            "existing": False,
        }

    if not save_jpg(
        info["url"],
        path
    ):

        return {
            "country": country,
            "path": None,
            "source": None,
            "existing": False,
        }

    return {
        "country": country,
        "path": str(
            path.relative_to(ROOT)
        ).replace("\\", "/"),
        "source": info,
        "existing": False,
    }


def download_country_images(
    all_countries
):

    print("")
    print(
        "======================================"
    )

    print(
        "ULKE GORSELLERI"
    )

    print(
        "======================================"
    )

    country_images = {}
    sources = {}

    total = len(
        all_countries
    )

    for index, country in enumerate(
        all_countries,
        start=1
    ):

        print(
            f"[Ulke {index}/{total}] "
            f"{country}"
        )

        result = country_task(
            country
        )

        if result["path"]:

            country_images[
                country
            ] = result["path"]

        if result["source"]:

            sources[
                result["path"]
            ] = result["source"]

    print("")
    print(
        f"Ulke gorselleri: "
        f"{len(country_images)}/{total}"
    )

    return (
        country_images,
        sources
    )


# ============================================================
# UNESCO GÖRSELLERİ
# ============================================================

def site_task(site):

    first_country = (
        site["countries"][0]
        if site["countries"]
        else ""
    )

    search_country = ALIASES.get(
        first_country,
        first_country
    )

    filename = clean(
        f"{first_country} - "
        f"{site['name']}.jpg"
    )

    path = (
        SITE_DIR / filename
    )

    if path.exists():

        return {
            "id": site["id"],
            "path": str(
                path.relative_to(ROOT)
            ).replace("\\", "/"),
            "source": None,
            "existing": True,
        }

    queries = [
        (
            f"{site['name']} "
            f"{search_country} "
            f"UNESCO"
        ),
        (
            f"{site['name']} "
            f"{search_country}"
        ),
        site["name"],
    ]

    info = commons_search(
        queries
    )

    if not info:

        return {
            "id": site["id"],
            "path": None,
            "source": None,
            "existing": False,
        }

    if not save_jpg(
        info["url"],
        path
    ):

        return {
            "id": site["id"],
            "path": None,
            "source": None,
            "existing": False,
        }

    return {
        "id": site["id"],
        "path": str(
            path.relative_to(ROOT)
        ).replace("\\", "/"),
        "source": info,
        "existing": False,
    }


def download_site_images(
    sites,
    part_name
):

    start, end = PART_RANGES[
        part_name
    ]

    selected = sites[
        start:end
    ]

    print("")
    print(
        "======================================"
    )

    print(
        f"UNESCO GORSELLERI - {part_name}"
    )

    print(
        f"Aralik: {start + 1}-{end}"
    )

    print(
        f"Bu parca: {len(selected)} site"
    )

    print(
        "======================================"
    )

    site_images = {}
    sources = load_existing_sources()

    total = len(
        selected
    )

    successful = 0

    for local_index, site in enumerate(
        selected,
        start=1
    ):

        global_index = start + local_index

        print("")
        print(
            f"[UNESCO {global_index}/"
            f"{len(sites)}] "
            f"{site['name']}"
        )

        result = site_task(
            site
        )

        site_images[
            site["id"]
        ] = result["path"]

        if result["path"]:

            successful += 1

        if result["source"]:

            sources[
                result["path"]
            ] = result["source"]

    # Diğer parçaların mevcut dosyalarını da JSON'a dahil et.
    for site in sites:

        filename = clean(
            f"{site['countries'][0]} - "
            f"{site['name']}.jpg"
        )

        path = (
            SITE_DIR / filename
        )

        if path.exists():

            site_images[
                site["id"]
            ] = str(
                path.relative_to(ROOT)
            ).replace("\\", "/")

    print("")
    print(
        f"UNESCO gorselleri "
        f"bu parca: "
        f"{successful}/{total}"
    )

    return (
        site_images,
        sources
    )


# ============================================================
# JSON
# ============================================================

def create_json(
    sites,
    country_images,
    site_images,
    sources
):

    data = {
        "source": (
            "UNESCO World Heritage List"
        ),
        "source_url": (
            "https://whc.unesco.org/en/list/"
        ),
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "countries": {},
    }

    for site in sites:

        for country in site[
            "countries"
        ]:

            if country not in data[
                "countries"
            ]:

                data[
                    "countries"
                ][country] = {
                    "image": country_images.get(
                        country
                    ),
                    "sites": [],
                }

            data[
                "countries"
            ][country][
                "sites"
            ].append(
                {
                    "id": site[
                        "id"
                    ],
                    "name": site[
                        "name"
                    ],
                    "year": site[
                        "year"
                    ],
                    "category": site[
                        "category"
                    ],
                    "region": site[
                        "region"
                    ],
                    "image": site_images.get(
                        site["id"]
                    ),
                }
            )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    unesco_file = (
        DATA_DIR / "unesco.json"
    )

    sources_file = (
        DATA_DIR
        / "image_sources.json"
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
    print(
        f"JSON olusturuldu: "
        f"{unesco_file}"
    )

    print(
        f"Kaynak JSON olusturuldu: "
        f"{sources_file}"
    )


# ============================================================
# MOD / ARGÜMAN
# ============================================================

def get_mode():

    if len(sys.argv) >= 2:

        return sys.argv[1].strip().lower()

    return "countries"


# ============================================================
# MAIN
# ============================================================

def main():

    mode = get_mode()

    valid_modes = {
        "countries",
        "unesco-1",
        "unesco-2",
        "unesco-3",
    }

    if mode not in valid_modes:

        raise SystemExit(
            "Gecersiz mod. "
            "Kullan: countries, unesco-1, "
            "unesco-2 veya unesco-3"
        )

    print("")
    print(
        "======================================"
    )

    print(
        " PIECE OF PAST - UNESCO DOWNLOADER"
    )

    print(
        f" MOD: {mode}"
    )

    print(
        "======================================"
    )

    COUNTRY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    SITE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # UNESCO VERİSİNİ HER AŞAMADA OKU
    # --------------------------------------------------------

    sites, all_countries = (
        download_unesco()
    )

    # --------------------------------------------------------
    # MEVCUT ÜLKE GÖRSELLERİNİ BUL
    # --------------------------------------------------------

    country_images = {}

    for country in all_countries:

        path = (
            COUNTRY_DIR
            / f"{clean(country)}.jpg"
        )

        if path.exists():

            country_images[
                country
            ] = str(
                path.relative_to(ROOT)
            ).replace("\\", "/")

    # --------------------------------------------------------
    # ÜLKELER
    # --------------------------------------------------------

    if mode == "countries":

        country_images, country_sources = (
            download_country_images(
                all_countries
            )
        )

        existing_sources = (
            load_existing_sources()
        )

        existing_sources.update(
            country_sources
        )

        # UNESCO site görselleri henüz yok.
        site_images = {}

        for site in sites:

            filename = clean(
                f"{site['countries'][0]} - "
                f"{site['name']}.jpg"
            )

            path = (
                SITE_DIR / filename
            )

            if path.exists():

                site_images[
                    site["id"]
                ] = str(
                    path.relative_to(ROOT)
                ).replace("\\", "/")

        create_json(
            sites,
            country_images,
            site_images,
            existing_sources
        )

        print("")
        print(
            "ULKE ASAMASI TAMAMLANDI."
        )

        print(
            f"Toplam ulke: "
            f"{len(all_countries)}"
        )

        print(
            f"Indirilen/mevcut ulke: "
            f"{len(country_images)}"
        )

        return

    # --------------------------------------------------------
    # UNESCO PARÇASI
    # --------------------------------------------------------

    site_images, site_sources = (
        download_site_images(
            sites,
            mode
        )
    )

    # Tüm mevcut ülke görsellerini tekrar oku.
    country_images = {}

    for country in all_countries:

        path = (
            COUNTRY_DIR
            / f"{clean(country)}.jpg"
        )

        if path.exists():

            country_images[
                country
            ] = str(
                path.relative_to(ROOT)
            ).replace("\\", "/")

    # Mevcut kaynakları koru.
    sources = load_existing_sources()

    sources.update(
        site_sources
    )

    # Tüm mevcut site görsellerini JSON'a dahil et.
    all_site_images = {}

    for site in sites:

        filename = clean(
            f"{site['countries'][0]} - "
            f"{site['name']}.jpg"
        )

        path = (
            SITE_DIR / filename
        )

        if path.exists():

            all_site_images[
                site["id"]
            ] = str(
                path.relative_to(ROOT)
            ).replace("\\", "/")

    # Bu çalıştırmada bulunanlar da eklensin.
    all_site_images.update(
        site_images
    )

    create_json(
        sites,
        country_images,
        all_site_images,
        sources
    )

    print("")
    print(
        "======================================"
    )

    print(
        f"Toplam UNESCO alani: "
        f"{len(sites)}"
    )

    print(
        f"Toplam ulke: "
        f"{len(all_countries)}"
    )

    print(
        f"Toplam mevcut ulke gorseli: "
        f"{len(country_images)}"
    )

    print(
        f"Toplam mevcut UNESCO gorseli: "
        f"{sum(1 for x in all_site_images.values() if x)}"
    )

    print(
        f"Tamamlanan parca: {mode}"
    )

    print(
        "======================================"
    )

    print("")
    print(
        "UNESCO asamasi tamamlandi."
    )


if __name__ == "__main__":
    main()
