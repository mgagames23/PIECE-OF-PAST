import sys
import re
import json
import time
import unicodedata
from pathlib import Path
from io import BytesIO
import xml.etree.ElementTree as ET

import requests
from PIL import Image


# ============================================================
# PIECE OF PAST
# UNESCO WORLD HERITAGE IMAGE DOWNLOADER
# ============================================================

ROOT = Path(__file__).resolve().parent

COUNTRY_DIR = ROOT / "ülkeler"
SITE_DIR = ROOT / "unesco dünya mirasları"
DATA_DIR = ROOT / "data"

SITE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# UNESCO
# ============================================================

UNESCO_XML_URL = "https://whc.unesco.org/en/list/xml/"

# Wikimedia Commons API
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = (
    "PieceOfPast/1.0 "
    "(https://github.com/mgagames23/PIECE-OF-PAST; "
    "UNESCO World Heritage image downloader)"
)

REQUEST_TIMEOUT = 45

# Wikimedia'ya seri istek gönderiyoruz.
WIKIMEDIA_DELAY = 3.0

MAX_RETRIES = 8


# ============================================================
# 3 PARÇA
#
# Liste kaç kayıt içerirse içersin 3 parçaya bölünür.
# Böylece 1273'e sabitlenmez.
# ============================================================

PART_COUNT = 3


# ============================================================
# ÜLKE ALIASLARI
# ============================================================

COUNTRY_ALIASES = {
    "Türkiye": [
        "Türkiye",
        "Turkey",
        "Turkiye",
    ],

    "Turkey": [
        "Türkiye",
        "Turkey",
        "Turkiye",
    ],

    "Czechia": [
        "Czechia",
        "Czech Republic",
    ],

    "Czech Republic": [
        "Czechia",
        "Czech Republic",
    ],

    "Russian Federation": [
        "Russian Federation",
        "Russia",
    ],

    "Russia": [
        "Russian Federation",
        "Russia",
    ],

    "Iran (Islamic Republic of)": [
        "Iran (Islamic Republic of)",
        "Iran",
    ],

    "Iran": [
        "Iran (Islamic Republic of)",
        "Iran",
    ],

    "Syrian Arab Republic": [
        "Syrian Arab Republic",
        "Syria",
    ],

    "Syria": [
        "Syrian Arab Republic",
        "Syria",
    ],

    "Venezuela (Bolivarian Republic of)": [
        "Venezuela (Bolivarian Republic of)",
        "Venezuela",
    ],

    "Venezuela": [
        "Venezuela (Bolivarian Republic of)",
        "Venezuela",
    ],

    "Bolivia (Plurinational State of)": [
        "Bolivia (Plurinational State of)",
        "Bolivia",
    ],

    "Bolivia": [
        "Bolivia (Plurinational State of)",
        "Bolivia",
    ],

    "United Republic of Tanzania": [
        "United Republic of Tanzania",
        "Tanzania",
    ],

    "Tanzania": [
        "United Republic of Tanzania",
        "Tanzania",
    ],

    "Democratic Republic of the Congo": [
        "Democratic Republic of the Congo",
        "DR Congo",
        "Congo, Democratic Republic of the",
    ],

    "Congo, Democratic Republic of the": [
        "Democratic Republic of the Congo",
        "DR Congo",
        "Congo, Democratic Republic of the",
    ],

    "United States of America": [
        "United States of America",
        "United States",
        "USA",
    ],

    "United States": [
        "United States of America",
        "United States",
        "USA",
    ],

    "United Kingdom of Great Britain and Northern Ireland": [
        "United Kingdom of Great Britain and Northern Ireland",
        "United Kingdom",
        "UK",
    ],

    "United Kingdom": [
        "United Kingdom of Great Britain and Northern Ireland",
        "United Kingdom",
        "UK",
    ],

    "Republic of Korea": [
        "Republic of Korea",
        "South Korea",
        "Korea, Republic of",
    ],

    "South Korea": [
        "Republic of Korea",
        "South Korea",
        "Korea, Republic of",
    ],

    "Democratic People's Republic of Korea": [
        "Democratic People's Republic of Korea",
        "North Korea",
        "Korea, Democratic People's Republic of",
    ],

    "North Korea": [
        "Democratic People's Republic of Korea",
        "North Korea",
        "Korea, Democratic People's Republic of",
    ],

    "Lao People's Democratic Republic": [
        "Lao People's Democratic Republic",
        "Laos",
    ],

    "Laos": [
        "Lao People's Democratic Republic",
        "Laos",
    ],

    "United Arab Emirates": [
        "United Arab Emirates",
        "UAE",
    ],

    "Côte d'Ivoire": [
        "Côte d'Ivoire",
        "Ivory Coast",
    ],

    "Côte d’Ivoire": [
        "Côte d’Ivoire",
        "Côte d'Ivoire",
        "Ivory Coast",
    ],

    "Eswatini": [
        "Eswatini",
        "Swaziland",
    ],

    "North Macedonia": [
        "North Macedonia",
        "Macedonia",
    ],

    "Viet Nam": [
        "Viet Nam",
        "Vietnam",
    ],

    "Vietnam": [
        "Viet Nam",
        "Vietnam",
    ],
}


