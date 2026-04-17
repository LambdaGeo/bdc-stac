#!/usr/bin/env python3
"""
generate_bdc_fixture.py — LambdaGeo / UFMA — 2026

Gera JSON compatível com bdc-catalog a partir de GeoTIFFs locais.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

import rasterio
from rasterio.warp import transform_bounds


# ================= CONFIG =================
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "./fixtures/LAMBDA_AMZ_TS_bdc.json"))
ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "http://localhost:8081/assets")
COLLECTION_ID = os.getenv("COLLECTION_ID", "LAMBDA_AMZ_TS")


# ================= HELPERS =================
def compute_bdc_multihash(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"1220{h.hexdigest()}"


def extract_bbox_and_footprint(geotiff: Path):
    with rasterio.open(geotiff) as src:
        bounds = src.bounds
        epsg = src.crs.to_epsg() if src.crs else 4326

        if epsg and epsg != 4326:
            bounds = transform_bounds(src.crs, "EPSG:4326", *bounds)

        bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]

        footprint = {
            "type": "Polygon",
            "coordinates": [[
                [bounds.left, bounds.bottom],
                [bounds.right, bounds.bottom],
                [bounds.right, bounds.top],
                [bounds.left, bounds.top],
                [bounds.left, bounds.bottom],
            ]]
        }

        return bbox, footprint


def extract_year(filename: str):
    match = re.search(r"_(\d{4})\.tif$", filename)
    return match.group(1) if match else None


# ================= BANDS =================
def create_bands():
    return [
        {
            "name": "B1",
            "common_name": "blue",
            "data_type": "uint16",
            "nodata": 0,
            "scale": 0.0001,
            "mime_type": "image/tiff; application=geotiff"
        },
        {
            "name": "B2",
            "common_name": "green",
            "data_type": "uint16",
            "nodata": 0,
            "scale": 0.0001,
            "mime_type": "image/tiff; application=geotiff"
        },
        {
            "name": "B3",
            "common_name": "red",
            "data_type": "uint16",
            "nodata": 0,
            "scale": 0.0001,
            "mime_type": "image/tiff; application=geotiff"
        },
        {
            "name": "B4",
            "common_name": "nir",
            "data_type": "uint16",
            "nodata": 0,
            "scale": 0.0001,
            "mime_type": "image/tiff; application=geotiff"
        }
    ]


# ================= COLLECTION =================
def create_collection():
    return {
        "name": COLLECTION_ID,
        "title": "LambdaGeo Amazon Time Series",
        "description": "Serie temporal de imagens LambdaGeo para a regiao amazonica (1997-2003).",

        "collection_type": "collection",

        "is_available": True,
        "is_public": True,

        "version": 1,
        "category": "eo",

        "start_date": "1997-01-01",
        "end_date": "2003-12-31",

        "spatial_extent": "SRID=4326;POLYGON((-64.6 -11.0, -62.7 -11.0, -62.7 -9.2, -64.6 -9.2, -64.6 -11.0))",

        "bands": create_bands(),

        "items": []
    }


# ================= ITEM =================
def create_item(geotiff: Path):
    item_name = geotiff.stem

    year = extract_year(geotiff.name)
    if year is None:
        print(f"⚠️ Ignorando (sem ano): {geotiff.name}")
        return None

    bbox, footprint = extract_bbox_and_footprint(geotiff)

    file_size = geotiff.stat().st_size
    checksum = compute_bdc_multihash(geotiff)
    now = datetime.now(timezone.utc).isoformat()

    return {
        "name": item_name,
        "start_date": f"{year}-06-15",
        "end_date": f"{year}-06-15",
        "srid": 4326,

        "footprint": footprint,

        # 🔥 BDC quer geometria, não lista
        "bbox": footprint,

        "assets": {
            "data": {
                "href": f"{ASSET_BASE_URL}/{geotiff.name}",
                "type": "image/tiff; application=geotiff",
                "bdc:size": file_size,
                "checksum:multihash": checksum,
                "roles": ["data"],
                "created": now,
                "updated": now
            }
        }
    }


# ================= MAIN =================
def main():
    print("🚀 Generating BDC fixture")

    if not DATA_DIR.exists():
        print("❌ Data dir not found")
        return False

    collection = create_collection()

    tiffs = sorted(DATA_DIR.glob("*.tif"))
    print(f"🔎 Found {len(tiffs)} files")

    for tif in tiffs:
        print(f"📄 Processing {tif.name}")

        try:
            item = create_item(tif)
            if item:
                collection["items"].append(item)
                print(f"  ✅ Added {item['name']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(collection, f, indent=2)

    print("\n✨ Done!")
    print(f"📦 Collection: {collection['name']}")
    print(f"📊 Items: {len(collection['items'])}")

    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)