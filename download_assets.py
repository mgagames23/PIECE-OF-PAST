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
UA = "PieceOfPast/1.0"

ALIASES = {
    "Türkiye": "Turkey",
    "Czechia": "Czech Republic",
    "Viet Nam": "Vietnam",
    "Republic of Korea": "South Korea",
    "Russian Federation": "Russia",
    "United States of America": "United States",
    "United Republic of Tanzania": "Tanzania",
}

def clean(s):
    s = re.sub(r'[<>:"/\\|?*]', "-", str(s).strip())
    return re.sub(r"\s+", " ", s).strip(" .")

def txt(node, tag):
    x = node.find(tag)
    return (x.text or "").strip() if x is not None else ""

def countries(row):
    out = []
    states = row.find("states")
    if states is not None:
        for x in states.findall(".//state"):
            n = (x.text or "").strip()
            if n and n not in out:
                out.append(n)
    if not out:
        raw = txt(row, "country")
        out = [x.strip() for x in re.split(r"\s*[,;/]\s*", raw) if x.strip()]
    return out

def commons(query):
    r = requests.get(COMMONS_API, params={
        "action":"query", "generator":"search", "gsrsearch":query,
        "gsrnamespace":6, "gsrlimit":10, "prop":"imageinfo",
        "iiprop":"url|mime|extmetadata", "iiurlwidth":800, "format":"json"
    }, headers={"User-Agent":UA}, timeout=30)
    r.raise_for_status()
    for page in r.json().get("query", {}).get("pages", {}).values():
        info = page.get("imageinfo", [{}])[0]
        if info.get("mime") in ("image/jpeg","image/png","image/webp"):
            return {
                "url": info.get("thumburl") or info.get("url"),
                "title": page.get("title",""),
                "license": info.get("extmetadata",{}).get("LicenseShortName",{}).get("value",""),
                "artist": info.get("extmetadata",{}).get("Artist",{}).get("value","")
            }
    return None

def save_jpg(url, path):
    r = requests.get(url, headers={"User-Agent":UA}, timeout=60)
    r.raise_for_status()
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(r.content)))
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, "white")
        if "A" in im.getbands():
            bg.paste(im, mask=im.getchannel("A"))
        else:
            bg.paste(im)
        im = bg
    im.thumbnail((800,800), Image.Resampling.LANCZOS)
    im.save(path, "JPEG", quality=78, optimize=True)

def main():
    COUNTRY_DIR.mkdir(exist_ok=True)
    SITE_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    r = requests.get(UNESCO_XML, headers={"User-Agent":UA}, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    for e in root.iter():
        if "}" in e.tag:
            e.tag = e.tag.split("}",1)[1]

    rows = root.findall(".//row")
    if not rows:
        raise RuntimeError("UNESCO XML kaydi bulunamadi.")

    sites = []
    all_countries = []
    for row in rows:
        name = txt(row, "site")
        cs = countries(row)
        if not name or not cs:
            continue
        item = {
            "id": txt(row,"id_number") or txt(row,"id"),
            "name": name,
            "countries": cs,
            "year": txt(row,"year"),
            "category": txt(row,"category"),
            "region": txt(row,"region")
        }
        sites.append(item)
        for c in cs:
            if c not in all_countries:
                all_countries.append(c)

    sources = {}
    country_images = {}

    for c in all_countries:
        path = COUNTRY_DIR / f"{clean(c)}.jpg"
        if not path.exists():
            q = ALIASES.get(c,c) + " flag"
            info = commons(q)
            if info:
                save_jpg(info["url"], path)
                sources[str(path.relative_to(ROOT))] = info
        if path.exists():
            country_images[c] = str(path.relative_to(ROOT)).replace("\\","/")

    site_images = {}
    for s in sites:
        c = ALIASES.get(s["countries"][0], s["countries"][0])
        path = SITE_DIR / clean(f'{s["countries"][0]} - {s["name"]}.jpg')
        if not path.exists():
            info = commons(f'{s["name"]} {c} UNESCO World Heritage')
            if info:
                save_jpg(info["url"], path)
                sources[str(path.relative_to(ROOT))] = info
        site_images[s["id"]] = str(path.relative_to(ROOT)).replace("\\","/") if path.exists() else None

    data = {"source":"UNESCO World Heritage List",
            "generated_at":datetime.now(timezone.utc).isoformat(),
            "countries":{}}

    for s in sites:
        for c in s["countries"]:
            data["countries"].setdefault(c, {"image":country_images.get(c), "sites":[]})
            data["countries"][c]["sites"].append({
                "id":s["id"], "name":s["name"], "year":s["year"],
                "category":s["category"], "region":s["region"],
                "image":site_images.get(s["id"])
            })

    (DATA_DIR/"unesco.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA_DIR/"image_sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"UNESCO alanlari: {len(sites)}")
    print(f"Ulkeler: {len(all_countries)}")

if __name__ == "__main__":
    main()
