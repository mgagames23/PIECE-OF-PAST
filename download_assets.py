#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import io
import json
import time
import html
import unicodedata
import xml.etree.ElementTree as ET

import requests
from PIL import Image


# ==========================================================
# AYARLAR
# ==========================================================

UNESCO_XML_URL = (
    "https://whc.unesco.org/en/list/xml/"
)

COMMONS_API = (
    "https://commons.wikimedia.org/w/api.php"
)

UNESCO_DIR = "unesco dünya mirasları"
FLAGS_DIR = "ülkeler"
DATA_DIR = "data"

SOURCES_FILE = os.path.join(
    DATA_DIR,
    "image_sources.json"
)

REQUEST_TIMEOUT = 40

# Wikimedia API'yi aşırı hızlı sorgulamamak için
REQUEST_DELAY = 1.2

# Bir site için ilk aramada yeterli sonuç yoksa
# ikinci arama yapılabilir.
MAX_SEARCH_RESULTS = 20

# Kabul edilen görüntü MIME tipleri
ALLOWED_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

# Kabul edilen dosya uzantıları
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

# Açıkça istemediğimiz dosya uzantıları
BAD_EXTENSIONS = {
    ".pdf",
    ".djvu",
    ".djv",
    ".svg",
    ".svgz",
    ".tif",
    ".tiff",
    ".psd",
    ".eps",
    ".ai",
    ".xcf",
    ".webm",
    ".ogv",
    ".ogg",
    ".mp4",
    ".avi",
    ".mov",
    ".gif",
}


# ==========================================================
# ÜLKE ISO KODLARI
# ==========================================================

ISO_CODES = {
    "afghanistan": "af",
    "albania": "al",
    "algeria": "dz",
    "andorra": "ad",
    "angola": "ao",
    "antigua and barbuda": "ag",
    "argentina": "ar",
    "armenia": "am",
    "australia": "au",
    "austria": "at",
    "azerbaijan": "az",
    "bahamas": "bs",
    "bahrain": "bh",
    "bangladesh": "bd",
    "barbados": "bb",
    "belarus": "by",
    "belgium": "be",
    "belize": "bz",
    "benin": "bj",
    "bhutan": "bt",
    "bolivia": "bo",
    "bosnia and herzegovina": "ba",
    "botswana": "bw",
    "brazil": "br",
    "brunei": "bn",
    "bulgaria": "bg",
    "burkina faso": "bf",
    "burundi": "bi",
    "cabo verde": "cv",
    "cape verde": "cv",
    "cambodia": "kh",
    "cameroon": "cm",
    "canada": "ca",
    "central african republic": "cf",
    "chad": "td",
    "chile": "cl",
    "china": "cn",
    "colombia": "co",
    "comoros": "km",
    "congo": "cg",
    "democratic republic of the congo": "cd",
    "republic of the congo": "cg",
    "costa rica": "cr",
    "cote d'ivoire": "ci",
    "côte d'ivoire": "ci",
    "croatia": "hr",
    "cuba": "cu",
    "cyprus": "cy",
    "czechia": "cz",
    "czech republic": "cz",
    "denmark": "dk",
    "djibouti": "dj",
    "dominica": "dm",
    "dominican republic": "do",
    "ecuador": "ec",
    "egypt": "eg",
    "el salvador": "sv",
    "equatorial guinea": "gq",
    "eritrea": "er",
    "estonia": "ee",
    "eswatini": "sz",
    "swaziland": "sz",
    "ethiopia": "et",
    "fiji": "fj",
    "finland": "fi",
    "france": "fr",
    "gabon": "ga",
    "gambia": "gm",
    "georgia": "ge",
    "germany": "de",
    "ghana": "gh",
    "greece": "gr",
    "grenada": "gd",
    "guatemala": "gt",
    "guinea": "gn",
    "guinea-bissau": "gw",
    "guyana": "gy",
    "haiti": "ht",
    "honduras": "hn",
    "hungary": "hu",
    "iceland": "is",
    "india": "in",
    "indonesia": "id",
    "iran": "ir",
    "iraq": "iq",
    "ireland": "ie",
    "israel": "il",
    "italy": "it",
    "jamaica": "jm",
    "japan": "jp",
    "jordan": "jo",
    "kazakhstan": "kz",
    "kenya": "ke",
    "kiribati": "ki",
    "kuwait": "kw",
    "kyrgyzstan": "kg",
    "laos": "la",
    "latvia": "lv",
    "lebanon": "lb",
    "lesotho": "ls",
    "liberia": "lr",
    "libya": "ly",
    "liechtenstein": "li",
    "lithuania": "lt",
    "luxembourg": "lu",
    "madagascar": "mg",
    "malawi": "mw",
    "malaysia": "my",
    "maldives": "mv",
    "mali": "ml",
    "malta": "mt",
    "marshall islands": "mh",
    "mauritania": "mr",
    "mauritius": "mu",
    "mexico": "mx",
    "micronesia": "fm",
    "moldova": "md",
    "monaco": "mc",
    "mongolia": "mn",
    "montenegro": "me",
    "morocco": "ma",
    "mozambique": "mz",
    "myanmar": "mm",
    "namibia": "na",
    "nauru": "nr",
    "nepal": "np",
    "netherlands": "nl",
    "new zealand": "nz",
    "nicaragua": "ni",
    "niger": "ne",
    "nigeria": "ng",
    "north korea": "kp",
    "democratic people's republic of korea": "kp",
    "norway": "no",
    "oman": "om",
    "pakistan": "pk",
    "palau": "pw",
    "palestine": "ps",
    "panama": "pa",
    "papua new guinea": "pg",
    "paraguay": "py",
    "peru": "pe",
    "philippines": "ph",
    "poland": "pl",
    "portugal": "pt",
    "qatar": "qa",
    "romania": "ro",
    "russia": "ru",
    "russian federation": "ru",
    "rwanda": "rw",
    "saint kitts and nevis": "kn",
    "saint lucia": "lc",
    "saint vincent and the grenadines": "vc",
    "samoa": "ws",
    "san marino": "sm",
    "sao tome and principe": "st",
    "são tomé and príncipe": "st",
    "saudi arabia": "sa",
    "senegal": "sn",
    "serbia": "rs",
    "seychelles": "sc",
    "sierra leone": "sl",
    "singapore": "sg",
    "slovakia": "sk",
    "slovenia": "si",
    "solomon islands": "sb",
    "somalia": "so",
    "south africa": "za",
    "south korea": "kr",
    "republic of korea": "kr",
    "spain": "es",
    "sri lanka": "lk",
    "sudan": "sd",
    "suriname": "sr",
    "sweden": "se",
    "switzerland": "ch",
    "syria": "sy",
    "tajikistan": "tj",
    "tanzania": "tz",
    "thailand": "th",
    "timor-leste": "tl",
    "togo": "tg",
    "tonga": "to",
    "trinidad and tobago": "tt",
    "tunisia": "tn",
    "turkey": "tr",
    "türkiye": "tr",
    "turkiye": "tr",
    "turkmenistan": "tm",
    "tuvalu": "tv",
    "uganda": "ug",
    "ukraine": "ua",
    "united arab emirates": "ae",
    "united kingdom": "gb",
    "united states": "us",
    "united states of america": "us",
    "uruguay": "uy",
    "uzbekistan": "uz",
    "vanuatu": "vu",
    "venezuela": "ve",
    "vietnam": "vn",
    "viet nam": "vn",
    "yemen": "ye",
    "zambia": "zm",
    "zimbabwe": "zw",
}