# ============================================================
# ISO KODLARI
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
    "Bolivia": "bo",
    "Bosnia and Herzegovina": "ba",
    "Botswana": "bw",
    "Brazil": "br",
    "Brunei Darussalam": "bn",
    "Bulgaria": "bg",
    "Burkina Faso": "bf",
    "Burundi": "bi",
    "Cabo Verde": "cv",
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
    "Croatia": "hr",
    "Cuba": "cu",
    "Cyprus": "cy",
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
    "Lao People's Democratic Republic": "la",
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
    "Republic of Korea": "kr",
    "Republic of Moldova": "md",
    "Romania": "ro",
    "Russian Federation": "ru",
    "Rwanda": "rw",
    "Saint Kitts and Nevis": "kn",
    "Saint Lucia": "lc",
    "Saint Vincent and the Grenadines": "vc",
    "Samoa": "ws",
    "San Marino": "sm",
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
    "Spain": "es",
    "Sri Lanka": "lk",
    "Sudan": "sd",
    "Suriname": "sr",
    "Sweden": "se",
    "Switzerland": "ch",
    "Syrian Arab Republic": "sy",
    "Tajikistan": "tj",
    "Thailand": "th",
    "Timor-Leste": "tl",
    "Togo": "tg",
    "Tonga": "to",
    "Trinidad and Tobago": "tt",
    "Tunisia": "tn",
    "Türkiye": "tr",
    "Turkey": "tr",
    "Turkmenistan": "tm",
    "Tuvalu": "tv",
    "Uganda": "ug",
    "Ukraine": "ua",
    "United Arab Emirates": "ae",
    "United Kingdom": "gb",
    "United Republic of Tanzania": "tz",
    "United States of America": "us",
    "Uruguay": "uy",
    "Uzbekistan": "uz",
    "Vanuatu": "vu",
    "Venezuela": "ve",
    "Viet Nam": "vn",
    "Vietnam": "vn",
    "Yemen": "ye",
    "Zambia": "zm",
    "Zimbabwe": "zw",
}


# ============================================================
# YARDIMCI
# ============================================================

def local_name(tag):
    """
    XML namespace varsa kaldırır.

    Örnek:
        {http://example.com}site
    ->  site
    """

    if not tag:
        return ""

    if "}" in tag:
        return tag.rsplit("}", 1)[-1]

    return tag


def normalize_text(text):
    text = str(text or "")

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        c
        for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower()

    text = text.replace("’", "'")
    text = text.replace("&", "and")

    text = re.sub(
        r"[^a-z0-9]+",
        "",
        text,
    )

    return text


