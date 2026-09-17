import sys
import os
import re
import json
import time
import html
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
from io import BytesIO

import requests
from PIL import Image


# ============================================================
# PIECE OF PAST
# UNESCO WORLD HERITAGE ASSET DOWNLOADER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

COUNTRY_FLAG_DIR = BASE_DIR / "ülkeler"
UNESCO_DIR = BASE_DIR / "unesco dünya mirasları"
DATA_DIR = BASE_DIR / "data"

UNESCO_XML_URL = "https://whc.unesco.org/en/list/xml/"
COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"


# ============================================================
# KLASÖRLER
# ============================================================

DATA_DIR.mkdir(parents=True, exist_ok=True)

# UNESCO klasörünü burada oluşturuyoruz.
# Böylece hiçbir görsel bulunmasa bile klasörün oluşması sağlanır.
UNESCO_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "PIECE-OF-PAST-UNESCO-DOWNLOADER/2.0 "
        "(GitHub Actions)"
    )
})


# ============================================================
# ISO COUNTRY CODES
# ============================================================

ISO_CODES = {
    "af": "Afghanistan",
    "al": "Albania",
    "dz": "Algeria",
    "ad": "Andorra",
    "ao": "Angola",
    "ag": "Antigua and Barbuda",
    "ar": "Argentina",
    "am": "Armenia",
    "au": "Australia",
    "at": "Austria",
    "az": "Azerbaijan",
    "bs": "Bahamas",
    "bh": "Bahrain",
    "bd": "Bangladesh",
    "bb": "Barbados",
    "by": "Belarus",
    "be": "Belgium",
    "bz": "Belize",
    "bj": "Benin",
    "bt": "Bhutan",
    "bo": "Bolivia",
    "ba": "Bosnia and Herzegovina",
    "bw": "Botswana",
    "br": "Brazil",
    "bn": "Brunei Darussalam",
    "bg": "Bulgaria",
    "bf": "Burkina Faso",
    "bi": "Burundi",
    "cv": "Cabo Verde",
    "kh": "Cambodia",
    "cm": "Cameroon",
    "ca": "Canada",
    "cf": "Central African Republic",
    "td": "Chad",
    "cl": "Chile",
    "cn": "China",
    "co": "Colombia",
    "km": "Comoros",
    "cg": "Congo",
    "cd": "Democratic Republic of the Congo",
    "cr": "Costa Rica",
    "ci": "Côte d'Ivoire",
    "hr": "Croatia",
    "cu": "Cuba",
    "cy": "Cyprus",
    "cz": "Czechia",
    "dk": "Denmark",
    "dj": "Djibouti",
    "dm": "Dominica",
    "do": "Dominican Republic",
    "ec": "Ecuador",
    "eg": "Egypt",
    "sv": "El Salvador",
    "gq": "Equatorial Guinea",
    "er": "Eritrea",
    "ee": "Estonia",
    "sz": "Eswatini",
    "et": "Ethiopia",
    "fj": "Fiji",
    "fi": "Finland",
    "fr": "France",
    "ga": "Gabon",
    "gm": "Gambia",
    "ge": "Georgia",
    "de": "Germany",
    "gh": "Ghana",
    "gr": "Greece",
    "gd": "Grenada",
    "gt": "Guatemala",
    "gn": "Guinea",
    "gw": "Guinea-Bissau",
    "gy": "Guyana",
    "ht": "Haiti",
    "hn": "Honduras",
    "hu": "Hungary",
    "is": "Iceland",
    "in": "India",
    "id": "Indonesia",
    "ir": "Iran",
    "iq": "Iraq",
    "ie": "Ireland",
    "il": "Israel",
    "it": "Italy",
    "jm": "Jamaica",
    "jp": "Japan",
    "jo": "Jordan",
    "kz": "Kazakhstan",
    "ke": "Kenya",
    "ki": "Kiribati",
    "kp": "North Korea",
    "kr": "South Korea",
    "kw": "Kuwait",
    "kg": "Kyrgyzstan",
    "la": "Laos",
    "lv": "Latvia",
    "lb": "Lebanon",
    "ls": "Lesotho",
    "lr": "Liberia",
    "ly": "Libya",
    "li": "Liechtenstein",
    "lt": "Lithuania",
    "lu": "Luxembourg",
    "mg": "Madagascar",
    "mw": "Malawi",
    "my": "Malaysia",
    "mv": "Maldives",
    "ml": "Mali",
    "mt": "Malta",
    "mh": "Marshall Islands",
    "mr": "Mauritania",
    "mu": "Mauritius",
    "mx": "Mexico",
    "fm": "Micronesia",
    "md": "Moldova",
    "mc": "Monaco",
    "mn": "Mongolia",
    "me": "Montenegro",
    "ma": "Morocco",
    "mz": "Mozambique",
    "mm": "Myanmar",
    "na": "Namibia",
    "nr": "Nauru",
    "np": "Nepal",
    "nl": "Netherlands",
    "nz": "New Zealand",
    "ni": "Nicaragua",
    "ne": "Niger",
    "ng": "Nigeria",
    "mk": "North Macedonia",
    "no": "Norway",
    "om": "Oman",
    "pk": "Pakistan",
    "pw": "Palau",
    "pa": "Panama",
    "pg": "Papua New Guinea",
    "py": "Paraguay",
    "pe": "Peru",
    "ph": "Philippines",
    "pl": "Poland",
    "pt": "Portugal",
    "qa": "Qatar",
    "ro": "Romania",
    "ru": "Russian Federation",
    "rw": "Rwanda",
    "kn": "Saint Kitts and Nevis",
    "lc": "Saint Lucia",
    "vc": "Saint Vincent and the Grenadines",
    "ws": "Samoa",
    "sm": "San Marino",
    "st": "Sao Tome and Principe",
    "sa": "Saudi Arabia",
    "sn": "Senegal",
    "rs": "Serbia",
    "sc": "Seychelles",
    "sl": "Sierra Leone",
    "sg": "Singapore",
    "sk": "Slovakia",
    "si": "Slovenia",
    "sb": "Solomon Islands",
    "so": "Somalia",
    "za": "South Africa",
    "ss": "South Sudan",
    "es": "Spain",
    "lk": "Sri Lanka",
    "sd": "Sudan",
    "sr": "Suriname",
    "se": "Sweden",
    "ch": "Switzerland",
    "sy": "Syrian Arab Republic",
    "tj": "Tajikistan",
    "tz": "United Republic of Tanzania",
    "th": "Thailand",
    "tl": "Timor-Leste",
    "tg": "Togo",
    "to": "Tonga",
    "tt": "Trinidad and Tobago",
    "tn": "Tunisia",
    "tr": "Türkiye",
    "tm": "Turkmenistan",
    "tv": "Tuvalu",
    "ug": "Uganda",
    "ua": "Ukraine",
    "ae": "United Arab Emirates",
    "gb": "United Kingdom",
    "us": "United States of America",
    "uy": "Uruguay",
    "uz": "Uzbekistan",
    "vu": "Vanuatu",
    "va": "Holy See",
    "ve": "Venezuela",
    "vn": "Viet Nam",
    "ye": "Yemen",
    "zm": "Zambia",
    "zw": "Zimbabwe",
}