COUNTRY_ALIASES = {
    "Türkiye": [
        "Türkiye",
        "Turkiye",
        "Turkey",
        "TR",
    ],
    "Turkey": [
        "Turkey",
        "Türkiye",
        "Turkiye",
        "TR",
    ],
    "United States of America": [
        "United States of America",
        "United States",
        "USA",
        "US",
        "America",
    ],
    "United Kingdom": [
        "United Kingdom",
        "UK",
        "Britain",
        "Great Britain",
        "GB",
    ],
    "Russian Federation": [
        "Russian Federation",
        "Russia",
        "Russian",
        "RU",
    ],
    "Czechia": [
        "Czechia",
        "Czech Republic",
        "CZ",
    ],
    "Republic of Korea": [
        "Republic of Korea",
        "South Korea",
        "Korea",
        "KR",
    ],
    "Democratic People's Republic of Korea": [
        "Democratic People's Republic of Korea",
        "North Korea",
        "Korea DPR",
        "KP",
    ],
    "Viet Nam": [
        "Viet Nam",
        "Vietnam",
        "VN",
    ],
    "Côte d'Ivoire": [
        "Côte d'Ivoire",
        "Cote d'Ivoire",
        "Ivory Coast",
        "CI",
    ],
}


# ==========================================================
# GENEL YARDIMCI FONKSİYONLAR
# ==========================================================

def local_name(tag):
    """
    XML namespace varsa sadece gerçek tag adını döndürür.
    """
    if not tag:
        return ""

    if "}" in tag:
        tag = tag.split("}", 1)[1]

    return tag.strip().lower()