def clean_filename(text):
    text = str(text or "").strip()

    text = re.sub(
        r'[<>:"/\\|?*]',
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def get_country_variants(country):
    variants = [
        country,
    ]

    if country in COUNTRY_ALIASES:
        variants.extend(
            COUNTRY_ALIASES[country]
        )

    for key, values in COUNTRY_ALIASES.items():

        if country == key:
            continue

        if country in values:
            variants.append(key)
            variants.extend(values)

    result = []
    seen = set()

    for value in variants:

        normalized = normalize_text(value)

        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(value)

    return result


# ============================================================
# BAYRAK BUL
#
# BAYRAKLARA DOKUNMUYORUZ.
# SADECE OKUYORUZ.
# ============================================================

def find_country_image(country):

    if not COUNTRY_DIR.exists():
        return None

    wanted_names = set()

    for variant in get_country_variants(country):
        wanted_names.add(
            normalize_text(variant)
        )

    wanted_iso = set()

    for variant in get_country_variants(country):

        if variant in ISO_CODES:
            wanted_iso.add(
                ISO_CODES[variant].lower()
            )

    for path in COUNTRY_DIR.iterdir():

        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }:
            continue

        stem = normalize_text(
            path.stem
        )

        if stem in wanted_names:
            return path

        if stem in wanted_iso:
            return path

    return None


def verify_country_flags(sites):

    countries = set()

    for site in sites:

        for country in site.get(
            "countries",
            [],
        ):

            country = country.strip()

            if country:
                countries.add(country)

    countries = sorted(
        countries,
        key=lambda x: normalize_text(x),
    )

    print()
    print("=" * 70)
    print("ÜLKE BAYRAKLARI KONTROLÜ")
    print("=" * 70)

    print(
        f"UNESCO kayıtlarında bulunan farklı ülke sayısı: "
        f"{len(countries)}"
    )

    print()

    missing = []

    for country in countries:

        image = find_country_image(
            country
        )

        if image:

            print(
                f"[OK] {country} -> {image.name}"
            )

        else:

            print(
                f"[YOK] {country}"
            )

            missing.append(country)

    print()

    if missing:

        print(
            f"Eksik bayrak: {len(missing)}"
        )

        print()

        for country in missing:
            print(
                f" - {country}"
            )

        raise RuntimeError(
            "UNESCO listesinde bulunan bazı "
            "ülkelerin bayrakları ülkeler/ klasöründe yok."
        )

    print(
        "TÜM GEREKLİ ÜLKE BAYRAKLARI BULUNDU."
    )

    print()


# ============================================================
# UNESCO XML İNDİR
# ============================================================