# ============================================================
# COUNTRY ALIASES
# ============================================================

COUNTRY_ALIASES = {
    "turkey": "Türkiye",
    "turkiye": "Türkiye",
    "türkiye": "Türkiye",

    "russia": "Russian Federation",
    "russian federation": "Russian Federation",

    "vietnam": "Viet Nam",
    "viet nam": "Viet Nam",

    "czech republic": "Czechia",
    "czechia": "Czechia",

    "south korea": "South Korea",
    "republic of korea": "South Korea",

    "north korea": "North Korea",
    "democratic people's republic of korea": "North Korea",

    "cape verde": "Cabo Verde",
    "cabo verde": "Cabo Verde",

    "iran": "Iran",
    "iran islamic republic of": "Iran",

    "bolivia": "Bolivia",
    "plurinational state of bolivia": "Bolivia",

    "laos": "Laos",
    "lao people's democratic republic": "Laos",

    "moldova": "Moldova",
    "republic of moldova": "Moldova",

    "brunei": "Brunei Darussalam",

    "united states": "United States of America",
    "usa": "United States of America",

    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",

    "tanzania": "United Republic of Tanzania",

    "venezuela": "Venezuela",
    "bolivarian republic of venezuela": "Venezuela",
}


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    value = html.unescape(str(value))
    value = value.replace("\r", " ")
    value = value.replace("\n", " ")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize(value):
    value = clean_text(value).lower()

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = value.replace("&", "and")

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return re.sub(
        r"\s+",
        " ",
        value
    ).strip()