def clean_text(value):
    if value is None:
        return ""

    value = html.unescape(str(value))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_text(value):
    """
    Arama ve karşılaştırma için Türkçe dahil Unicode normalize eder.
    """
    value = clean_text(value)

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = value.lower()

    value = value.replace("’", "'")
    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def slug_filename(value):
    value = clean_text(value)

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = re.sub(
        r'[<>:"/\\|?*]',
        "",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    value = value.strip()

    return value


def split_tokens(value):
    normalized = normalize_text(value)

    return [
        token
        for token in normalized.split()
        if len(token) >= 3
    ]


def element_text(element):
    """
    Element içindeki tüm text parçalarını birleştirir.
    """
    if element is None:
        return ""

    parts = []

    for text in element.itertext():
        text = clean_text(text)

        if text:
            parts.append(text)

    return clean_text(" ".join(parts))


# ==========================================================
# UNESCO XML
# ==========================================================

def download_unesco_xml():
    print("=" * 70)
    print("UNESCO DÜNYA MİRAS LİSTESİ XML İNDİRİLİYOR")
    print("=" * 70)

    response = requests.get(
        UNESCO_XML_URL,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "PieceOfPast-UNESCO-Downloader/1.0 "
                "(GitHub Actions)"
            )
        }
    )

    print(
        f"UNESCO HTTP durumu: {response.status_code}"
    )

    response.raise_for_status()

    print(
        f"UNESCO XML boyutu: "
        f"{len(response.content):,} byte"
    )

    return response.content


def get_direct_children_map(row):
    """
    Bir UNESCO row içindeki doğrudan alanları çıkarır.
    """
    result = {}

    for child in list(row):
        tag = local_name(child.tag)

        if not tag:
            continue

        text = element_text(child)

        if text:
            if tag in result:
                result[tag] = (
                    result[tag]
                    + " | "
                    + text
                )
            else:
                result[tag] = text

    return result


def extract_country_from_element(row):
    """
    Ülke bilgisini farklı olası UNESCO XML yapılarından çıkarır.
    """

    candidates = []

    # Önce doğrudan child'lar
    for child in list(row):
        tag = local_name(child.tag)

        if tag in {
            "country",
            "countries",
            "stateparty",
            "state_party",
            "statesparty",
            "states_parties",
            "countryname",
            "country_name",
        }:
            text = element_text(child)

            if text:
                candidates.append(text)

    # Sonra descendant'lar
    if not candidates:
        for element in row.iter():
            tag = local_name(element.tag)

            if tag in {
                "country",
                "countries",
                "stateparty",
                "state_party",
                "statesparty",
                "states_parties",
                "countryname",
                "country_name",
            }:
                text = element_text(element)

                if text:
                    candidates.append(text)

    # XML attribute kontrolü
    if not candidates:
        for element in row.iter():
            for key, value in element.attrib.items():
                key_norm = local_name(key)

                if key_norm in {
                    "country",
                    "countryname",
                    "country_name",
                    "stateparty",
                    "state_party",
                }:
                    value = clean_text(value)

                    if value:
                        candidates.append(value)

    return candidates


def normalize_country_name(value):
    value = clean_text(value)

    if not value:
        return ""

    normalized = normalize_text(value)

    for canonical, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            if normalized == normalize_text(alias):
                return canonical

    for country, iso in ISO_CODES.items():
        if normalized == country:
            return country

    return value


def parse_country_values(row):
    raw_values = extract_country_from_element(row)

    countries = []

    for raw in raw_values:
        raw = clean_text(raw)

        if not raw:
            continue

        # Önce yaygın çoklu ayraçlar
        pieces = re.split(
            r"\s*[;|]\s*|\s*\n\s*",
            raw
        )

        for piece in pieces:
            piece = clean_text(piece)

            if not piece:
                continue

            normalized_piece = normalize_text(piece)

            # Tek bir ülke ise doğrudan kabul
            if (
                normalized_piece in ISO_CODES
                or any(
                    normalized_piece
                    == normalize_text(alias)
                    for aliases in COUNTRY_ALIASES.values()
                    for alias in aliases
                )
            ):
                countries.append(
                    normalize_country_name(piece)
                )
                continue

            # Virgüllü değerlerde sadece bilinen ülke adlarını
            # ayıklamaya çalış.
            comma_parts = [
                clean_text(x)
                for x in piece.split(",")
            ]

            if len(comma_parts) > 1:
                found_any = False

                for cp in comma_parts:
                    cp_norm = normalize_text(cp)

                    if (
                        cp_norm in ISO_CODES
                        or any(
                            cp_norm
                            == normalize_text(alias)
                            for aliases in COUNTRY_ALIASES.values()
                            for alias in aliases
                        )
                    ):
                        countries.append(
                            normalize_country_name(cp)
                        )
                        found_any = True

                if found_any:
                    continue

            countries.append(
                normalize_country_name(piece)
            )

    # Tekrarlardan arındır
    result = []

    seen = set()

    for country in countries:
        key = normalize_text(country)

        if key and key not in seen:
            seen.add(key)
            result.append(country)

    return result


