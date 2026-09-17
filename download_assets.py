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
# KLASORLER
# ============================================================

ROOT = Path(__file__).resolve().parent

COUNTRY_DIR = ROOT / "ülkeler"
SITE_DIR = ROOT / "unesco dünya mirasları"
DATA_DIR = ROOT / "data"

COUNTRY_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# KAYNAKLAR
# ============================================================

UNESCO_XML = "https://whc.unesco.org/en/list/xml/"

# Standart ülke bayrakları
COUNTRY_FLAGS_BASE = (
    "https://raw.githubusercontent.com/oppops/Country-Flags/master/png250px"
)

# Wikimedia sadece UNESCO alan görselleri için kullanılacak.
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


# ============================================================
# AYARLAR
# ============================================================

USER_AGENT = (
    "PieceOfPast/1.0 "
    "(https://github.com/mgagames23/PIECE-OF-PAST; "
    "UNESCO asset downloader)"
)

REQUEST_TIMEOUT = 40

# Wikimedia istekleri arasında bekleme
WIKIMEDIA_DELAY = 1.5

MAX_RETRIES = 6

# UNESCO parçaları
PART_RANGES = {
    "unesco-1": (0, 424),    # 1-424
    "unesco-2": (424, 848),  # 425-848
    "unesco-3": (848, 1273), # 849-1273
}


# ============================================================
# SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    }
)


# ============================================================
# ÜLKE İSİM ALIASLARI
# ============================================================

COUNTRY_ALIASES = {
    "Türkiye": "Turkey",
    "Turkey": "Turkey",

    "Czechia": "Czech Republic",
    "Czech Republic": "Czech Republic",

    "Viet Nam": "Vietnam",
    "Vietnam": "Vietnam",

    "Republic of Korea": "South Korea",
    "South Korea": "South Korea",

    "Democratic People's Republic of Korea": "North Korea",
    "DPRK": "North Korea",
    "North Korea": "North Korea",

    "Russian Federation": "Russia",
    "Russia": "Russia",

    "United States of America": "United States",
    "United States": "United States",
    "USA": "United States",

    "United Republic of Tanzania": "Tanzania",
    "Tanzania": "Tanzania",

    "Bolivia (Plurinational State of)": "Bolivia",
    "Bolivia": "Bolivia",

    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Venezuela": "Venezuela",

    "Iran (Islamic Republic of)": "Iran",
    "Iran": "Iran",

    "Lao People's Democratic Republic": "Laos",
    "Laos": "Laos",

    "Republic of Moldova": "Moldova",
    "Moldova": "Moldova",

    "Syrian Arab Republic": "Syria",
    "Syria": "Syria",

    "United Kingdom of Great Britain and Northern Ireland":
        "United Kingdom",

    "United Kingdom": "United Kingdom",

    "Brunei Darussalam": "Brunei",
    "Brunei": "Brunei",

    "Côte d'Ivoire": "Cote d'Ivoire",
    "Cote d'Ivoire": "Cote d'Ivoire",

    "Cabo Verde": "Cape Verde",
    "Cape Verde": "Cape Verde",

    "Eswatini": "Eswatini",

    "North Macedonia": "North Macedonia",

    "Türkiye": "Turkey",
}


# ============================================================
# ISO ÜLKE KODLARI
#
# UNESCO'dan gelen ülke isimlerini standart ISO kodlarına
# dönüştürüyoruz.
# ============================================================