def canonical_country_name(name):
    name = clean_text(name)

    if not name:
        return ""

    normalized = normalize(name)

    if normalized in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[normalized]

    for code, official_name in ISO_CODES.items():
        if normalize(official_name) == normalized:
            return official_name

    return name


def safe_filename(name, max_length=170):
    name = clean_text(name)

    name = unicodedata.normalize(
        "NFKD",
        name
    )

    name = "".join(
        c for c in name
        if not unicodedata.combining(c)
    )

    name = re.sub(
        r'[<>:"/\\|?*]',
        "",
        name
    )

    name = re.sub(
        r"\s+",
        " ",
        name
    )

    name = name.strip(" .")

    if len(name) > max_length:
        name = name[:max_length].rstrip()

    return name


# ============================================================
# UNESCO XML FIELD
# ============================================================

def child_text(row, field):
    element = row.find(field)

    if element is None:
        return ""

    return clean_text(element.text)


# ============================================================
# FLAG FILE MAP
# ============================================================

def build_flag_map():
    """
    ülkeler klasöründeki mevcut JPG bayrakları tarar.

    Örnek:
        ülkeler/Albania.jpg

    map:
        "albania" -> Path(...)
    """

    print("=" * 70)
    print("MANUEL ÜLKE BAYRAKLARI TARANIYOR")
    print("=" * 70)

    if not COUNTRY_FLAG_DIR.exists():
        raise RuntimeError(
            "'ülkeler' klasörü bulunamadı."
        )

    flag_map = {}

    for path in COUNTRY_FLAG_DIR.iterdir():

        if not path.is_file():
            continue

        if path.suffix.lower() not in (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ):
            continue

        key = normalize(path.stem)

        if key:
            flag_map[key] = path

    print(
        f"Bulunan manuel bayrak dosyası: "
        f"{len(flag_map)}"
    )

    return flag_map


# ============================================================
# COUNTRY FLAG MATCH
# ============================================================

def find_flag(country_name, flag_map):
    canonical = canonical_country_name(
        country_name
    )

    candidates = [
        country_name,
        canonical,
    ]

    for candidate in candidates:

        key = normalize(candidate)

        if key in flag_map:
            return flag_map[key]

    # Bazı isim farklılıkları için ters alias kontrolü
    normalized_target = normalize(
        canonical
    )

    for key, path in flag_map.items():

        if key == normalized_target:
            return path

    return None


# ============================================================
# UNESCO XML DOWNLOAD
# ============================================================

def download_unesco_xml():

    print("=" * 70)
    print("UNESCO DÜNYA MİRAS LİSTESİ XML İNDİRİLİYOR")
    print("=" * 70)

    response = SESSION.get(
        UNESCO_XML_URL,
        timeout=90
    )

    print(
        f"UNESCO HTTP durumu: "
        f"{response.status_code}"
    )

    print(
        f"UNESCO XML boyutu: "
        f"{len(response.content):,} byte"
    )

    response.raise_for_status()

    return response.content


# ============================================================
# UNESCO XML PARSE
# ============================================================