def parse_unesco_xml(xml_bytes):
    print("=" * 70)
    print("UNESCO XML PARSE EDİLİYOR")
    print("=" * 70)

    root = ET.fromstring(xml_bytes)

    print(
        f"XML root etiketi: "
        f"{local_name(root.tag)}"
    )

    rows = [
        element
        for element in root.iter()
        if local_name(element.tag) == "row"
    ]

    print(
        f"UNESCO kayıt sayısı: {len(rows)}"
    )

    records = []

    for index, row in enumerate(rows, start=1):

        fields = get_direct_children_map(row)

        site_name = ""

        # En muhtemel UNESCO alan adları
        for key in [
            "site",
            "name",
            "property",
            "propertyname",
            "site_name",
            "sitename",
            "name_en",
            "official_name",
        ]:
            if fields.get(key):
                site_name = clean_text(
                    fields[key]
                )
                break

        # Eğer doğrudan child'da bulamadıysak
        if not site_name:
            for element in row.iter():
                tag = local_name(element.tag)

                if tag in {
                    "site",
                    "name",
                    "propertyname",
                    "site_name",
                    "sitename",
                    "official_name",
                }:
                    text = element_text(element)

                    if text:
                        site_name = text
                        break

        if not site_name:
            continue

        countries = parse_country_values(row)

        record = {
            "id": index,
            "site": site_name,
            "countries": countries,
        }

        records.append(record)

    print(
        f"Başarıyla parse edilen kayıt: "
        f"{len(records)}"
    )

    countries_found = set()

    for record in records:
        for country in record["countries"]:
            countries_found.add(country)

    print(
        f"UNESCO kayıtlarında bulunan farklı "
        f"ülke sayısı: {len(countries_found)}"
    )

    # İlk 5 kaydı özellikle göster
    print("=" * 70)
    print("İLK 5 UNESCO KAYDI KONTROLÜ")
    print("=" * 70)

    for record in records[:5]:
        print(
            f"{record['site']} | "
            f"Ülke: "
            f"{', '.join(record['countries']) or 'YOK'}"
        )

    return records


# ==========================================================
# BAYRAK KONTROLÜ
# ==========================================================

def get_flag_files():
    """
    Kullanıcının manuel yüklediği ülke bayraklarını okur.

    Bu fonksiyon sadece okur.
    Hiçbir dosyayı silmez veya değiştirmez.
    """

    if not os.path.isdir(FLAGS_DIR):
        return []

    files = []

    for filename in os.listdir(FLAGS_DIR):

        path = os.path.join(
            FLAGS_DIR,
            filename
        )

        if not os.path.isfile(path):
            continue

        ext = os.path.splitext(
            filename
        )[1].lower()

        if ext not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }:
            continue

        files.append(filename)

    return files


def flag_matches_country(filename, country):
    base = os.path.splitext(
        filename
    )[0]

    base_norm = normalize_text(base)
    country_norm = normalize_text(country)

    # Doğrudan isim
    if base_norm == country_norm:
        return True

    # ISO kodu
    iso = ISO_CODES.get(country_norm)

    if iso and base_norm == iso:
        return True

    # Alias
    aliases = COUNTRY_ALIASES.get(
        country,
        []
    )

    for alias in aliases:

        if base_norm == normalize_text(alias):
            return True

    return False


def find_country_flag(country):
    flag_files = get_flag_files()

    for filename in flag_files:

        if flag_matches_country(
            filename,
            country
        ):
            return os.path.join(
                FLAGS_DIR,
                filename
            )

    return None


def verify_country_flags(records):
    print("=" * 70)
    print("ÜLKE BAYRAKLARI KONTROLÜ")
    print("=" * 70)

    countries = set()

    for record in records:
        for country in record["countries"]:
            countries.add(country)

    print(
        f"UNESCO kayıtlarında bulunan farklı "
        f"ülke sayısı: {len(countries)}"
    )

    if not countries:
        print()
        print(
            "HATA: UNESCO kayıtlarından ülke "
            "bilgisi çıkarılamadı."
        )
        print(
            "Bu nedenle işlem güvenli şekilde "
            "durduruluyor."
        )
        print()
        return False

    missing = []

    for country in sorted(countries):

        if not find_country_flag(country):
            missing.append(country)

    if missing:

        print(
            f"EKSİK BAYRAK SAYISI: {len(missing)}"
        )

        for country in missing:
            print(
                f"  [EKSIK] {country}"
            )

        print()
        print(
            "Eksik bayrak bulunduğu için işlem "
            "durduruluyor."
        )

        return False

    print(
        "TÜM GEREKLİ ÜLKE BAYRAKLARI BULUNDU."
    )

    return True


# ==========================================================
# DOSYA İSİMLERİ
# ==========================================================

def get_primary_country(record):
    countries = record.get(
        "countries",
        []
    )

    if countries:
        return countries[0]

    return "Unknown"