def download_unesco_xml():

    print(
        "UNESCO Dünya Mirası XML indiriliyor..."
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/xml,text/xml,*/*",
        "Accept-Encoding": "gzip",
    }

    response = requests.get(
        UNESCO_XML_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    print(
        f"UNESCO HTTP durumu: "
        f"{response.status_code}"
    )

    print(
        f"UNESCO XML boyutu: "
        f"{len(response.content):,} byte"
    )

    if not response.content:
        raise RuntimeError(
            "UNESCO XML boş geldi."
        )

    return response.content


# ============================================================
# XML İÇERİĞİNDEN DEĞER BULMA
# ============================================================

def element_text(element):

    if element is None:
        return ""

    text = "".join(
        element.itertext()
    ).strip()

    return re.sub(
        r"\s+",
        " ",
        text,
    )


def child_text_by_names(
    element,
    names,
):

    wanted = {
        name.lower()
        for name in names
    }

    for child in element.iter():

        tag = local_name(
            child.tag
        ).lower()

        if tag in wanted:

            text = element_text(
                child
            )

            if text:
                return text

    return ""


def extract_country_values(element):

    countries = []

    # Öncelikle country alanlarını bul.
    for child in element.iter():

        tag = local_name(
            child.tag
        ).lower()

        if tag not in {
            "country",
            "countries",
            "stateparty",
            "stateparties",
        }:
            continue

        text = element_text(
            child
        )

        if not text:
            continue

        # XML'de birden fazla ülke çeşitli
        # ayraçlarla gelebilir.
        pieces = re.split(
            r"\s*(?:,|;|\|)\s*",
            text,
        )

        for piece in pieces:

            piece = piece.strip()

            if piece and piece not in countries:
                countries.append(piece)

    return countries


# ============================================================
# UNESCO XML PARSE
# ============================================================

def parse_unesco_xml():

    xml_data = download_unesco_xml()

    try:

        root = ET.fromstring(
            xml_data
        )

    except ET.ParseError as exc:

        raise RuntimeError(
            f"UNESCO XML parse edilemedi: {exc}"
        )

    print(
        f"XML root etiketi: {root.tag}"
    )

    # --------------------------------------------------------
    # XML'deki bütün elementleri incele.
    # Önce gerçek "site" elementlerini bul.
    # --------------------------------------------------------

    site_elements = []

    for element in root.iter():

        tag = local_name(
            element.tag
        ).lower()

        if tag in {
            "site",
            "property",
            "propertyname",
        }:

            text = element_text(
                element
            )

            if text:
                site_elements.append(
                    element
                )

    # --------------------------------------------------------
    # Eğer site elementleri varsa onların parent benzeri
    # kapsayıcılarını kullanmak yerine doğrudan site'dan
    # kayıt çıkarmaya çalışıyoruz.
    # --------------------------------------------------------

    sites = []

    for site_element in site_elements:

        name = element_text(
            site_element
        )

        if not name:
            continue

        # Site elementinin kendisi dışında,
        # parent'a erişim ElementTree'de doğrudan olmadığı
        # için ülke bilgisini XML genelinden daha sonra
        # eşleştirmeye çalışacağız.
        countries = []

        sites.append({
            "name": name,
            "countries": countries,
        })

    # --------------------------------------------------------
    # Daha doğru yöntem:
    # XML'de "row" veya benzeri kayıt kapsayıcılarını bul.
    # --------------------------------------------------------

    containers = []

    container_names = {
        "row",
        "record",
        "item",
        "property",
        "site",
    }

    for element in root.iter():

        tag = local_name(
            element.tag
        ).lower()

        if tag in container_names:

            child_tags = {
                local_name(
                    child.tag
                ).lower()
                for child in element.iter()
            }

            has_name = bool(
                child_tags.intersection({
                    "site",
                    "name",
                    "property",
                    "propertyname",
                })
            )

            has_country = bool(
                child_tags.intersection({
                    "country",
                    "countries",
                    "stateparty",
                    "stateparties",
                })
            )

            if has_name and has_country:
                containers.append(
                    element
                )

    # --------------------------------------------------------
    # Öncelik: ülke bilgisi içeren container kayıtları
    # --------------------------------------------------------

    if containers:

        parsed = []

        for container in containers:

            name = child_text_by_names(
                container,
                {
                    "site",
                    "name",
                    "property",
                    "propertyname",
                },
            )

            countries = extract_country_values(
                container
            )

            if not name:
                continue

            parsed.append({
                "name": name,
                "countries": countries,
            })

        if parsed:
            sites = parsed

    # --------------------------------------------------------
    # Duplicate temizliği
    # --------------------------------------------------------

    unique = []
    seen = set()

    for site in sites:

        name = (
            site.get("name", "")
            .strip()
        )

        countries = []

        for country in site.get(
            "countries",
            [],
        ):

            country = country.strip()

            if country and country not in countries:
                countries.append(country)

        if not name:
            continue

        key = (
            normalize_text(name),
            tuple(
                normalize_text(c)
                for c in countries
            ),
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append({
            "name": name,
            "countries": countries,
        })

    sites = unique

    # --------------------------------------------------------
    # 0 kayıt ise detaylı teşhis
    # --------------------------------------------------------

    if not sites:

        print()
        print(
            "UNESCO XML geldi ancak kayıt çıkarılamadı."
        )

        print(
            "XML root:",
            root.tag,
        )

        print(
            "İlk XML etiketleri:"
        )

        count = 0

        for element in root.iter():

            print(
                " -",
                element.tag,
            )

            count += 1

            if count >= 30:
                break

        raise RuntimeError(
            "UNESCO XML içinden Dünya Mirası kayıtları "
            "çıkarılamadı."
        )

    print()
    print(
        f"UNESCO kayıt sayısı: {len(sites)}"
    )

    # UNESCO listesi binin üzerinde olmalı.
    # Sabit olarak 1273 beklemiyoruz.
    if len(sites) < 1000:

        raise RuntimeError(
            "UNESCO kayıt sayısı beklenenden düşük: "
            f"{len(sites)}"
        )

    return sites


# ============================================================
# WIKIMEDIA API
# ============================================================

def wikipedia_request(params):

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }

    wait_time = 5

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = requests.get(
                WIKIMEDIA_API,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            # 429
            if response.status_code == 429:

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                if retry_after:

                    try:
                        wait = max(
                            5,
                            int(retry_after),
                        )

                    except ValueError:
                        wait = wait_time

                else:
                    wait = wait_time

                print(
                    f"Wikimedia 429 -> "
                    f"{wait} saniye bekleniyor."
                )

                time.sleep(wait)

                wait_time = min(
                    wait_time * 2,
                    60,
                )

                continue

            # 5xx
            if response.status_code in {
                500,
                502,
                503,
                504,
            }:

                print(
                    f"Wikimedia HTTP "
                    f"{response.status_code} -> "
                    f"{wait_time} saniye bekleniyor."
                )

                time.sleep(
                    wait_time
                )

                wait_time = min(
                    wait_time * 2,
                    60,
                )

                continue

            response.raise_for_status()

            data = response.json()

            # API error
            if "error" in data:

                error = data.get(
                    "error",
                    {},
                )

                code = error.get(
                    "code",
                    "",
                )

                info = error.get(
                    "info",
                    "",
                )

                print(
                    f"Wikimedia API hatası: "
                    f"{code} - {info}"
                )

                if code in {
                    "maxlag",
                    "ratelimited",
                }:

                    time.sleep(
                        wait_time
                    )

                    wait_time = min(
                        wait_time * 2,
                        60,
                    )

                    continue

                return None

            # İstekler arasında bekleme
            time.sleep(
                WIKIMEDIA_DELAY
            )

            return data

        except (
            requests.RequestException,
            ValueError,
        ) as exc:

            print(
                f"Wikimedia istek hatası "
                f"(deneme {attempt}/{MAX_RETRIES}): "
                f"{exc}"
            )

            if attempt >= MAX_RETRIES:
                return None

            time.sleep(
                wait_time
            )

            wait_time = min(
                wait_time * 2,
                60,
            )

    return None


# ============================================================
# COMMONS ARAMA
# ============================================================

def commons_search(query):

    params = {
        "action": "query",
        "format": "json",

        "generator": "search",

        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": 8,

        "prop": "imageinfo",

        "iiprop": "url",

        "iiurlwidth": 1000,

        "maxlag": 5,
    }

    data = wikipedia_request(
        params
    )

    if not data:
        return []

    pages = (
        data.get("query", {})
        .get("pages", {})
    )

    results = []

    for page in pages.values():

        imageinfo = (
            page.get("imageinfo")
            or []
        )

        if not imageinfo:
            continue

        info = imageinfo[0]

        url = (
            info.get("thumburl")
            or info.get("url")
        )

        if not url:
            continue

        results.append({
            "title": page.get(
                "title",
                "",
            ),
            "url": url,
        })

    return results


# ============================================================
# UNESCO GÖRSELİ ARA
# ============================================================

def search_site_image(site):

    name = site.get(
        "name",
        "",
    )

    countries = site.get(
        "countries",
        [],
    )

    country = (
        countries[0]
        if countries
        else ""
    )

    queries = []

    if country:

        queries.append(
            f"{name} {country} UNESCO World Heritage"
        )

        queries.append(
            f"{name} {country} UNESCO"
        )

    queries.append(
        f"{name} UNESCO World Heritage"
    )

    queries.append(
        f"{name} UNESCO"
    )

    queries.append(
        name
    )

    seen_urls = set()

    for query in queries:

        print(
            f"  Commons araması: {query}"
        )

        results = commons_search(
            query
        )

        for result in results:

            url = result.get(
                "url",
                "",
            )

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            return result

    return None


# ============================================================
# GÖRSEL KAYDET
# ============================================================

def save_jpg(
    url,
    destination,
):

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "image/*,*/*",
    }

    wait_time = 5

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:

                retry_after = (
                    response.headers.get(
                        "Retry-After"
                    )
                )

                if retry_after:

                    try:
                        wait = max(
                            5,
                            int(retry_after),
                        )

                    except ValueError:
                        wait = wait_time

                else:
                    wait = wait_time

                print(
                    f"  Görsel 429 -> "
                    f"{wait} saniye bekleniyor."
                )

                time.sleep(wait)

                wait_time = min(
                    wait_time * 2,
                    60,
                )

                continue

            if response.status_code in {
                500,
                502,
                503,
                504,
            }:

                print(
                    f"  Görsel HTTP "
                    f"{response.status_code} -> "
                    f"{wait_time} saniye bekleniyor."
                )

                time.sleep(
                    wait_time
                )

                wait_time = min(
                    wait_time * 2,
                    60,
                )

                continue

            response.raise_for_status()

            image = Image.open(
                BytesIO(
                    response.content
                )
            )

            if (
                image.width < 200
                or image.height < 200
            ):

                print(
                    "  Görsel çok küçük:"
                    f" {image.width}x{image.height}"
                )

                return False

            image = image.convert(
                "RGB"
            )

            image.save(
                destination,
                "JPEG",
                quality=88,
                optimize=True,
            )

            return True

        except Exception as exc:

            print(
                f"  Görsel kaydetme hatası "
                f"(deneme {attempt}/{MAX_RETRIES}): "
                f"{exc}"
            )

            if attempt >= MAX_RETRIES:
                return False

            time.sleep(
                wait_time
            )

            wait_time = min(
                wait_time * 2,
                60,
            )

    return False