def parse_unesco_xml(xml_bytes):

    print("=" * 70)
    print("UNESCO XML PARSE EDİLİYOR")
    print("=" * 70)

    root = ET.fromstring(
        xml_bytes
    )

    print(
        f"XML root etiketi: "
        f"{root.tag}"
    )

    rows = root.findall(
        ".//row"
    )

    print(
        f"UNESCO kayıt sayısı: "
        f"{len(rows)}"
    )

    records = []

    for row in rows:

        site = child_text(
            row,
            "site"
        )

        if not site:
            site = child_text(
                row,
                "name"
            )

        if not site:
            continue

        record = {
            "id": child_text(
                row,
                "id_number"
            ),

            "site": site,

            "states": child_text(
                row,
                "states"
            ),

            "iso_code": child_text(
                row,
                "iso_code"
            ),

            "image_url": child_text(
                row,
                "image_url"
            ),

            "http_url": child_text(
                row,
                "http_url"
            ),

            "category": child_text(
                row,
                "category"
            ),

            "region": child_text(
                row,
                "region"
            ),

            "latitude": child_text(
                row,
                "latitude"
            ),

            "longitude": child_text(
                row,
                "longitude"
            ),
        }

        countries = []

        # UNESCO XML'deki gerçek alan:
        # states
        if record["states"]:

            parts = re.split(
                r"\s*,\s*",
                record["states"]
            )

            for country in parts:

                country = clean_text(
                    country
                )

                if country:
                    countries.append(
                        canonical_country_name(
                            country
                        )
                    )

        # states yoksa iso_code kullan
        if not countries and record["iso_code"]:

            codes = re.split(
                r"[,\s;]+",
                record["iso_code"]
            )

            for code in codes:

                code = code.strip().lower()

                if code in ISO_CODES:

                    countries.append(
                        ISO_CODES[code]
                    )

        record["countries"] = list(
            dict.fromkeys(
                countries
            )
        )

        records.append(
            record
        )

    print(
        f"Başarıyla parse edilen kayıt: "
        f"{len(records)}"
    )

    all_countries = set()

    for record in records:

        for country in record["countries"]:

            all_countries.add(
                country
            )

    print(
        "UNESCO kayıtlarında bulunan farklı "
        f"ülke sayısı: {len(all_countries)}"
    )

    return records


# ============================================================
# UNESCO DATA TEST
# ============================================================

def print_unesco_test(records):

    print("=" * 70)
    print("İLK 5 UNESCO KAYDI KONTROLÜ")
    print("=" * 70)

    for record in records[:5]:

        countries = ", ".join(
            record["countries"]
        )

        print(
            f"{record['site']} | "
            f"Ülke: "
            f"{countries or 'YOK'}"
        )


# ============================================================
# FLAG VALIDATION
# ============================================================

def validate_flags(records, flag_map):

    print("=" * 70)
    print("ÜLKE BAYRAKLARI KONTROLÜ")
    print("=" * 70)

    countries = set()

    for record in records:

        for country in record["countries"]:
            countries.add(country)

    found = []
    missing = []

    for country in sorted(
        countries,
        key=lambda x: normalize(x)
    ):

        flag = find_flag(
            country,
            flag_map
        )

        if flag:
            found.append(country)
        else:
            missing.append(country)

    print(
        f"UNESCO ülke sayısı: "
        f"{len(countries)}"
    )

    print(
        f"Manuel bayrağı bulunan ülke: "
        f"{len(found)}"
    )

    print(
        f"Manuel bayrağı bulunamayan ülke: "
        f"{len(missing)}"
    )

    if missing:

        print()
        print(
            "Bayrağı bulunamayan ülkeler:"
        )

        for country in missing[:80]:
            print(
                f"  - {country}"
            )

        if len(missing) > 80:
            print(
                f"  ... "
                f"{len(missing) - 80} ülke daha"
            )

    print()

    print(
        "Mevcut 'ülkeler' klasöründeki "
        "bayraklara DOKUNULMAYACAK."
    )

    print(
        "UNESCO görselleri ayrı klasöre "
        "indirilecek."
    )

    return found, missing


# ============================================================
# CHUNK
# ============================================================

def split_chunks(records):

    total = len(records)

    base = total // 3
    remainder = total % 3

    sizes = [
        base + (1 if remainder >= 1 else 0),
        base + (1 if remainder >= 2 else 0),
        base
    ]

    chunks = []

    start = 0

    for size in sizes:

        chunks.append(
            records[
                start:start + size
            ]
        )

        start += size

    return chunks


def get_chunk(records, mode):

    mapping = {
        "unesco-1": 0,
        "unesco-2": 1,
        "unesco-3": 2,
    }

    if mode not in mapping:

        raise ValueError(
            "Geçersiz mod. "
            "unesco-1, unesco-2 veya unesco-3 kullan."
        )

    chunks = split_chunks(
        records
    )

    index = mapping[mode]

    print("=" * 70)
    print("UNESCO PARÇA BİLGİSİ")
    print("=" * 70)

    print(
        f"Toplam kayıt: {len(records)}"
    )

    print(
        f"1. parça: {len(chunks[0])}"
    )

    print(
        f"2. parça: {len(chunks[1])}"
    )

    print(
        f"3. parça: {len(chunks[2])}"
    )

    print(
        f"Çalıştırılan parça: "
        f"{mode}"
    )

    print(
        f"Bu parçada işlenecek kayıt: "
        f"{len(chunks[index])}"
    )

    return chunks[index]