def make_image_filename(record):
    site = slug_filename(
        record["site"]
    )

    country = slug_filename(
        get_primary_country(record)
    )

    if not country:
        country = "Unknown"

    return (
        f"{site} - {country}.jpg"
    )


# ==========================================================
# WIKIMEDIA COMMONS
# ==========================================================

def commons_api(params):
    params = dict(params)

    params["format"] = "json"
    params["formatversion"] = "2"

    headers = {
        "User-Agent": (
            "PieceOfPast-UNESCO-Downloader/1.0 "
            "(GitHub Actions; Wikimedia Commons API)"
        )
    }

    time.sleep(
        REQUEST_DELAY
    )

    response = requests.get(
        COMMONS_API,
        params=params,
        timeout=REQUEST_TIMEOUT,
        headers=headers
    )

    response.raise_for_status()

    return response.json()


def is_bad_filename(title):
    title_lower = title.lower()

    for ext in BAD_EXTENSIONS:
        if title_lower.endswith(ext):
            return True

    bad_words = [
        "world factbook",
        "location map",
        "locator map",
        "blank map",
        "coat of arms",
        "flag of",
        "logo",
        "poster",
        "stamp",
        "coin",
        "book cover",
        "screenshot",
        "diagram",
        "chart",
        "document",
        "brochure",
        "pdf",
    ]

    normalized = normalize_text(
        title_lower
    )

    for word in bad_words:
        if normalize_text(word) in normalized:
            return True

    return False


def get_imageinfo(titles):
    if not titles:
        return {}

    params = {
        "action": "query",
        "prop": "imageinfo",
        "titles": "|".join(titles),
        "iiprop": (
            "url|mime|size|extmetadata"
        ),
        "iiurlwidth": "1600",
    }

    data = commons_api(params)

    result = {}

    pages = (
        data
        .get("query", {})
        .get("pages", [])
    )

    for page in pages:

        title = page.get(
            "title",
            ""
        )

        imageinfo = page.get(
            "imageinfo",
            []
        )

        if not imageinfo:
            continue

        info = imageinfo[0]

        result[title] = info

    return result


def search_commons(query):
    """
    Commons'ta dosya namespace'inde arama yapar.
    """

    params = {
        "action": "query",
        "list": "search",
        "srnamespace": "6",
        "srsearch": query,
        "srwhat": "title",
        "srsort": "relevance",
        "srlimit": str(
            MAX_SEARCH_RESULTS
        ),
        "srprop": "size",
    }

    data = commons_api(params)

    return data.get(
        "query",
        {}
    ).get(
        "search",
        []
    )


def candidate_score(
    title,
    info,
    site_name,
    countries
):
    """
    Commons adayına kalite/alaka puanı verir.
    """

    title_norm = normalize_text(
        title
    )

    site_norm = normalize_text(
        site_name
    )

    score = 0

    # ------------------------------------------------------
    # Dosya türü
    # ------------------------------------------------------

    mime = (
        info
        .get("mime", "")
        .lower()
    )

    if mime not in ALLOWED_MIMES:
        return -10000

    # ------------------------------------------------------
    # Kötü dosya adı
    # ------------------------------------------------------

    if is_bad_filename(title):
        return -10000

    # ------------------------------------------------------
    # Site adı
    # ------------------------------------------------------

    site_tokens = split_tokens(
        site_name
    )

    matched_site_tokens = 0

    for token in site_tokens:

        if token in title_norm:
            matched_site_tokens += 1
            score += 8

    if site_norm and site_norm in title_norm:
        score += 60

    if matched_site_tokens >= 3:
        score += 30

    if matched_site_tokens >= 5:
        score += 20

    # ------------------------------------------------------
    # Ülke adı
    # ------------------------------------------------------

    for country in countries:

        country_norm = normalize_text(
            country
        )

        country_tokens = split_tokens(
            country
        )

        if (
            country_norm
            and country_norm in title_norm
        ):
            score += 20

        for token in country_tokens:
            if token in title_norm:
                score += 3

        iso = ISO_CODES.get(
            country_norm
        )

        if iso and iso in title_norm:
            score += 2

    # ------------------------------------------------------
    # UNESCO kelimesi
    # ------------------------------------------------------

    if "unesco" in title_norm:
        score += 10

    if "world heritage" in title_norm:
        score += 8

    # ------------------------------------------------------
    # Boyut
    # ------------------------------------------------------

    try:
        width = int(
            info.get("width", 0)
        )

        height = int(
            info.get("height", 0)
        )

        if width >= 1000 and height >= 600:
            score += 15

        elif width >= 700 and height >= 400:
            score += 8

        elif width < 400 or height < 300:
            score -= 20

    except Exception:
        pass

    # ------------------------------------------------------
    # Açıklama
    # ------------------------------------------------------

    metadata = info.get(
        "extmetadata",
        {}
    )

    description = ""

    for key in [
        "ImageDescription",
        "ObjectName",
        "Categories",
    ]:

        value = metadata.get(
            key,
            {}
        )

        if isinstance(value, dict):
            value = value.get(
                "value",
                ""
            )

        if value:
            description += " "
            description += clean_text(
                value
            )

    description_norm = normalize_text(
        description
    )

    if site_norm and site_norm in description_norm:
        score += 35

    if "unesco" in description_norm:
        score += 8

    if "world heritage" in description_norm:
        score += 8

    return score


