import sys
import os
import re
import json
import time
import html
import hashlib
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image


# ============================================================
# PIECE OF PAST
# UNESCO WORLD HERITAGE ASSET DOWNLOADER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UNESCO_DIR = BASE_DIR / "unesco dünya mirasları"
COUNTRY_DIR = BASE_DIR / "ülkeler"
DATA_DIR = BASE_DIR / "data"

UNESCO_XML_URL = "https://whc.unesco.org/en/list/xml/"

COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"

UNESCO_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HTTP
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "PIECE-OF-PAST-UNESCO-ASSET-DOWNLOADER/1.0 "
        "(GitHub Actions; educational/game asset collection)"
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
# COUNTRY NAME ALIASES
# ============================================================

COUNTRY_ALIASES = {
    "turkey": "Türkiye",
    "türkiye": "Türkiye",
    "turkiye": "Türkiye",

    "russian federation": "Russian Federation",
    "russia": "Russian Federation",

    "iran": "Iran",
    "iran islamic republic of": "Iran",

    "viet nam": "Viet Nam",
    "vietnam": "Viet Nam",

    "venezuela": "Venezuela",
    "venezuela bolivarian republic of": "Venezuela",

    "bolivia": "Bolivia",
    "bolivia plurinational state of": "Bolivia",

    "tanzania": "United Republic of Tanzania",
    "united republic of tanzania": "United Republic of Tanzania",

    "laos": "Laos",
    "lao people's democratic republic": "Laos",

    "moldova": "Moldova",
    "republic of moldova": "Moldova",

    "czech republic": "Czechia",
    "czechia": "Czechia",

    "south korea": "South Korea",
    "republic of korea": "South Korea",

    "north korea": "North Korea",
    "democratic people's republic of korea": "North Korea",

    "cape verde": "Cabo Verde",
    "cabo verde": "Cabo Verde",

    "iran islamic republic": "Iran",

    "brunei": "Brunei Darussalam",

    "micronesia": "Micronesia",

    "holy see": "Holy See",

    "united states": "United States of America",
    "usa": "United States of America",

    "united kingdom": "United Kingdom",
    "uk": "United Kingdom",
}


# ============================================================
# HELPERS
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

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = value.replace("&", "and")

    value = re.sub(r"[^a-z0-9]+", " ", value)

    return re.sub(r"\s+", " ", value).strip()


def safe_filename(value, max_length=160):
    value = clean_text(value)

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = re.sub(r'[<>:"/\\|?*]', "", value)
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" .")

    if len(value) > max_length:
        value = value[:max_length].rstrip()

    return value


def get_child_text(row, name):
    element = row.find(name)

    if element is None:
        return ""

    return clean_text(element.text)


def parse_iso_codes(value):
    if not value:
        return []

    result = []

    for item in re.split(r"[,\s;]+", value):
        code = item.strip().lower()

        if code in ISO_CODES:
            result.append(code)

    return list(dict.fromkeys(result))


def canonical_country_name(name):
    name = clean_text(name)

    if not name:
        return ""

    key = normalize(name)

    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]

    for code, official_name in ISO_CODES.items():
        if normalize(official_name) == key:
            return official_name

    return name


# ============================================================
# COUNTRY DIRECTORY
# ============================================================

def find_country_directory(country_name):
    """
    Finds the manually uploaded country directory.

    IMPORTANT:
    This function NEVER creates, deletes or changes country folders.
    """

    if not COUNTRY_DIR.exists():
        return None

    canonical = canonical_country_name(country_name)
    target = normalize(canonical)

    candidates = []

    for path in COUNTRY_DIR.iterdir():
        if not path.is_dir():
            continue

        candidates.append(path)

        if normalize(path.name) == target:
            return path

    # Common Turkish / English naming variations
    for path in candidates:
        n = normalize(path.name)

        if n == normalize(country_name):
            return path

        if n == normalize(canonical):
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
        timeout=60
    )

    print(f"UNESCO HTTP durumu: {response.status_code}")
    print(
        f"UNESCO XML boyutu: "
        f"{len(response.content):,} byte"
    )

    response.raise_for_status()

    return response.content


# ============================================================
# UNESCO XML PARSER
# ============================================================

