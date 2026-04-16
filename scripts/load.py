#!/usr/bin/env python3
"""
Gera um catálogo STAC local a partir de GeoTIFFs
Independente do bdc-catalog
"""

from pathlib import Path
import rasterio
from datetime import datetime
import pystac

DATA_DIR = Path("./data")
OUTPUT_DIR = Path("./stac_catalog")

COLLECTION_ID = "meu_datacube"
COLLECTION_DESC = "Coleção gerada localmente a partir de GeoTIFFs"

def create_collection():
    extent = pystac.Extent(
        spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
        temporal=pystac.TemporalExtent([[None, None]])
    )

    collection = pystac.Collection(
        id=COLLECTION_ID,
        description=COLLECTION_DESC,
        extent=extent,
        license="proprietary"
    )

    return collection

def create_item(geotiff: Path):
    item_id = geotiff.stem

    with rasterio.open(geotiff) as src:
        bounds = src.bounds
        width = src.width
        height = src.height

    bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]

    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [bounds.left, bounds.bottom],
            [bounds.right, bounds.bottom],
            [bounds.right, bounds.top],
            [bounds.left, bounds.top],
            [bounds.left, bounds.bottom],
        ]]
    }

    # tenta extrair ano do nome
    try:
        year = int(item_id.split("_")[-1])
        dt = datetime(year, 6, 15)
    except:
        dt = datetime.utcnow()

    item = pystac.Item(
        id=item_id,
        geometry=geometry,
        bbox=bbox,
        datetime=dt,
        properties={}
    )

    item.add_asset(
        "data",
        pystac.Asset(
            href=str(geotiff.resolve()),
            media_type=pystac.MediaType.GEOTIFF,
            roles=["data"]
        )
    )

    return item

def main():
    catalog = pystac.Catalog(
        id="catalogo_local",
        description="Catálogo STAC local"
    )

    collection = create_collection()

    for tif in sorted(DATA_DIR.glob("*.tif")):
        item = create_item(tif)
        collection.add_item(item)
        print(f"✅ Item criado: {item.id}")

    catalog.add_child(collection)

    catalog.normalize_and_save(
        root_href=str(OUTPUT_DIR),
        catalog_type=pystac.CatalogType.SELF_CONTAINED
    )

    print("\n✨ Catálogo STAC gerado em:", OUTPUT_DIR)

if __name__ == "__main__":
    main()