ISO_CODES = {
    "Afghanistan": "af",
    "Albania": "al",
    "Algeria": "dz",
    "Andorra": "ad",
    "Angola": "ao",
    "Antigua and Barbuda": "ag",
    "Argentina": "ar",
    "Armenia": "am",
    "Australia": "au",
    "Austria": "at",
    "Azerbaijan": "az",
    "Bahamas": "bs",
    "Bahrain": "bh",
    "Bangladesh": "bd",
    "Barbados": "bb",
    "Belarus": "by",
    "Belgium": "be",
    "Belize": "bz",
    "Benin": "bj",
    "Bhutan": "bt",
    "Bolivia": "bo",
    "Bosnia and Herzegovina": "ba",
    "Botswana": "bw",
    "Brazil": "br",
    "Brunei": "bn",
    "Bulgaria": "bg",
    "Burkina Faso": "bf",
    "Burundi": "bi",
    "Cabo Verde": "cv",
    "Cape Verde": "cv",
    "Cambodia": "kh",
    "Cameroon": "cm",
    "Canada": "ca",
    "Central African Republic": "cf",
    "Chad": "td",
    "Chile": "cl",
    "China": "cn",
    "Colombia": "co",
    "Comoros": "km",
    "Congo": "cg",
    "Costa Rica": "cr",
    "Côte d'Ivoire": "ci",
    "Cote d'Ivoire": "ci",
    "Croatia": "hr",
    "Cuba": "cu",
    "Cyprus": "cy",
    "Czech Republic": "cz",
    "Czechia": "cz",
    "Democratic Republic of the Congo": "cd",
    "Denmark": "dk",
    "Djibouti": "dj",
    "Dominica": "dm",
    "Dominican Republic": "do",
    "Ecuador": "ec",
    "Egypt": "eg",
    "El Salvador": "sv",
    "Equatorial Guinea": "gq",
    "Eritrea": "er",
    "Estonia": "ee",
    "Eswatini": "sz",
    "Ethiopia": "et",
    "Fiji": "fj",
    "Finland": "fi",
    "France": "fr",
    "Gabon": "ga",
    "Gambia": "gm",
    "Georgia": "ge",
    "Germany": "de",
    "Ghana": "gh",
    "Greece": "gr",
    "Grenada": "gd",
    "Guatemala": "gt",
    "Guinea": "gn",
    "Guinea-Bissau": "gw",
    "Guyana": "gy",
    "Haiti": "ht",
    "Honduras": "hn",
    "Hungary": "hu",
    "Iceland": "is",
    "India": "in",
    "Indonesia": "id",
    "Iran": "ir",
    "Iraq": "iq",
    "Ireland": "ie",
    "Israel": "il",
    "Italy": "it",
    "Jamaica": "jm",
    "Japan": "jp",
    "Jordan": "jo",
    "Kazakhstan": "kz",
    "Kenya": "ke",
    "Kiribati": "ki",
    "Kuwait": "kw",
    "Kyrgyzstan": "kg",
    "Laos": "la",
    "Latvia": "lv",
    "Lebanon": "lb",
    "Lesotho": "ls",
    "Liberia": "lr",
    "Libya": "ly",
    "Liechtenstein": "li",
    "Lithuania": "lt",
    "Luxembourg": "lu",
    "Madagascar": "mg",
    "Malawi": "mw",
    "Malaysia": "my",
    "Maldives": "mv",
    "Mali": "ml",
    "Malta": "mt",
    "Marshall Islands": "mh",
    "Mauritania": "mr",
    "Mauritius": "mu",
    "Mexico": "mx",
    "Micronesia": "fm",
    "Moldova": "md",
    "Monaco": "mc",
    "Mongolia": "mn",
    "Montenegro": "me",
    "Morocco": "ma",
    "Mozambique": "mz",
    "Myanmar": "mm",
    "Namibia": "na",
    "Nauru": "nr",
    "Nepal": "np",
    "Netherlands": "nl",
    "New Zealand": "nz",
    "Nicaragua": "ni",
    "Niger": "ne",
    "Nigeria": "ng",
    "North Korea": "kp",
    "North Macedonia": "mk",
    "Norway": "no",
    "Oman": "om",
    "Pakistan": "pk",
    "Palau": "pw",
    "Panama": "pa",
    "Papua New Guinea": "pg",
    "Paraguay": "py",
    "Peru": "pe",
    "Philippines": "ph",
    "Poland": "pl",
    "Portugal": "pt",
    "Qatar": "qa",
    "Romania": "ro",
    "Russia": "ru",
    "Rwanda": "rw",
    "Saint Kitts and Nevis": "kn",
    "Saint Lucia": "lc",
    "Saint Vincent and the Grenadines": "vc",
    "Samoa": "ws",
    "San Marino": "sm",
    "Sao Tome and Principe": "st",
    "Saudi Arabia": "sa",
    "Senegal": "sn",
    "Serbia": "rs",
    "Seychelles": "sc",
    "Sierra Leone": "sl",
    "Singapore": "sg",
    "Slovakia": "sk",
    "Slovenia": "si",
    "Solomon Islands": "sb",
    "Somalia": "so",
    "South Africa": "za",
    "South Korea": "kr",
    "South Sudan": "ss",
    "Spain": "es",
    "Sri Lanka": "lk",
    "Sudan": "sd",
    "Suriname": "sr",
    "Sweden": "se",
    "Switzerland": "ch",
    "Syria": "sy",
    "Tajikistan": "tj",
    "Tanzania": "tz",
    "Thailand": "th",
    "Timor-Leste": "tl",
    "Togo": "tg",
    "Tonga": "to",
    "Trinidad and Tobago": "tt",
    "Tunisia": "tn",
    "Turkey": "tr",
    "Turkmenistan": "tm",
    "Tuvalu": "tv",
    "Uganda": "ug",
    "Ukraine": "ua",
    "United Arab Emirates": "ae",
    "United Kingdom": "gb",
    "United States": "us",
    "Uruguay": "uy",
    "Uzbekistan": "uz",
    "Vanuatu": "vu",
    "Vatican City": "va",
    "Venezuela": "ve",
    "Vietnam": "vn",
    "Yemen": "ye",
    "Zambia": "zm",
    "Zimbabwe": "zw",
}