# ============================================================
# DOSYA ADI
# ============================================================

def build_site_filename(site):

    name = clean_filename(
        site.get(
            "name",
            "Unknown Site",
        )
    )

    countries = site.get(
        "countries",
        [],
    )

    country = (
        countries[0]
        if countries
        else "Unknown"
    )

    country = clean_filename(
        country
    )

    return (
        f"{name} - {country}.jpg"
    )


# ============================================================
# PARÇA ARALIĞI
# ============================================================

def get_part_range(
    mode,
    total,
):

    if total <= 0:
        return 0, 0

    part_size = (
        total + PART_COUNT - 1
    ) // PART_COUNT

    if mode == "unesco-1":

        start = 0
        end = min(
            part_size,
            total,
        )

    elif mode == "unesco-2":

        start = part_size
        end = min(
            part_size * 2,
            total,
        )

    elif mode == "unesco-3":

        start = part_size * 2
        end = total

    else:

        raise RuntimeError(
            f"Geçersiz mod: {mode}"
        )

    return start, end


# ============================================================
# UNESCO GÖRSELLERİNİ İNDİR
# ============================================================

def download_site_images(
    sites,
    start,
    end,
    mode,
):

    selected = sites[
        start:end
    ]

    print()
    print("=" * 70)

    print(
        f"{mode} BAŞLIYOR"
    )

    print(
        f"Aralık: "
        f"{start + 1}-{end} / {len(sites)}"
    )

    print(
        f"Bu parçada: "
        f"{len(selected)} kayıt"
    )

    print("=" * 70)
    print()

    downloaded = 0
    skipped = 0
    failed = 0

    for absolute_index, site in enumerate(
        selected,
        start=start + 1,
    ):

        filename = build_site_filename(
            site
        )

        destination = (
            SITE_DIR / filename
        )

        print(
            f"[{absolute_index}/{len(sites)}] "
            f"{site.get('name', '')}"
        )

        # ----------------------------------------------------
        # Zaten varsa indirme.
        # ----------------------------------------------------

        if (
            destination.exists()
            and destination.stat().st_size > 0
        ):

            print(
                "  [SKIP] Görsel zaten mevcut."
            )

            skipped += 1

            continue

        # ----------------------------------------------------
        # Commons ara
        # ----------------------------------------------------

        result = search_site_image(
            site
        )

        if not result:

            print(
                "  [HATA] Uygun Commons görseli bulunamadı."
            )

            failed += 1

            continue

        print(
            f"  Bulunan görsel: "
            f"{result.get('title', '')}"
        )

        # ----------------------------------------------------
        # İndir
        # ----------------------------------------------------

        success = save_jpg(
            result["url"],
            destination,
        )

        if success:

            print(
                f"  [OK] {destination.name}"
            )

            downloaded += 1

        else:

            print(
                "  [HATA] Görsel indirilemedi."
            )

            failed += 1

    print()
    print("=" * 70)

    print(
        f"{mode} TAMAMLANDI"
    )

    print(
        f"Yeni indirilen : {downloaded}"
    )

    print(
        f"Zaten mevcut   : {skipped}"
    )

    print(
        f"Başarısız       : {failed}"
    )

    print("=" * 70)
    print()


