import sys
import re
import json
import time
import unicodedata
from pathlib import Path

import requests
from PIL import Image
from io import BytesIO
import xml.etree.ElementTree as ET


# ============================================================
# AYARLAR
# ============================================================

ROOT = Path(__file__).resolve().parent

COUNTRY_DIR = ROOT / "ülkeler"
SITE_DIR = ROOT / "unesco dünya mirasları"
DATA_DIR = ROOT / "data"

SITE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

UNESCO_XML_URL = "https://whc.unesco.org/en/list/xml/"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = (
    "PieceOfPast/1.0 "
    "(https://github.com/mgagames23/PIECE-OF-PAST; UNESCO image downloader)"
)

REQUEST_TIMEOUT = 45

# Wikimedia'nın güncel API tavsiyelerine uygun olarak
# istekleri seri şekilde gönderiyoruz.
WIKIMEDIA_DELAY = 3.0

MAX_RETRIES = 8

# 1273 UNESCO mülkünü 3 ardışık bölüme ayırıyoruz.
PART_RANGES = {
    "unesco-1": (0, 424),
    "unesco-2": (424, 848),
    "unesco-3": (848, 1273),
}


# ============================================================
# ÜLKE ALIASLARI
# ============================================================

COUNTRY_ALIASES = {
    "Türkiye": ["Türkiye", "Turkey", "Turkiye"],
    "Czechia": ["Czechia", "Czech Republic"],
    "Czech Republic": ["Czechia", "Czech Republic"],
    "Russian Federation": ["Russian Federation", "Russia"],
    "Russia": ["Russian Federation", "Russia"],
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
    "Congo": [
        "Congo",
        "Republic of the Congo",
    ],
    "Republic of the Congo": [
        "Congo",
        "Republic of the Congo",
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
    "United Republic of Tanzania": [
        "United Republic of Tanzania",
        "Tanzania",
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
    "Türkiye": [
        "Türkiye",
        "Turkey",
        "Turkiye",
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
    "Yemen": "ye",
    "Zambia": "zm",
    "Zimbabwe": "zw",
}


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def normalize_text(text):
    text = str(text or "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text = text.lower()
    text = text.replace("’", "'")
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def clean_filename(text):
    text = str(text or "").strip()
    text = re.sub(r'[<>:"/\\|?*]', "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def get_country_variants(country):
    variants = [country]

    if country in COUNTRY_ALIASES:
        variants.extend(COUNTRY_ALIASES[country])

    for key, values in COUNTRY_ALIASES.items():
        if country in values:
            variants.append(key)
            variants.extend(values)

    # benzersiz
    result = []
    seen = set()

    for item in variants:
        n = normalize_text(item)

        if n and n not in seen:
            seen.add(n)
            result.append(item)

    return result


def find_country_image(country):
    """
    GitHub'a manuel yüklenen bayrağı bulur.

    Kabul edilen örnekler:
        Turkey.jpg
        Türkiye.jpg
        Turkiye.jpg
        tr.jpg
        TR.jpg

    PNG/JPEG/JPG hepsi kabul edilir.
    """

    if not COUNTRY_DIR.exists():
        return None

    variants = get_country_variants(country)

    wanted = {
        normalize_text(v)
        for v in variants
    }

    iso_candidates = set()

    for variant in variants:
        if variant in ISO_CODES:
            iso_candidates.add(ISO_CODES[variant])

    # Dosyaları tek seferde tarıyoruz.
    for path in COUNTRY_DIR.iterdir():

        if not path.is_file():
            continue

        if path.suffix.lower() not in {
            ".jpg",
            ".jpeg",
            ".png",
        }:
            continue

        stem_norm = normalize_text(path.stem)

        if stem_norm in wanted:
            return path

        if stem_norm in iso_candidates:
            return path

    return None


def parse_unesco_xml():
    print("UNESCO Dünya Mirası XML indiriliyor...")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip",
    }

    response = requests.get(
        UNESCO_XML_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    root = ET.fromstring(response.content)

    sites = []

    for child in root.iter():
        if child.tag.lower().endswith("site"):
            name = (
                child.findtext("site")
                or child.findtext("name")
                or ""
            ).strip()

            country = (
                child.findtext("country")
                or child.findtext("countries")
                or ""
            ).strip()

            if not name:
                continue

            countries = [
                x.strip()
                for x in re.split(r"\s*,\s*", country)
                if x.strip()
            ]

            sites.append({
                "name": name,
                "countries": countries,
            })

    # Aynı site tekrar gelirse temizle
    unique = []
    seen = set()

    for site in sites:
        key = (
            site["name"],
            tuple(site["countries"]),
        )

        if key not in seen:
            seen.add(key)
            unique.append(site)

    sites = unique

    print(f"UNESCO sites sayisi: {len(sites)}")

    if len(sites) < 1200:
        raise RuntimeError(
            f"UNESCO XML beklenenden az site içeriyor: {len(sites)}"
        )

    return sites


# ============================================================
# WIKIMEDIA
# ============================================================

def wikipedia_request(params):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip",
    }

    delay = WIKIMEDIA_DELAY

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = requests.get(
                WIKIMEDIA_API,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        wait = max(5, int(retry_after))
                    except ValueError:
                        wait = delay * 2
                else:
                    wait = max(5, delay * 2)

                print(
                    f"Wikimedia 429. {wait} saniye bekleniyor..."
                )

                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue

            if response.status_code in {500, 502, 503, 504}:
                wait = min(delay * 2, 60)

                print(
                    f"Wikimedia HTTP {response.status_code}. "
                    f"{wait} saniye bekleniyor..."
                )

                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue

            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error_code = data["error"].get("code", "")
                error_info = data["error"].get("info", "")

                print(
                    f"Wikimedia API hatasi: "
                    f"{error_code} - {error_info}"
                )

                if error_code in {
                    "maxlag",
                    "ratelimited",
                }:
                    wait = min(delay * 2, 60)
                    time.sleep(wait)
                    delay = min(delay * 2, 60)
                    continue

                return None

            time.sleep(WIKIMEDIA_DELAY)

            return data

        except requests.RequestException as exc:

            wait = min(delay * 2, 60)

            print(
                f"Wikimedia istek hatasi "
                f"(deneme {attempt}/{MAX_RETRIES}): {exc}"
            )

            if attempt == MAX_RETRIES:
                return None

            time.sleep(wait)
            delay = min(delay * 2, 60)

    return None


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

    data = wikipedia_request(params)

    if not data:
        return []

    pages = data.get("query", {}).get("pages", {})

    results = []

    for page in pages.values():

        imageinfo = page.get("imageinfo") or []

        if not imageinfo:
            continue

        info = imageinfo[0]

        url = (
            info.get("thumburl")
            or info.get("url")
        )

        if url:
            results.append({
                "title": page.get("title", ""),
                "url": url,
            })

    return results


# ============================================================
# GÖRSEL İNDİRME
# ============================================================

def save_jpg(url, destination):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip",
    }

    delay = 5

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        wait = max(5, int(retry_after))
                    except ValueError:
                        wait = delay
                else:
                    wait = delay

                print(
                    f"Görsel 429. {wait} saniye bekleniyor..."
                )

                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue

            if response.status_code in {500, 502, 503, 504}:
                wait = delay

                print(
                    f"Görsel HTTP {response.status_code}. "
                    f"{wait} saniye bekleniyor..."
                )

                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue

            response.raise_for_status()

            image = Image.open(
                BytesIO(response.content)
            )

            if image.width < 200 or image.height < 200:
                print(
                    f"Çok küçük görsel atlandı: "
                    f"{image.width}x{image.height}"
                )
                return False

            image = image.convert("RGB")

            image.save(
                destination,
                "JPEG",
                quality=88,
                optimize=True,
            )

            return True

        except Exception as exc:

            print(
                f"Görsel kaydetme hatasi "
                f"(deneme {attempt}/{MAX_RETRIES}): {exc}"
            )

            if attempt == MAX_RETRIES:
                return False

            time.sleep(delay)
            delay = min(delay * 2, 60)

    return False


# ============================================================
# ÜLKE BAYRAKLARINI SADECE KONTROL ET
# ============================================================

def verify_country_flags(sites):
    countries = set()

    for site in sites:
        for country in site["countries"]:
            countries.add(country)

    countries = sorted(countries)

    print()
    print("=" * 60)
    print("ÜLKE BAYRAKLARI KONTROL EDİLİYOR")
    print("=" * 60)
    print(f"UNESCO listesinde kullanılan ülke sayisi: {len(countries)}")
    print()

    missing = []

    for country in countries:

        image = find_country_image(country)

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
    print(
        f"Bulunan bayrak: "
        f"{len(countries) - len(missing)}/{len(countries)}"
    )

    if missing:
        print()
        print("Eksik bayraklar:")

        for country in missing:
            print(f" - {country}")

        raise RuntimeError(
            f"{len(missing)} UNESCO ülkesi için bayrak bulunamadı."
        )

    print()
    print("TÜM UNESCO ÜLKELERİNİN BAYRAKLARI MEVCUT.")
    print()


# ============================================================
# UNESCO GÖRSELLERİ
# ============================================================

def build_site_filename(site):
    name = clean_filename(site["name"])

    country = (
        site["countries"][0]
        if site["countries"]
        else "Unknown"
    )

    country = clean_filename(country)

    return f"{name} - {country}.jpg"


def search_site_image(site):
    name = site["name"]
    countries = site["countries"]

    queries = []

    country = (
        countries[0]
        if countries
        else ""
    )

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

    queries.append(name)

    seen_urls = set()

    for query in queries:

        print(f"  Wikimedia arama: {query}")

        results = commons_search(query)

        for result in results:

            url = result["url"]

            if url in seen_urls:
                continue

            seen_urls.add(url)

            return result

    return None


def download_site_images(sites, start, end, mode):
    selected = sites[start:end]

    print()
    print("=" * 70)
    print(
        f"{mode} BASLIYOR | "
        f"{start + 1}-{end} / {len(sites)}"
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

        filename = build_site_filename(site)
        destination = SITE_DIR / filename

        print(
            f"[{absolute_index}/{len(sites)}] "
            f"{site['name']}"
        )

        if destination.exists() and destination.stat().st_size > 0:
            print("  [SKIP] Zaten mevcut.")
            skipped += 1
            continue

        result = search_site_image(site)

        if not result:
            print("  [HATA] Wikimedia'da görsel bulunamadı.")
            failed += 1
            continue

        print(
            f"  Görsel: {result['title']}"
        )

        if save_jpg(
            result["url"],
            destination,
        ):
            print(
                f"  [OK] {destination.name}"
            )
            downloaded += 1
        else:
            print("  [HATA] Görsel indirilemedi.")
            failed += 1

    print()
    print("=" * 70)
    print(f"{mode} TAMAMLANDI")
    print(f"Yeni indirilen: {downloaded}")
    print(f"Zaten mevcut:   {skipped}")
    print(f"Başarısız:      {failed}")
    print("=" * 70)
    print()


# ============================================================
# JSON
# ============================================================

def create_json(sites):
    site_files = {}

    for path in SITE_DIR.glob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() != ".jpg":
            continue

        site_files[path.name] = str(
            path.relative_to(ROOT)
        ).replace("\\", "/")

    unesco_data = []

    for site in sites:

        filename = build_site_filename(site)

        unesco_data.append({
            "name": site["name"],
            "countries": site["countries"],
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
        image_sources[filename] = {
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

    print("JSON dosyalari güncellendi.")


# ============================================================
# MOD
# ============================================================

def get_mode():
    if len(sys.argv) < 2:
        raise RuntimeError(
            "Mod belirtilmedi. "
            "Kullanım: unesco-1 / unesco-2 / unesco-3"
        )

    mode = sys.argv[1].strip().lower()

    if mode not in PART_RANGES:
        raise RuntimeError(
            f"Geçersiz mod: {mode}"
        )

    return mode


# ============================================================
# MAIN
# ============================================================

def main():

    mode = get_mode()

    print()
    print("PIECE OF PAST - UNESCO ASSET DOWNLOADER")
    print(f"Mod: {mode}")
    print()

    # UNESCO listesini al
    sites = parse_unesco_xml()

    # BAYRAKLARA SADECE BAKIYORUZ.
    # İNDİRME / SİLME / DEĞİŞTİRME YOK.
    verify_country_flags(sites)

    start, end = PART_RANGES[mode]

    # UNESCO görselleri
    download_site_images(
        sites,
        start,
        end,
        mode,
    )

    # JSON
    create_json(sites)

    print()
    print(f"{mode} başarıyla tamamlandı.")
    print()


if __name__ == "__main__":
    main()