# ============================================================
# GENEL YARDIMCILAR
# ============================================================

def clean_filename(name):
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def local_name(tag):
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def text_of(element):
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def find_first_text(element, names):
    names = set(names)

    for child in element.iter():
        if local_name(child.tag) in names:
            value = text_of(child)
            if value:
                return value

    return ""


# ============================================================
# UNESCO XML
# ============================================================

def find_site_name(site):
    value = find_first_text(
        site,
        [
            "site",
            "name",
            "site_name",
            "short_description",
        ],
    )

    if value:
        return value

    for attr in ["name", "site", "title"]:
        if attr in site.attrib and site.attrib[attr]:
            return site.attrib[attr].strip()

    return ""


def find_site_id(site):
    for key in ["id", "siteid", "whc_id", "idno"]:
        if key in site.attrib:
            return site.attrib[key].strip()

    value = find_first_text(
        site,
        ["id", "siteid", "whc_id", "idno"],
    )

    return value


def find_year(site):
    value = find_first_text(
        site,
        [
            "date_inscribed",
            "date",
            "year",
        ],
    )

    match = re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", value)

    if match:
        return int(match.group(1))

    return None


def find_category(site):
    value = find_first_text(
        site,
        [
            "category",
            "category_id",
            "type",
        ],
    )

    return value


def find_region(site):
    value = find_first_text(
        site,
        [
            "region",
            "region_name",
        ],
    )

    return value


def find_countries(site):
    countries = []

    for child in site.iter():
        tag = local_name(child.tag)

        if tag in {
            "country",
            "countries",
            "states",
            "state",
        }:
            value = text_of(child)

            if value:
                parts = re.split(r"[,;/|]", value)

                for part in parts:
                    part = part.strip()

                    if part and part not in countries:
                        countries.append(part)

    return countries


def parse_unesco_xml(xml_text):
    root = ET.fromstring(xml_text)

    sites = []

    for element in root.iter():
        tag = local_name(element.tag)

        if tag.lower() not in {
            "site",
            "property",
            "item",
        }:
            continue

        name = find_site_name(element)

        if not name:
            continue

        site_id = find_site_id(element)

        countries = find_countries(element)

        sites.append(
            {
                "id": site_id,
                "name": name,
                "countries": countries,
                "year": find_year(element),
                "category": find_category(element),
                "region": find_region(element),
            }
        )

    # Aynı kayıtların tekrarını önle
    unique = {}

    for site in sites:
        key = (
            site.get("id")
            or f"{site.get('name')}|{','.join(site.get('countries', []))}"
        )

        unique[key] = site

    return list(unique.values())