# ============================================================
# JSON OLUŞTUR
# ============================================================

def create_json(sites):

    site_files = {}

    if SITE_DIR.exists():

        for path in SITE_DIR.iterdir():

            if not path.is_file():
                continue

            if path.suffix.lower() != ".jpg":
                continue

            relative = str(
                path.relative_to(ROOT)
            ).replace(
                "\\",
                "/",
            )

            site_files[
                path.name
            ] = relative

    unesco_data = []

    for site in sites:

        filename = build_site_filename(
            site
        )

        unesco_data.append({
            "name": site.get(
                "name",
                "",
            ),

            "countries": site.get(
                "countries",
                [],
            ),

            "image": site_files.get(
                filename
            ),
        })

    with open(
        DATA_DIR / "unesco.json",
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

    for filename in site_files:

        image_sources[
            filename
        ] = {
            "source": "Wikimedia Commons"
        }

    with open(
        DATA_DIR / "image_sources.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            image_sources,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        "data/unesco.json oluşturuldu."
    )

    print(
        "data/image_sources.json oluşturuldu."
    )


# ============================================================
# MOD
# ============================================================

def get_mode():

    if len(sys.argv) < 2:

        raise RuntimeError(
            "Mod belirtilmedi."
        )

    mode = (
        sys.argv[1]
        .strip()
        .lower()
    )

    if mode not in {
        "unesco-1",
        "unesco-2",
        "unesco-3",
    }:

        raise RuntimeError(
            "Geçersiz mod: "
            f"{mode}"
        )

    return mode


# ============================================================
# MAIN
# ============================================================

def main():

    mode = get_mode()

    print()
    print("=" * 70)
    print(
        "PIECE OF PAST"
    )
    print(
        "UNESCO WORLD HERITAGE ASSET DOWNLOADER"
    )
    print("=" * 70)

    print(
        f"Mod: {mode}"
    )

    print()

    # --------------------------------------------------------
    # 1. UNESCO listesini al
    # --------------------------------------------------------

    sites = parse_unesco_xml()

    # --------------------------------------------------------
    # 2. GitHub'a senin yüklediğin bayrakları kontrol et.
    #
    # BURADA HİÇBİR DOSYA DEĞİŞTİRİLMEZ.
    # --------------------------------------------------------

    verify_country_flags(
        sites
    )

    # --------------------------------------------------------
    # 3. Bu parçanın aralığını hesapla
    # --------------------------------------------------------

    start, end = get_part_range(
        mode,
        len(sites),
    )

    # --------------------------------------------------------
    # 4. UNESCO görsellerini indir
    # --------------------------------------------------------

    download_site_images(
        sites,
        start,
        end,
        mode,
    )

    # --------------------------------------------------------
    # 5. JSON
    # --------------------------------------------------------

    create_json(
        sites
    )

    print()
    print("=" * 70)
    print(
        f"{mode} BAŞARIYLA TAMAMLANDI"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