def get_license(info):
    metadata = info.get(
        "extmetadata",
        {}
    )

    possible_keys = [
        "LicenseShortName",
        "License",
        "UsageTerms",
    ]

    for key in possible_keys:

        value = metadata.get(
            key,
            {}
        )

        if isinstance(value, dict):
            value = value.get(
                "value",
                ""
            )

        value = clean_text(
            value
        )

        if value:
            return value

    return ""


def is_reusable_license(license_text):
    normalized = normalize_text(
        license_text
    )

    if not normalized:
        return False

    allowed = [
        "public domain",
        "cc0",
        "cc by",
        "cc by sa",
        "cc by-sa",
        "creative commons attribution",
        "creative commons attribution sharealike",
    ]

    for item in allowed:

        if normalize_text(item) in normalized:
            return True

    return False


def find_best_commons_image(
    site_name,
    countries
):

    queries = []

    # Önce tam site adına yakın arama
    queries.append(
        f'"{site_name}"'
    )

    # UNESCO ile ikinci arama
    queries.append(
        f'"{site_name}" UNESCO'
    )

    # Çok uzun isimlerde daha genel arama
    tokens = split_tokens(
        site_name
    )

    if len(tokens) >= 3:
        short_query = " ".join(
            tokens[:6]
        )

        queries.append(
            short_query
        )

    all_candidates = {}

    for query in queries:

        print(
            f"  Commons araması: {query}"
        )

        try:
            results = search_commons(
                query
            )

        except Exception as exc:

            print(
                f"  [UYARI] Commons arama "
                f"hatası: {exc}"
            )

            continue

        if not results:
            continue

        titles = []

        for item in results:

            title = item.get(
                "title",
                ""
            )

            if not title:
                continue

            if is_bad_filename(title):
                continue

            titles.append(
                title
            )

        if not titles:
            continue

        try:
            imageinfo = get_imageinfo(
                titles
            )

        except Exception as exc:

            print(
                f"  [UYARI] Görsel bilgisi "
                f"alınamadı: {exc}"
            )

            continue

        for title, info in imageinfo.items():

            mime = info.get(
                "mime",
                ""
            ).lower()

            if mime not in ALLOWED_MIMES:
                continue

            score = candidate_score(
                title,
                info,
                site_name,
                countries
            )

            if score <= -1000:
                continue

            # Aynı dosya birden fazla aramada
            # bulunursa en yüksek puanı tut.
            if (
                title not in all_candidates
                or score
                > all_candidates[title]["score"]
            ):

                all_candidates[title] = {
                    "title": title,
                    "info": info,
                    "score": score,
                    "query": query,
                }

        # İlk aramada güçlü aday bulduysak
        # gereksiz ikinci/üçüncü aramaları yapma.
        if all_candidates:

            best = max(
                all_candidates.values(),
                key=lambda x: x["score"]
            )

            if best["score"] >= 70:
                break

    if not all_candidates:
        return None

    ranked = sorted(
        all_candidates.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    # Lisansı uygun olan adayları önceliklendir.
    reusable = [
        candidate
        for candidate in ranked
        if is_reusable_license(
            get_license(
                candidate["info"]
            )
        )
    ]

    if reusable:
        ranked = reusable

    best = ranked[0]

    # Çok düşük alakalı sonuçları kaydetme.
    if best["score"] < 25:

        print(
            f"  [ATLANDI] Yeterli alakalı "
            f"görsel bulunamadı."
        )

        print(
            f"  En iyi aday puanı: "
            f"{best['score']}"
        )

        return None

    title = best["title"]
    info = best["info"]

    print(
        f"  Bulunan görsel: {title}"
    )

    print(
        f"  Puan: {best['score']}"
    )

    license_text = get_license(
        info
    )

    print(
        f"  Lisans: "
        f"{license_text or 'Bilinmiyor'}"
    )

    return {
        "title": title,
        "info": info,
        "score": best["score"],
        "query": best["query"],
    }


# ==========================================================
# GÖRSEL İNDİRME
# ==========================================================

def get_download_url(info):
    """
    Wikimedia'nin thumbnail URL'sini
    tercih eder. Orijinal yoksa URL'ye düşer.
    """

    url = info.get(
        "thumburl"
    )

    if url:
        return url

    url = info.get(
        "url"
    )

    return url


def download_and_convert(
    url,
    output_path
):
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "PieceOfPast-UNESCO-Downloader/1.0"
            )
        }
    )

    response.raise_for_status()

    content = response.content

    if not content:
        raise ValueError(
            "Boş dosya indirildi."
        )

    # Gerçekten görüntü mü?
    image = Image.open(
        io.BytesIO(content)
    )

    image.load()

    # RGB'ye çevir
    if image.mode in {
        "RGBA",
        "LA",
        "P",
    }:

        background = Image.new(
            "RGB",
            image.size,
            "white"
        )

        if image.mode == "P":
            image = image.convert(
                "RGBA"
            )

        if image.mode in {
            "RGBA",
            "LA",
        }:

            background.paste(
                image,
                mask=image.getchannel(
                    "A"
                )
            )

            image = background

        else:
            image = image.convert(
                "RGB"
            )

    else:
        image = image.convert(
            "RGB"
        )

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    image.save(
        output_path,
        "JPEG",
        quality=92,
        optimize=True
    )

    return image.size