def download_unesco():
    print("UNESCO XML indiriliyor...")

    response = SESSION.get(
        UNESCO_XML,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    sites = parse_unesco_xml(response.text)

    print(f"UNESCO alanlari: {len(sites)}")

    if not sites:
        raise RuntimeError(
            "UNESCO XML okundu fakat hic alan bulunamadi."
        )

    return sites


# ============================================================
# ÜLKE İSMİ
# ============================================================

def normalize_country_name(name):
    name = (name or "").strip()

    if name in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[name]

    return name


def country_code(name):
    normalized = normalize_country_name(name)

    return ISO_CODES.get(normalized)


# ============================================================
# ÜLKE BAYRAĞI
# ============================================================

def country_flag_url(code):
    return f"{COUNTRY_FLAGS_BASE}/{code}.png"


def save_country_flag(url, destination):
    """
    Standart Country-Flags PNG'sini alır.
    Sonucu JPEG olarak kaydeder.
    """

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = SESSION.get(
                url,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                wait = min(30, attempt * 5)

                print(
                    f"  Bayrak 429. "
                    f"{wait} saniye bekleniyor..."
                )

                time.sleep(wait)
                continue

            if response.status_code >= 500:
                wait = min(30, attempt * 3)

                print(
                    f"  Bayrak sunucu hatasi "
                    f"{response.status_code}. "
                    f"{wait} saniye bekleniyor..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            image = Image.open(
                io.BytesIO(response.content)
            )

            image = ImageOps.exif_transpose(image)

            # Şeffaflığı beyaz zemine çevir
            if image.mode in ("RGBA", "LA"):
                background = Image.new(
                    "RGB",
                    image.size,
                    "white",
                )

                alpha = image.getchannel("A")

                background.paste(
                    image.convert("RGB"),
                    mask=alpha,
                )

                image = background
            else:
                image = image.convert("RGB")

            # Bayraklar standart oranlarını korusun.
            # 250 px kaynak olduğu için gereksiz büyütme yok.
            image.thumbnail(
                (1000, 1000),
                Image.Resampling.LANCZOS,
            )

            image.save(
                destination,
                "JPEG",
                quality=92,
                optimize=True,
                progressive=True,
            )

            return True

        except Exception as exc:

            print(
                f"  Bayrak indirme hatasi "
                f"(deneme {attempt}/{MAX_RETRIES}): {exc}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(
                    min(30, attempt * 3)
                )

    return False


def get_unesco_countries(sites):
    countries = set()

    for site in sites:

        for country in site.get("countries", []):

            country = normalize_country_name(country)

            if country:
                countries.add(country)

    return sorted(countries)


def download_country_images(sites):
    """
    UNESCO verisinde geçen bütün ülkelerin standart bayraklarını indirir.
    """

    countries = get_unesco_countries(sites)

    print()
    print("=" * 60)
    print("ULKE BAYRAKLARI")
    print("=" * 60)
    print(f"Toplam ulke: {len(countries)}")
    print()

    country_images = {}

    success = 0
    skipped = 0
    failed = 0

    for index, country in enumerate(countries, 1):

        code = country_code(country)

        filename = clean_filename(country) + ".jpg"

        destination = COUNTRY_DIR / filename

        print(
            f"[{index}/{len(countries)}] "
            f"{country}"
        )

        if destination.exists() and destination.stat().st_size > 1000:

            print("  Zaten var -> atlandi")

            country_images[country] = (
                f"ülkeler/{filename}"
            )

            skipped += 1
            continue

        if not code:

            print(
                f"  ISO kodu bulunamadi: {country}"
            )

            failed += 1
            continue

        url = country_flag_url(code)

        print(
            f"  ISO: {code.upper()}"
        )

        print(
            f"  Kaynak: Country-Flags"
        )

        if save_country_flag(
            url,
            destination,
        ):

            print("  OK")

            country_images[country] = (
                f"ülkeler/{filename}"
            )

            success += 1

        else:

            print("  BASARISIZ")

            failed += 1

        # Kaynağı gereksiz yere zorlamamak için
        time.sleep(0.25)

    print()
    print("=" * 60)
    print("ULKE BAYRAKLARI SONUCU")
    print("=" * 60)

    print(f"Toplam : {len(countries)}")
    print(f"Yeni   : {success}")
    print(f"Mevcut : {skipped}")
    print(f"Hata   : {failed}")
    print()

    # Ülkelerin tamamı yoksa UNESCO'ya geçme.
    if len(country_images) != len(countries):

        missing = [
            country
            for country in countries
            if country not in country_images
        ]

        print("Eksik ulkeler:")

        for country in missing:
            print(f"  - {country}")

        raise RuntimeError(
            "Tum ulke bayraklari indirilemedi. "
            "UNESCO asamasina gecilmeyecek."
        )

    return country_images


# ============================================================
# WIKIMEDIA
# ============================================================

_last_wikimedia_request = 0.0


def wait_before_wikimedia_request():
    global _last_wikimedia_request

    now = time.monotonic()

    elapsed = now - _last_wikimedia_request

    if elapsed < WIKIMEDIA_DELAY:
        time.sleep(
            WIKIMEDIA_DELAY - elapsed
        )

    _last_wikimedia_request = time.monotonic()


def commons_request(params):

    params = dict(params)

    params["format"] = "json"
    params["maxlag"] = "5"

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            wait_before_wikimedia_request()

            response = SESSION.get(
                COMMONS_API,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code in (429, 503):

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = 10
                else:
                    wait = min(
                        60,
                        5 * (2 ** (attempt - 1)),
                    )

                print(
                    f"  Wikimedia {response.status_code}. "
                    f"{wait:.0f} saniye bekleniyor..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            error = data.get("error")

            if error:

                code = error.get("code", "")

                if code in {
                    "maxlag",
                    "ratelimited",
                }:

                    wait = min(
                        60,
                        5 * (2 ** (attempt - 1)),
                    )

                    print(
                        f"  Wikimedia {code}. "
                        f"{wait} saniye bekleniyor..."
                    )

                    time.sleep(wait)
                    continue

                print(
                    f"  Commons API hata: "
                    f"{error}"
                )

                return None

            return data

        except Exception as exc:

            print(
                f"  Commons istek hatasi "
                f"(deneme {attempt}/{MAX_RETRIES}): "
                f"{exc}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(
                    min(
                        60,
                        5 * (2 ** (attempt - 1)),
                    )
                )

    return None


def commons_search(query):

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "5",
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": "800",
    }

    data = commons_request(params)

    if not data:
        return None

    pages = (
        data
        .get("query", {})
        .get("pages", {})
    )

    candidates = []

    for page in pages.values():

        imageinfo = page.get(
            "imageinfo",
            [],
        )

        if not imageinfo:
            continue

        info = imageinfo[0]

        url = (
            info.get("thumburl")
            or info.get("url")
        )

        mime = (
            info.get("mime")
            or ""
        ).lower()

        if not url:
            continue

        if not mime.startswith("image/"):
            continue

        candidates.append(
            {
                "url": url,
                "title": page.get(
                    "title",
                    "",
                ),
            }
        )

    if not candidates:
        return None

    return candidates[0]


def save_jpg(
    url,
    destination,
):

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            wait_before_wikimedia_request()

            response = SESSION.get(
                url,
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
                        wait = float(retry_after)
                    except ValueError:
                        wait = 10

                else:

                    wait = min(
                        60,
                        5 * (2 ** (attempt - 1)),
                    )

                print(
                    f"  Gorsel {response.status_code}. "
                    f"{wait:.0f} saniye bekleniyor..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            image = Image.open(
                io.BytesIO(response.content)
            )

            image = ImageOps.exif_transpose(
                image
            )

            image = image.convert("RGB")

            image.thumbnail(
                (800, 800),
                Image.Resampling.LANCZOS,
            )

            image.save(
                destination,
                "JPEG",
                quality=82,
                optimize=True,
                progressive=True,
            )

            return True

        except Exception as exc:

            print(
                f"  Gorsel kaydetme hatasi "
                f"(deneme {attempt}/{MAX_RETRIES}): "
                f"{exc}"
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    min(
                        60,
                        5 * (2 ** (attempt - 1)),
                    )
                )

    return False


# ============================================================
# UNESCO GÖRSELLERİ
# ============================================================

def site_filename(site):

    name = clean_filename(
        site["name"]
    )

    countries = site.get(
        "countries",
        [],
    )

    country = (
        normalize_country_name(
            countries[0]
        )
        if countries
        else ""
    )

    if country:
        return (
            f"{name} - {country}.jpg"
        )

    return f"{name}.jpg"


def download_site_images(
    sites,
    part_name,
):

    if part_name not in PART_RANGES:
        raise ValueError(
            f"Gecersiz UNESCO parcasi: "
            f"{part_name}"
        )

    start, end = PART_RANGES[
        part_name
    ]

    selected = sites[start:end]

    print()
    print("=" * 60)
    print(
        f"UNESCO GORSELLERI - {part_name}"
    )
    print("=" * 60)

    print(
        f"Aralik: {start + 1}-{end}"
    )

    print(
        f"Bu parca: {len(selected)} alan"
    )

    print()

    downloaded = 0
    skipped = 0
    failed = 0

    for local_index, site in enumerate(
        selected,
        1,
    ):

        global_index = start + local_index

        filename = site_filename(site)

        destination = (
            SITE_DIR / filename
        )

        print(
            f"[{global_index}/{len(sites)}] "
            f"{site['name']}"
        )

        if (
            destination.exists()
            and destination.stat().st_size > 1000
        ):

            print("  Zaten var -> atlandi")

            skipped += 1
            continue

        countries = site.get(
            "countries",
            [],
        )

        search_country = ""

        if countries:
            search_country = (
                normalize_country_name(
                    countries[0]
                )
            )

        queries = []

        if search_country:

            queries.append(
                f"{site['name']} "
                f"{search_country} "
                f"UNESCO"
            )

            queries.append(
                f"{site['name']} "
                f"{search_country}"
            )

        queries.append(
            site["name"]
        )

        found = None

        for query in queries:

            print(
                f"  Commons arama: {query}"
            )

            found = commons_search(
                query
            )

            if found:
                break

        if not found:

            print(
                "  Gorsel bulunamadi."
            )

            failed += 1
            continue

        print(
            f"  Bulundu: "
            f"{found['title']}"
        )

        if save_jpg(
            found["url"],
            destination,
        ):

            print("  OK")

            downloaded += 1

        else:

            print("  BASARISIZ")

            failed += 1

    print()
    print("=" * 60)
    print(
        f"{part_name} TAMAMLANDI"
    )
    print("=" * 60)

    print(
        f"Yeni   : {downloaded}"
    )

    print(
        f"Mevcut : {skipped}"
    )

    print(
        f"Hata   : {failed}"
    )

    print()


# ============================================================
# JSON
# ============================================================

def build_existing_site_images(sites):

    site_images = {}

    for site in sites:

        filename = site_filename(site)

        path = SITE_DIR / filename

        if (
            path.exists()
            and path.stat().st_size > 1000
        ):

            site_images[
                str(
                    site.get("id")
                    or site.get("name")
                )
            ] = (
                f"unesco dünya mirasları/"
                f"{filename}"
            )

    return site_images


def load_existing_sources():

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
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        return data if isinstance(
            data,
            dict,
        ) else {}

    except Exception:

        return {}


def create_json(
    sites,
    country_images,
):

    existing_sources = (
        load_existing_sources()
    )

    site_images = (
        build_existing_site_images(
            sites
        )
    )

    output_sites = []

    for site in sites:

        site_key = str(
            site.get("id")
            or site.get("name")
        )

        item = dict(site)

        if site_key in site_images:

            item["image"] = (
                site_images[
                    site_key
                ]
            )

        output_sites.append(item)

    unesco_data = {
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "sites": output_sites,
    }

    unesco_json = (
        DATA_DIR
        / "unesco.json"
    )

    with open(
        unesco_json,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            unesco_data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    image_sources = {}

    for country, path in country_images.items():

        image_sources[
            f"country:{country}"
        ] = {
            "type": "country_flag",
            "source": "Country-Flags",
            "path": path,
        }

    # Önceki UNESCO kaynaklarını koru
    for key, value in existing_sources.items():

        if not key.startswith(
            "country:"
        ):

            image_sources[
                key
            ] = value

    image_sources_json = (
        DATA_DIR
        / "image_sources.json"
    )

    with open(
        image_sources_json,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            image_sources,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        f"JSON olusturuldu: "
        f"{unesco_json}"
    )

    print(
        f"Kaynak JSON olusturuldu: "
        f"{image_sources_json}"
    )


# ============================================================
# MOD
# ============================================================

def get_mode():

    if len(sys.argv) < 2:
        return "countries"

    mode = sys.argv[1].strip().lower()

    allowed = {
        "countries",
        "unesco-1",
        "unesco-2",
        "unesco-3",
    }

    if mode not in allowed:

        raise SystemExit(
            "Gecersiz mod. "
            "Kullanim: "
            "countries | unesco-1 | "
            "unesco-2 | unesco-3"
        )

    return mode


# ============================================================
# MAIN
# ============================================================

def main():

    mode = get_mode()

    print()
    print("=" * 60)
    print("PIECE OF PAST - UNESCO ASSET DOWNLOADER")
    print("=" * 60)

    print(
        f"Mod: {mode}"
    )

    print()

    # Her aşamada güncel UNESCO verisini al.
    sites = download_unesco()

    country_images = {}

    # --------------------------------------------------------
    # ÜLKELER
    # --------------------------------------------------------

    if mode == "countries":

        country_images = (
            download_country_images(
                sites
            )
        )

        create_json(
            sites,
            country_images,
        )

        print()
        print(
            "ULKE ASAMASI BASARIYLA TAMAMLANDI."
        )

        print(
            "UNESCO asamasina gecilebilir."
        )

        return

    # --------------------------------------------------------
    # UNESCO
    # --------------------------------------------------------

    # UNESCO aşamasına gelindiğinde ülke klasörünü oku.
    countries = get_unesco_countries(
        sites
    )

    for country in countries:

        filename = (
            clean_filename(country)
            + ".jpg"
        )

        path = COUNTRY_DIR / filename

        if (
            path.exists()
            and path.stat().st_size > 1000
        ):

            country_images[
                country
            ] = (
                f"ülkeler/{filename}"
            )

    # Güvenlik kontrolü
    if len(country_images) != len(countries):

        missing = [
            country
            for country in countries
            if country not in country_images
        ]

        print(
            "UNESCO'ya gecmeden once "
            "eksik ulke bayraklari bulundu:"
        )

        for country in missing:
            print(
                f"  - {country}"
            )

        raise RuntimeError(
            "Tum ulke bayraklari mevcut "
            "olmadan UNESCO indirmesi baslatilamaz."
        )

    download_site_images(
        sites,
        mode,
    )

    create_json(
        sites,
        country_images,
    )

    print()
    print(
        f"{mode} BASARIYLA TAMAMLANDI."
    )


# ============================================================
# ÇALIŞTIR
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()
        print(
            "Islem kullanici tarafindan durduruldu."
        )

        sys.exit(130)

    except Exception as exc:

        print()
        print("=" * 60)
        print("HATA")
        print("=" * 60)
        print(exc)

        sys.exit(1)