def parse_unesco_xml(xml_bytes):
    print("=" * 70)
    print("UNESCO XML PARSE EDİLİYOR")
    print("=" * 70)

    root = ET.fromstring(xml_bytes)

    print(f"XML root etiketi: {root.tag}")

    rows = root.findall(".//row")

    print(f"UNESCO kayıt sayısı: {len(rows)}")

    records = []

    for row in rows:
        site = get_child_text(row, "site")

        if not site:
            site = get_child_text(row, "name")

        if not site:
            continue

        id_number = get_child_text(row, "id_number")
        image_url = get_child_text(row, "image_url")
        http_url = get_child_text(row, "http_url")

        states = get_child_text(row, "states")
        iso_code = get_child_text(row, "iso_code")

        # ====================================================
        # ASIL DÜZELTME:
        #
        # UNESCO XML:
        #
        # <states>Canada,United States of America</states>
        # <iso_code>ca,us</iso_code>
        #
        # ====================================================

        country_names = []

        if states:
            for country in re.split(r"\s*,\s*", states):
                country = clean_text(country)

                if country:
                    country_names.append(
                        canonical_country_name(country)
                    )

        country_names = list(
            dict.fromkeys(country_names)
        )

        iso_codes = parse_iso_codes(iso_code)

        # Eğer states alanı herhangi bir nedenle eksikse,
        # iso_code üzerinden ülke isimlerini çıkar.
        if not country_names and iso_codes:
            for code in iso_codes:
                country_names.append(
                    ISO_CODES[code]
                )

        records.append({
            "id": id_number,
            "site": site,
            "countries": country_names,
            "iso_codes": iso_codes,
            "image_url": image_url,
            "http_url": http_url,
            "category": get_child_text(row, "category"),
            "region": get_child_text(row, "region"),
            "latitude": get_child_text(row, "latitude"),
            "longitude": get_child_text(row, "longitude"),
        })

    print(
        f"Başarıyla parse edilen kayıt: "
        f"{len(records)}"
    )

    country_set = set()

    for record in records:
        country_set.update(
            record["countries"]
        )

    print(
        "UNESCO kayıtlarında bulunan farklı "
        f"ülke sayısı: {len(country_set)}"
    )

    return records


# ============================================================
# UNESCO VALIDATION
# ============================================================

def validate_unesco_data(records):
    print("=" * 70)
    print("İLK 5 UNESCO KAYDI KONTROLÜ")
    print("=" * 70)

    for record in records[:5]:
        countries = ", ".join(
            record["countries"]
        )

        print(
            f"{record['site']} | "
            f"Ülke: {countries or 'YOK'}"
        )

    print("=" * 70)
    print("ÜLKE BAYRAKLARI KONTROLÜ")
    print("=" * 70)

    country_set = set()

    for record in records:
        country_set.update(
            record["countries"]
        )

    print(
        "UNESCO kayıtlarında bulunan farklı "
        f"ülke sayısı: {len(country_set)}"
    )

    if not country_set:
        raise RuntimeError(
            "UNESCO XML kayıtlarından ülke bilgisi "
            "çıkarılamadı."
        )

    missing = []

    for country in sorted(country_set):
        directory = find_country_directory(
            country
        )

        if directory is None:
            missing.append(country)

    print(
        f"UNESCO ülkelerinin {len(country_set)} "
        f"tanesinden {len(country_set) - len(missing)} "
        "tanesi 'ülkeler' klasöründe bulundu."
    )

    if missing:
        print()
        print(
            "UYARI: 'ülkeler' klasöründe bulunamayan "
            "ülkeler:"
        )

        for country in missing[:50]:
            print(f"  - {country}")

        if len(missing) > 50:
            print(
                f"  ... ve {len(missing) - 50} ülke daha"
            )

        print()
        print(
            "Mevcut manuel bayrak klasörlerine "
            "dokunulmayacak."
        )


# ============================================================
# CHUNK SYSTEM
# ============================================================

def get_chunk(records, mode):
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
            records[start:start + size]
        )

        start += size

    mapping = {
        "unesco-1": 0,
        "unesco-2": 1,
        "unesco-3": 2,
    }

    if mode not in mapping:
        raise ValueError(
            "Geçersiz mod. "
            "unesco-1 / unesco-2 / unesco-3 kullan."
        )

    index = mapping[mode]

    selected = chunks[index]

    print("=" * 70)
    print("UNESCO PARÇA BİLGİSİ")
    print("=" * 70)

    print(f"Toplam UNESCO kaydı: {total}")
    print(f"1. parça: {len(chunks[0])}")
    print(f"2. parça: {len(chunks[1])}")
    print(f"3. parça: {len(chunks[2])}")
    print(
        f"Çalıştırılan parça: {mode} "
        f"({len(selected)} kayıt)"
    )

    return selected