# ==========================================================
# KAYNAK BİLGİLERİ
# ==========================================================

def load_sources():
    if not os.path.exists(
        SOURCES_FILE
    ):
        return {}

    try:

        with open(
            SOURCES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

            if isinstance(data, dict):
                return data

    except Exception as exc:

        print(
            f"[UYARI] image_sources.json "
            f"okunamadı: {exc}"
        )

    return {}


def save_sources(sources):

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    with open(
        SOURCES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            sources,
            file,
            ensure_ascii=False,
            indent=2
        )


def get_author(info):
    metadata = info.get(
        "extmetadata",
        {}
    )

    for key in [
        "Artist",
        "Credit",
        "Author",
    ]:

        value = metadata.get(
            key,
            {}
        )

        if isinstance(value, dict):
            value = value.get(
                "value",
                ""
            )

        value = clean_text(
            value
        )

        if value:
            # HTML taglerini basitçe temizle
            value = re.sub(
                r"<[^>]+>",
                "",
                value
            )

            return html.unescape(
                value
            )

    return ""


def add_source_record(
    sources,
    output_filename,
    record,
    candidate
):

    info = candidate["info"]

    title = candidate["title"]

    sources[output_filename] = {
        "site": record["site"],
        "countries": record["countries"],
        "file": output_filename,
        "source": "Wikimedia Commons",
        "commons_file": title,
        "source_url": info.get(
            "descriptionurl",
            ""
        ),
        "image_url": info.get(
            "url",
            ""
        ),
        "author": get_author(
            info
        ),
        "license": get_license(
            info
        ),
        "search_query": candidate[
            "query"
        ],
        "match_score": candidate[
            "score"
        ],
    }


# ==========================================================
# PARÇA HESAPLAMA
# ==========================================================

def get_chunk_range(
    total,
    chunk
):
    """
    3 parçaya mümkün olduğunca eşit böler.

    Örnek:
    1273 -> 425 / 425 / 423
    """

    base = total // 3
    remainder = total % 3

    sizes = []

    for i in range(3):

        size = base

        if i < remainder:
            size += 1

        sizes.append(
            size
        )

    start = sum(
        sizes[:chunk - 1]
    )

    end = start + sizes[
        chunk - 1
    ]

    return start, end, sizes


def get_requested_chunk():
    if len(sys.argv) < 2:
        print(
            "Kullanım:"
        )
        print(
            "  python download_assets.py unesco-1"
        )
        print(
            "  python download_assets.py unesco-2"
        )
        print(
            "  python download_assets.py unesco-3"
        )

        sys.exit(1)

    mode = sys.argv[1].strip().lower()

    mapping = {
        "unesco-1": 1,
        "unesco-2": 2,
        "unesco-3": 3,
    }

    if mode not in mapping:

        print(
            f"Geçersiz mod: {mode}"
        )

        sys.exit(1)

    return mode, mapping[mode]


# ==========================================================
# ANA PROGRAM
# ==========================================================

def main():

    print("=" * 70)
    print("PIECE OF PAST")
    print("UNESCO WORLD HERITAGE ASSET DOWNLOADER")
    print("=" * 70)

    mode, chunk_number = (
        get_requested_chunk()
    )

    print(
        f"Mod: {mode}"
    )

    # ------------------------------------------------------
    # UNESCO XML
    # ------------------------------------------------------

    try:
        xml_bytes = (
            download_unesco_xml()
        )

        records = parse_unesco_xml(
            xml_bytes
        )

    except Exception as exc:

        print()
        print(
            "[KRİTİK HATA] UNESCO XML "
            f"işlenemedi: {exc}"
        )

        sys.exit(1)

    if not records:

        print(
            "[KRİTİK HATA] UNESCO kaydı "
            "bulunamadı."
        )

        sys.exit(1)

    # ------------------------------------------------------
    # BAYRAKLAR
    # ------------------------------------------------------

    if not verify_country_flags(
        records
    ):
        sys.exit(1)

    # ------------------------------------------------------
    # 3 PARÇA
    # ------------------------------------------------------

    total = len(records)

    start, end, sizes = (
        get_chunk_range(
            total,
            chunk_number
        )
    )

    chunk_records = records[
        start:end
    ]

    print("=" * 70)
    print(f"{mode} BAŞLIYOR")
    print(
        f"Toplam UNESCO kaydı: {total}"
    )

    print(
        f"3 parça dağılımı: "
        f"{sizes[0]} / "
        f"{sizes[1]} / "
        f"{sizes[2]}"
    )

    print(
        f"Aralık: "
        f"{start + 1}-{end} / {total}"
    )

    print(
        f"Bu parçada: "
        f"{len(chunk_records)} kayıt"
    )

    print("=" * 70)

    # ------------------------------------------------------
    # KLASÖRLER
    # ------------------------------------------------------

    os.makedirs(
        UNESCO_DIR,
        exist_ok=True
    )

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    # ------------------------------------------------------
    # KAYNAK DOSYASI
    # ------------------------------------------------------

    sources = load_sources()

    downloaded = 0
    skipped = 0
    errors = 0

    # ------------------------------------------------------
    # SİTELER
    # ------------------------------------------------------

    for local_index, record in enumerate(
        chunk_records,
        start=1
    ):

        global_index = start + local_index

        site_name = record[
            "site"
        ]

        countries = record[
            "countries"
        ]

        output_filename = (
            make_image_filename(
                record
            )
        )

        output_path = os.path.join(
            UNESCO_DIR,
            output_filename
        )

        print()
        print(
            "=" * 70
        )

        print(
            f"[{global_index}/{total}] "
            f"{site_name}"
        )

        print(
            f"  Ülke: "
            f"{', '.join(countries) or 'Unknown'}"
        )

        print(
            f"  Hedef: "
            f"{output_filename}"
        )

        # --------------------------------------------------
        # Mevcut dosya varsa tekrar indirme
        # --------------------------------------------------

        if os.path.exists(
            output_path
        ):

            print(
                "  [MEVCUT] Dosya zaten var."
            )

            downloaded += 1

            continue

        # --------------------------------------------------
        # Commons
        # --------------------------------------------------

        try:

            candidate = (
                find_best_commons_image(
                    site_name,
                    countries
                )
            )

        except Exception as exc:

            print(
                f"  [HATA] Commons işlemi: "
                f"{exc}"
            )

            errors += 1
            continue

        if not candidate:

            print(
                "  [ATLANDI] Uygun görsel bulunamadı."
            )

            skipped += 1

            continue

        # --------------------------------------------------
        # Görsel URL
        # --------------------------------------------------

        image_url = get_download_url(
            candidate["info"]
        )

        if not image_url:

            print(
                "  [ATLANDI] Görsel URL'si yok."
            )

            skipped += 1

            continue

        print(
            f"  İndiriliyor: "
            f"{image_url}"
        )

        # --------------------------------------------------
        # İndir + JPG yap
        # --------------------------------------------------

        try:

            size = download_and_convert(
                image_url,
                output_path
            )

            print(
                f"  [OK] {site_name} - "
                f"{get_primary_country(record)}.jpg"
            )

            print(
                f"  Boyut: "
                f"{size[0]}x{size[1]}"
            )

            add_source_record(
                sources,
                output_filename,
                record,
                candidate
            )

            save_sources(
                sources
            )

            downloaded += 1

        except Exception as exc:

            print(
                f"  [HATA] Görsel indirilemedi: "
                f"{exc}"
            )

            # Hatalı/yarım dosya kaldıysa sil
            if os.path.exists(
                output_path
            ):
                try:
                    os.remove(
                        output_path
                    )
                except Exception:
                    pass

            errors += 1

    # ------------------------------------------------------
    # SONUÇ
    # ------------------------------------------------------

    print()
    print("=" * 70)
    print(f"{mode} TAMAMLANDI")
    print("=" * 70)

    print(
        f"Toplam kayıt: {len(chunk_records)}"
    )

    print(
        f"İndirilen/mevcut: {downloaded}"
    )

    print(
        f"Atlanan: {skipped}"
    )

    print(
        f"Hata: {errors}"
    )

    print()
    print(
        f"Kaynak dosyası: {SOURCES_FILE}"
    )

    print(
        "Not: 'ülkeler' klasöründeki "
        "manuel bayraklara dokunulmadı."
    )

    print("=" * 70)

    # Eğer bütün kayıtlar başarısızsa
    # workflow'un sessizce başarılı görünmesini engelle.
    if downloaded == 0 and len(
        chunk_records
    ) > 0:

        print(
            "[KRİTİK] Bu parçada hiçbir "
            "görsel indirilemedi."
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