# ============================================================
# UNESCO COUNTRY DIRECTORY
# ============================================================

def get_unesco_country_dir(country):

    country = canonical_country_name(
        country
    )

    directory = (
        UNESCO_DIR / safe_filename(
            country
        )
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    return directory


# ============================================================
# EXISTING UNESCO IMAGE
# ============================================================

def find_existing_image(
    country_dir,
    site
):

    target = normalize(
        site
    )

    if not country_dir.exists():
        return None

    for path in country_dir.iterdir():

        if not path.is_file():
            continue

        if path.suffix.lower() not in (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ):
            continue

        if normalize(
            path.stem
        ) == target:

            return path

    return None


# ============================================================
# COMMONS LICENSE
# ============================================================

def license_allowed(
    license_name
):

    value = normalize(
        license_name
    )

    if not value:
        return False

    allowed = [
        "cc0",
        "public domain",
        "cc by",
        "cc by sa",
        "cc by nc",
        "cc by nd",
        "cc by nc sa",
        "cc by nc nd",
    ]

    return any(
        item in value
        for item in allowed
    )


# ============================================================
# COMMONS SEARCH
# ============================================================

def commons_search(
    site_name,
    country_name
):

    queries = [
        site_name,
        f"{site_name} {country_name}",
    ]

    best = None

    for search_query in queries:

        try:

            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": search_query,
                "gsrnamespace": 6,
                "gsrlimit": 20,
                "gsrsort": "relevance",
                "prop": "imageinfo",
                "iiprop": (
                    "url|mime|size|extmetadata"
                ),
                "iiurlwidth": 1600,
            }

            response = SESSION.get(
                COMMONS_API_URL,
                params=params,
                timeout=60
            )

            if response.status_code != 200:
                continue

            data = response.json()

            pages = (
                data
                .get("query", {})
                .get("pages", {})
            )

            for page in pages.values():

                title = clean_text(
                    page.get(
                        "title",
                        ""
                    )
                )

                imageinfo = page.get(
                    "imageinfo",
                    []
                )

                if not imageinfo:
                    continue

                info = imageinfo[0]

                url = (
                    info.get("thumburl")
                    or info.get("url")
                )

                original_url = info.get(
                    "url"
                )

                if not url:
                    continue

                mime = clean_text(
                    info.get(
                        "mime",
                        ""
                    )
                ).lower()

                if not mime.startswith(
                    "image/"
                ):
                    continue

                metadata = info.get(
                    "extmetadata",
                    {}
                )

                license_name = clean_text(
                    metadata
                    .get(
                        "LicenseShortName",
                        {}
                    )
                    .get(
                        "value",
                        ""
                    )
                )

                if not license_allowed(
                    license_name
                ):
                    continue

                title_normalized = normalize(
                    title
                )

                site_normalized = normalize(
                    site_name
                )

                country_normalized = normalize(
                    country_name
                )

                # Harita / bayrak / logo vb. görselleri ele
                blocked = [
                    "flag",
                    "map",
                    "locator",
                    "logo",
                    "coat of arms",
                    "icon",
                    "symbol",
                    "stamp",
                    "diagram",
                    "plan",
                ]

                if any(
                    word in title_normalized
                    for word in blocked
                ):
                    continue

                score = 0

                site_words = set(
                    site_normalized.split()
                )

                title_words = set(
                    title_normalized.split()
                )

                common_words = (
                    site_words
                    & title_words
                )

                score += (
                    len(common_words) * 8
                )

                if site_normalized in title_normalized:
                    score += 50

                if country_normalized in title_normalized:
                    score += 15

                width = (
                    info.get("width")
                    or 0
                )

                height = (
                    info.get("height")
                    or 0
                )

                if width >= 1000:
                    score += 5

                if height >= 700:
                    score += 5

                description = clean_text(
                    metadata
                    .get(
                        "ImageDescription",
                        {}
                    )
                    .get(
                        "value",
                        ""
                    )
                )

                artist = clean_text(
                    metadata
                    .get(
                        "Artist",
                        {}
                    )
                    .get(
                        "value",
                        ""
                    )
                )

                if description:
                    score += 2

                if artist:
                    score += 2

                candidate = {
                    "title": title,
                    "url": url,
                    "original_url": original_url,
                    "license": license_name,
                    "artist": artist,
                    "description": description,
                    "score": score,
                    "commons_page": (
                        "https://commons.wikimedia.org/wiki/"
                        + quote(
                            title.replace(
                                " ",
                                "_"
                            )
                        )
                    ),
                }

                if (
                    best is None
                    or candidate["score"]
                    > best["score"]
                ):

                    best = candidate

        except Exception as exc:

            print(
                "[COMMONS ARAMA HATASI] "
                f"{exc}"
            )

        if (
            best is not None
            and best["score"] >= 40
        ):
            break

    return best


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(url):

    response = SESSION.get(
        url,
        timeout=90
    )

    response.raise_for_status()

    content = response.content

    if len(content) < 10_000:

        raise RuntimeError(
            "İndirilen dosya çok küçük."
        )

    return content