# ============================================================
# EXISTING IMAGE CHECK
# ============================================================

def image_already_exists(country_dir, site):
    if country_dir is None:
        return None

    target = normalize(site)

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

        if normalize(path.stem) == target:
            return path

    return None


# ============================================================
# COMMONS SEARCH
# ============================================================

def commons_search(site_name, country_name):
    queries = [
        site_name,
        f"{site_name} {country_name}",
    ]

    best = None

    for query in queries:
        try:
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 6,
                "gsrlimit": 20,
                "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata",
                "iiurlwidth": 1600,
            }

            response = SESSION.get(
                COMMONS_API_URL,
                params=params,
                timeout=45
            )

            if response.status_code != 200:
                continue

            data = response.json()

            pages = (
                data.get("query", {})
                .get("pages", {})
            )

            for page in pages.values():
                title = clean_text(
                    page.get("title", "")
                )

                imageinfo = page.get(
                    "imageinfo",
                    []
                )

                if not imageinfo:
                    continue

                info = imageinfo[0]

                url = info.get("thumburl") or info.get("url")

                if not url:
                    continue

                mime = (
                    info.get("mime")
                    or ""
                ).lower()

                if not mime.startswith("image/"):
                    continue

                metadata = info.get(
                    "extmetadata",
                    {}
                )

                license_name = clean_text(
                    metadata.get(
                        "LicenseShortName",
                        {}
                    ).get("value", "")
                )

                artist = clean_text(
                    metadata.get(
                        "Artist",
                        {}
                    ).get("value", "")
                )

                description = clean_text(
                    metadata.get(
                        "ImageDescription",
                        {}
                    ).get("value", "")
                )

                # ------------------------------------------------
                # License filtering
                # ------------------------------------------------

                license_lower = license_name.lower()

                allowed_license = any(
                    x in license_lower
                    for x in [
                        "cc0",
                        "cc by",
                        "cc-by",
                        "cc by-sa",
                        "cc-by-sa",
                        "public domain",
                        "pd"
                    ]
                )

                if not allowed_license:
                    continue

                # ------------------------------------------------
                # Bad / generic Wikimedia files
                # ------------------------------------------------

                title_lower = title.lower()

                blocked_words = [
                    "flag",
                    "map",
                    "logo",
                    "coat of arms",
                    "locator",
                    "icon",
                    "symbol",
                    "stamp",
                    "diagram",
                ]

                if any(
                    word in title_lower
                    for word in blocked_words
                ):
                    continue

                # ------------------------------------------------
                # Scoring
                # ------------------------------------------------

                score = 0

                normalized_site = normalize(
                    site_name
                )

                normalized_title = normalize(
                    title
                )

                normalized_country = normalize(
                    country_name
                )

                site_words = set(
                    normalized_site.split()
                )

                title_words = set(
                    normalized_title.split()
                )

                common_words = (
                    site_words & title_words
                )

                score += len(common_words) * 8

                if normalized_site in normalized_title:
                    score += 50

                if normalized_country in normalized_title:
                    score += 15

                if artist:
                    score += 2

                if description:
                    score += 2

                width = info.get("width") or 0
                height = info.get("height") or 0

                if width >= 1000:
                    score += 5

                if height >= 700:
                    score += 5

                candidate = {
                    "title": title,
                    "url": url,
                    "original_url": info.get("url"),
                    "license": license_name,
                    "artist": artist,
                    "description": description,
                    "score": score,
                    "commons_page": (
                        "https://commons.wikimedia.org/wiki/"
                        + quote(
                            title.replace(" ", "_")
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
                f"Commons araması başarısız: "
                f"{exc}"
            )

        if best and best["score"] >= 40:
            break

    return best


# ============================================================
# IMAGE DOWNLOAD
# ============================================================

def download_image(url):
    response = SESSION.get(
        url,
        timeout=90,
        stream=True
    )

    response.raise_for_status()

    content = response.content

    if len(content) < 10_000:
        raise RuntimeError(
            "Görsel çok küçük / geçersiz."
        )

    return content


# ============================================================
# IMAGE VALIDATION
# ============================================================

def validate_image(content):
    try:
        from io import BytesIO

        image = Image.open(
            BytesIO(content)
        )

        image.verify()

        image = Image.open(
            BytesIO(content)
        )

        width, height = image.size

        if width < 400 or height < 300:
            return False

        return True

    except Exception:
        return False


# ============================================================
# SAVE IMAGE
# ============================================================

def save_jpg(content, output_path):
    from io import BytesIO

    image = Image.open(
        BytesIO(content)
    )

    if image.mode not in (
        "RGB",
        "L"
    ):
        image = image.convert("RGB")

    image.save(
        output_path,
        "JPEG",
        quality=92,
        optimize=True
    )


# ============================================================
# SOURCE DATABASE
# ============================================================

def load_source_database():
    path = DATA_DIR / "image_sources.json"

    if not path.exists():
        return {}

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def save_source_database(data):
    path = DATA_DIR / "image_sources.json"

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# PROCESS ONE UNESCO SITE
# ============================================================

def process_site(record, source_db):
    site = record["site"]
    countries = record["countries"]

    if not countries:
        print(
            f"[ATLANDI] Ülke yok: {site}"
        )
        return 0

    downloaded_count = 0

    for country in countries:

        country_dir = find_country_directory(
            country
        )

        if country_dir is None:
            print(
                f"[ATLANDI] Bayrak klasörü yok: "
                f"{country} | {site}"
            )
            continue

        existing = image_already_exists(
            country_dir,
            site
        )

        if existing:
            print(
                f"[VAR] {country} / "
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

        candidate = commons_search(
            site,
            country
        )

        if candidate is None:
            print(
                "[BULUNAMADI] Commons'ta "
                "uygun görsel bulunamadı."
            )
            continue

        print(
            f"[COMMONS] {candidate['title']}"
        )

        print(
            f"[LİSANS] "
            f"{candidate['license']}"
        )

        print(
            f"[SKOR] "
            f"{candidate['score']}"
        )

        try:
            content = download_image(
                candidate["url"]
            )

            if not validate_image(content):
                print(
                    "[HATA] Geçersiz veya küçük görsel."
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

            save_jpg(
                content,
                output_path
            )

            source_key = (
                f"{country}|{site}"
            )

            source_db[source_key] = {
                "site": site,
                "country": country,
                "unesco_id": record["id"],
                "unesco_url": record["http_url"],
                "unesco_image_url": record["image_url"],
                "commons_title": candidate["title"],
                "commons_page": candidate["commons_page"],
                "image_url": candidate["original_url"],
                "download_url": candidate["url"],
                "license": candidate["license"],
                "artist": candidate["artist"],
                "saved_file": str(
                    output_path.relative_to(
                        BASE_DIR
                    )
                ),
            }

            downloaded_count += 1

            print(
                f"[OK] Kaydedildi: "
                f"{output_path}"
            )

        except Exception as exc:
            print(
                f"[HATA] Görsel indirilemedi: "
                f"{exc}"
            )

        time.sleep(0.4)

    return downloaded_count


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

    mode = sys.argv[1].strip().lower()

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
    print(f"Mod: {mode}")
    print("=" * 70)

    if not COUNTRY_DIR.exists():
        raise RuntimeError(
            "'ülkeler' klasörü bulunamadı."
        )

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

    validate_unesco_data(
        records
    )

    # --------------------------------------------------------
    # CHUNK
    # --------------------------------------------------------

    selected_records = get_chunk(
        records,
        mode
    )

    # --------------------------------------------------------
    # SOURCE DATABASE
    # --------------------------------------------------------

    source_db = load_source_database()

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    print("=" * 70)
    print(
        f"{mode.upper()} GÖRSELLERİ İNDİRİLİYOR"
    )
    print("=" * 70)

    downloaded = 0

    for index, record in enumerate(
        selected_records,
        start=1
    ):
        print()
        print(
            "-" * 70
        )
        print(
            f"[{index}/{len(selected_records)}] "
            f"{record['site']}"
        )
        print(
            "-" * 70
        )

        try:
            downloaded += process_site(
                record,
                source_db
            )

        except Exception as exc:
            print(
                f"[KAYIT HATASI] "
                f"{record['site']}: {exc}"
            )

    # --------------------------------------------------------
    # SAVE SOURCES
    # --------------------------------------------------------

    save_source_database(
        source_db
    )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("İŞLEM TAMAMLANDI")
    print("=" * 70)

    print(
        f"İndirilen yeni görsel sayısı: "
        f"{downloaded}"
    )

    print(
        f"Kaynak veritabanı: "
        f"{DATA_DIR / 'image_sources.json'}"
    )

    print()
    print(
        "NOT: 'ülkeler' klasöründeki mevcut "
        "manuel bayraklar değiştirilmedi."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
