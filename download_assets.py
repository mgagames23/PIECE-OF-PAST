import io
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Aynı anda kaç görsel indirilecek?
# 8 güvenli ve yeterince hızlı bir değerdir.
MAX_WORKERS = 8

# HTTP timeout
REQUEST_TIMEOUT = 25
IMAGE_TIMEOUT = 40

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
}


# ============================================================
# GENEL YARDIMCI FONKSİYONLAR
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
    """
    XML namespace bilgisini kaldırır.

    Örnek:
    {namespace}row -> row
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
# UNESCO XML
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

    # UNESCO'nun state yapısı
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

    # Alternatif alanlar
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

    # Attribute
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
            "UNESCO XML icinde veri "
            "kaydi bulunamadi."
        )

    return rows


def download_unesco():

    print(
        "UNESCO World Heritage List indiriliyor..."
    )

    response = requests.get(
        UNESCO_XML,
        headers={
            "User-Agent": UA
        },
        timeout=60,
    )

    response.raise_for_status()

    print(
        f"UNESCO HTTP: "
        f"{response.status_code}"
    )

    print(
        f"XML boyutu: "
        f"{len(response.content):,} byte"
    )

    rows = parse_unesco_xml(
        response.content
    )

    print(
        f"XML kayitlari: "
        f"{len(rows)}"
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
            "UNESCO alanlari 0. "
            "Veri okunamadi."
        )

    if not all_countries:

        raise RuntimeError(
            "Ulke sayisi 0. "
            "Veri okunamadi."
        )

    print(
        f"UNESCO alanlari: "
        f"{len(sites)}"
    )

    print(
        f"Ulkeler: "
        f"{len(all_countries)}"
    )

    return sites, all_countries


# ============================================================
# COMMONS
# ============================================================

def commons(query):

    try:

        response = requests.get(
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
                "format": "json",
            },
            headers={
                "User-Agent": UA
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        pages = (
            response
            .json()
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

            metadata = info.get(
                "extmetadata",
                {}
            )

            return {
                "url": (
                    info.get("thumburl")
                    or info.get("url")
                ),
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

    except Exception as exc:

        print(
            f"Commons hata: {query}"
        )

        print(
            f"  {exc}"
        )

    return None


def save_jpg(url, path):

    response = requests.get(
        url,
        headers={
            "User-Agent": UA
        },
        timeout=IMAGE_TIMEOUT,
    )

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

    info = commons(
        f"{search_name} flag"
    )

    if not info:
        return {
            "country": country,
            "path": None,
            "source": None,
            "existing": False,
        }

    try:

        save_jpg(
            info["url"],
            path
        )

        return {
            "country": country,
            "path": str(
                path.relative_to(ROOT)
            ).replace("\\", "/"),
            "source": info,
            "existing": False,
        }

    except Exception as exc:

        print(
            f"  Bayrak indirilemedi: "
            f"{country} - {exc}"
        )

        return {
            "country": country,
            "path": None,
            "source": None,
            "existing": False,
        }


def download_country_images(
    all_countries
):

    print("")
    print(
        "Ulke gorselleri indiriliyor..."
    )

    results = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                country_task,
                country
            ): country
            for country in all_countries
        }

        total = len(futures)

        completed = 0

        for future in as_completed(
            futures
        ):

            completed += 1

            country = futures[
                future
            ]

            try:

                result = future.result()

                results.append(
                    result
                )

                print(
                    f"[Ulke "
                    f"{completed}/{total}] "
                    f"{country}"
                )

            except Exception as exc:

                print(
                    f"[Ulke hata "
                    f"{completed}/{total}] "
                    f"{country}: "
                    f"{exc}"
                )

    country_images = {}
    sources = {}

    for result in results:

        country = result[
            "country"
        ]

        path = result[
            "path"
        ]

        if path:

            country_images[
                country
            ] = path

        if result[
            "source"
        ]:

            sources[path] = result[
                "source"
            ]

    print(
        f"Ulke gorselleri: "
        f"{len(country_images)}/"
        f"{len(all_countries)}"
    )

    return country_images, sources


# ============================================================
# UNESCO SITE GÖRSELLERİ
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
        }

    query = (
        f"{site['name']} "
        f"{search_country} "
        f"UNESCO World Heritage"
    )

    info = commons(
        query
    )

    if not info:

        return {
            "id": site["id"],
            "path": None,
            "source": None,
        }

    try:

        save_jpg(
            info["url"],
            path
        )

        return {
            "id": site["id"],
            "path": str(
                path.relative_to(ROOT)
            ).replace("\\", "/"),
            "source": info,
        }

    except Exception as exc:

        print(
            f"  Site gorseli "
            f"indirilemedi: "
            f"{site['name']} - "
            f"{exc}"
        )

        return {
            "id": site["id"],
            "path": None,
            "source": None,
        }


def download_site_images(
    sites
):

    print("")
    print(
        "UNESCO alan gorselleri "
        "indiriliyor..."
    )

    site_images = {}
    sources = {}

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                site_task,
                site
            ): site
            for site in sites
        }

        total = len(futures)

        completed = 0

        for future in as_completed(
            futures
        ):

            completed += 1

            site = futures[
                future
            ]

            try:

                result = future.result()

                site_id = result[
                    "id"
                ]

                site_images[
                    site_id
                ] = result[
                    "path"
                ]

                if result[
                    "source"
                ] and result[
                    "path"
                ]:

                    sources[
                        result["path"]
                    ] = result[
                        "source"
                    ]

                print(
                    f"[Site "
                    f"{completed}/{total}] "
                    f"{site['name']}"
                )

            except Exception as exc:

                print(
                    f"[Site hata "
                    f"{completed}/{total}] "
                    f"{site['name']}: "
                    f"{exc}"
                )

                site_images[
                    site["id"]
                ] = None

    successful = sum(
        1
        for value in site_images.values()
        if value
    )

    print(
        f"UNESCO gorselleri: "
        f"{successful}/{len(sites)}"
    )

    return site_images, sources


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
# MAIN
# ============================================================

def main():

    print("")
    print(
        "======================================"
    )
    print(
        " PIECE OF PAST - UNESCO DOWNLOADER"
    )
    print(
        "======================================"
    )
    print("")

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
    # 1. UNESCO VERİSİ
    # --------------------------------------------------------

    sites, all_countries = (
        download_unesco()
    )

    # --------------------------------------------------------
    # 2. ÜLKE GÖRSELLERİ
    # --------------------------------------------------------

    country_images, country_sources = (
        download_country_images(
            all_countries
        )
    )

    # --------------------------------------------------------
    # 3. UNESCO ALAN GÖRSELLERİ
    # --------------------------------------------------------

    site_images, site_sources = (
        download_site_images(
            sites
        )
    )

    # --------------------------------------------------------
    # 4. KAYNAKLARI BİRLEŞTİR
    # --------------------------------------------------------

    sources = {}

    sources.update(
        country_sources
    )

    sources.update(
        site_sources
    )

    # --------------------------------------------------------
    # 5. JSON
    # --------------------------------------------------------

    create_json(
        sites,
        country_images,
        site_images,
        sources
    )

    # --------------------------------------------------------
    # 6. SONUÇ
    # --------------------------------------------------------

    print("")
    print(
        "======================================"
    )

    print(
        f"UNESCO alanlari: "
        f"{len(sites)}"
    )

    print(
        f"Ulkeler: "
        f"{len(all_countries)}"
    )

    print(
        f"Ulke gorselleri: "
        f"{len(country_images)}"
    )

    print(
        f"UNESCO gorselleri: "
        f"{sum(1 for x in site_images.values() if x)}"
        f"/{len(sites)}"
    )

    print(
        "======================================"
    )

    print("")
    print(
        "UNESCO islemi tamamlandi."
    )


if __name__ == "__main__":
    main()
