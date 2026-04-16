#!/usr/bin/env python3
"""
generate_bdc_fixture.py — LambdaGeo / UFMA — 2026
Gera arquivo JSON no formato BDC-Catalog a partir de GeoTIFFs locais.
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

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "./fixtures/LAMBDA_AMZ_TS_bdc.json"))
ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "http://localhost:8081/assets")
COLLECTION_ID = os.getenv("COLLECTION_ID", "LAMBDA_AMZ_TS")


def compute_bdc_multihash(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"1220{h.hexdigest()}"


def extract_bbox_4326(geotiff: Path):
    with rasterio.open(geotiff) as src:
        bounds = src.bounds
        epsg = src.crs.to_epsg() if src.crs else 4326
        if epsg and epsg != 4326:
            bounds = transform_bounds(src.crs, "EPSG:4326", *bounds)
        bbox_list = [bounds.left, bounds.bottom, bounds.right, bounds.top]
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
        return bbox_list, footprint


def extract_year_from_filename(filename: str) -> str:
    match = re.search(r"_(\d{4})\.tif$", filename)
    return match.group(1) if match else "1997"


def create_bdc_collection():
    return {
        "name": COLLECTION_ID,
        "title": "LambdaGeo Amazon Time Series",
        "description": "Serie temporal de imagens LambdaGeo para a regiao amazonica (1997-2003).",
        "is_available": True,
        "version": "1",
        "category": "eo",
        "license": "proprietary",

        "extent": {
            "temporal": [["1997-01-01", "2003-12-31"]],
            "spatial": [[-64.6, -11.0, -62.7, -9.2]]
        },

        "bands": [...],
        "items": []
    }


def create_bdc_item(geotiff: Path, collection_name: str):
    item_name = geotiff.stem
    year = extract_year_from_filename(geotiff.name)
    bbox, footprint = extract_bbox_4326(geotiff)
    file_size = geotiff.stat().st_size
    checksum = compute_bdc_multihash(geotiff)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    
    return {
        "name": item_name,
        "start_date": f"{year}-06-15T00:00:00",
        "end_date": f"{year}-06-15T00:00:00",
        "srid": 4326,
        "footprint": footprint,
        "bbox": bbox,
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


def main():
    print(f"Generating BDC-Catalog fixture")
    print(f"Input: {DATA_DIR.resolve()}")
    print(f"Output: {OUTPUT_PATH.resolve()}")
    
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        return False
    
    collection = create_bdc_collection()
    tiffs = sorted(DATA_DIR.glob("*.tif"))
    print(f"Found {len(tiffs)} GeoTIFF(s)")
    
    for geotiff in tiffs:
        print(f"Processing {geotiff.name}...")
        try:
            item = create_bdc_item(geotiff, COLLECTION_ID)
            collection["items"].append(item)
            print(f"  Added {item['name']}")
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(collection, f, indent=2)
    
    print(f"Fixture generated: {OUTPUT_PATH}")
    print(f"Collection: {collection['name']}, Items: {len(collection['items'])}")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)