# ============================================================
# VALIDATE IMAGE
# ============================================================

def validate_image(content):

    try:

        image = Image.open(
            BytesIO(content)
        )

        width, height = image.size

        if width < 400:
            return False

        if height < 300:
            return False

        image.verify()

        return True

    except Exception:

        return False


# ============================================================
# SAVE JPG
# ============================================================

def save_as_jpg(
    content,
    output_path
):

    image = Image.open(
        BytesIO(content)
    )

    if image.mode != "RGB":

        image = image.convert(
            "RGB"
        )

    image.save(
        output_path,
        "JPEG",
        quality=92,
        optimize=True
    )


# ============================================================
# IMAGE SOURCE DATABASE
# ============================================================

def load_source_database():

    path = (
        DATA_DIR
        / "image_sources.json"
    )

    if not path.exists():
        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            dict
        ):
            return data

    except Exception:

        pass

    return {}


def save_source_database(
    data
):

    path = (
        DATA_DIR
        / "image_sources.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# ONE UNESCO SITE
# ============================================================

def process_site(
    record,
    flag_map,
    source_db
):

    site = record["site"]

    countries = record[
        "countries"
    ]

    if not countries:

        print(
            f"[ATLANDI] "
            f"Ülke bulunamadı: {site}"
        )

        return 0

    downloaded = 0

    for country in countries:

        # ----------------------------------------------------
        # Manuel bayrağın gerçekten mevcut olup olmadığını
        # kontrol ediyoruz.
        #
        # ÖNEMLİ:
        # Bayrak dosyasına dokunulmuyor.
        # ----------------------------------------------------

        flag = find_flag(
            country,
            flag_map
        )

        if flag is None:

            print(
                f"[ATLANDI] Bayrak yok: "
                f"{country} | {site}"
            )

            continue

        # ----------------------------------------------------
        # UNESCO ülke klasörü
        # ----------------------------------------------------

        country_dir = (
            get_unesco_country_dir(
                country
            )
        )

        existing = find_existing_image(
            country_dir,
            site
        )

        if existing:

            print(
                f"[VAR] {country} | "
                f"{existing.name}"
            )

            continue

        print()
        print(
            f"[UNESCO] {site}"
        )

        print(
            f"[ÜLKE] {country}"
        )

        print(
            f"[BAYRAK] {flag.name}"
        )

        # ----------------------------------------------------
        # Wikimedia Commons
        # ----------------------------------------------------

        candidate = commons_search(
            site,
            country
        )

        if candidate is None:

            print(
                "[BULUNAMADI] "
                "Uygun Commons görseli bulunamadı."
            )

            continue

        print(
            f"[COMMONS] "
            f"{candidate['title']}"
        )

        print(
            f"[LİSANS] "
            f"{candidate['license']}"
        )

        print(
            f"[SKOR] "
            f"{candidate['score']}"
        )

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        try:

            content = download_image(
                candidate["url"]
            )

            if not validate_image(
                content
            ):

                print(
                    "[HATA] Görsel doğrulanamadı."
                )

                continue

            filename = (
                safe_filename(site)
                + ".jpg"
            )

            output_path = (
                country_dir
                / filename
            )

            save_as_jpg(
                content,
                output_path
            )

            # ------------------------------------------------
            # Source database
            # ------------------------------------------------

            source_key = (
                f"{country}|{site}"
            )

            source_db[
                source_key
            ] = {

                "site": site,

                "country": country,

                "unesco_id": record[
                    "id"
                ],

                "unesco_url": record[
                    "http_url"
                ],

                "unesco_image_url": record[
                    "image_url"
                ],

                "commons_title": candidate[
                    "title"
                ],

                "commons_page": candidate[
                    "commons_page"
                ],

                "image_url": candidate[
                    "original_url"
                ],

                "download_url": candidate[
                    "url"
                ],

                "license": candidate[
                    "license"
                ],

                "artist": candidate[
                    "artist"
                ],

                "saved_file": str(
                    output_path.relative_to(
                        BASE_DIR
                    )
                ),
            }

            downloaded += 1

            print(
                f"[OK] Kaydedildi: "
                f"{output_path}"
            )

        except Exception as exc:

            print(
                f"[HATA] "
                f"{exc}"
            )

        # Commons API'yi aşırı zorlamamak için
        time.sleep(
            0.4
        )

    return downloaded


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            "Kullanım:"
        )

        print(
            "python download_assets.py unesco-1"
        )

        print(
            "python download_assets.py unesco-2"
        )

        print(
            "python download_assets.py unesco-3"
        )

        sys.exit(1)

    mode = (
        sys.argv[1]
        .strip()
        .lower()
    )

    if mode not in (
        "unesco-1",
        "unesco-2",
        "unesco-3"
    ):

        print(
            f"Geçersiz mod: {mode}"
        )

        sys.exit(1)

    print("=" * 70)
    print("PIECE OF PAST")
    print("UNESCO WORLD HERITAGE ASSET DOWNLOADER")
    print("=" * 70)

    print(
        f"Mod: {mode}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Manuel bayrakları oku
    # --------------------------------------------------------

    flag_map = build_flag_map()

    # --------------------------------------------------------
    # UNESCO XML
    # --------------------------------------------------------

    xml_bytes = download_unesco_xml()

    records = parse_unesco_xml(
        xml_bytes
    )

    if not records:

        raise RuntimeError(
            "UNESCO XML'den kayıt alınamadı."
        )

    # --------------------------------------------------------
    # Kontrol
    # --------------------------------------------------------

    print_unesco_test(
        records
    )

    validate_flags(
        records,
        flag_map
    )

    # --------------------------------------------------------
    # Chunk
    # --------------------------------------------------------

    selected_records = get_chunk(
        records,
        mode
    )

    # --------------------------------------------------------
    # Source database
    # --------------------------------------------------------

    source_db = load_source_database()

    # --------------------------------------------------------
    # UNESCO DIRECTORY
    # --------------------------------------------------------

    UNESCO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 70)
    print(
        f"{mode.upper()} GÖRSELLERİ İNDİRİLİYOR"
    )
    print("=" * 70)

    downloaded_total = 0

    for index, record in enumerate(
        selected_records,
        start=1
    ):

        print()
        print(
            "-" * 70
        )

        print(
            f"[{index}/{len(selected_records)}]"
        )

        print(
            record["site"]
        )

        print(
            "-" * 70
        )

        try:

            downloaded_total += process_site(
                record,
                flag_map,
                source_db
            )

        except Exception as exc:

            print(
                f"[KAYIT HATASI] "
                f"{record['site']}: "
                f"{exc}"
            )

    # --------------------------------------------------------
    # Source database save
    # --------------------------------------------------------

    save_source_database(
        source_db
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("İŞLEM TAMAMLANDI")
    print("=" * 70)

    print(
        f"Yeni indirilen UNESCO görseli: "
        f"{downloaded_total}"
    )

    print(
        f"UNESCO klasörü: "
        f"{UNESCO_DIR}"
    )

    print(
        f"Kaynak veritabanı: "
        f"{DATA_DIR / 'image_sources.json'}"
    )

    print()
    print(
        "MEVCUT BAYRAKLARA DOKUNULMADI."
    )

    print(
        "UNESCO görselleri ayrı "
        "'unesco dünya mirasları' "
        "klasörüne kaydedildi."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
