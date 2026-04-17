import requests
import rasterio
import matplotlib.pyplot as plt

# 1. URL do item no teu STAC
ITEM_URL = "http://localhost:8080/collections/LAMBDA_AMZ_TS-3/items"

# 2. Buscar items
resp = requests.get(ITEM_URL)
data = resp.json()

# 3. Pegar o primeiro item
item = data["features"][0]

# 4. Pegar o asset (GeoTIFF)
tif_url = item["assets"]["data"]["href"]

print("Baixando de:", tif_url)

# 5. Abrir direto via rasterio (stream HTTP funciona se habilitado GDAL)
with rasterio.open(tif_url) as src:
    img = src.read(1)  # primeira banda

# 6. Plotar
plt.figure(figsize=(8, 6))
plt.imshow(img, cmap="gray")
plt.title("LambdaGeo STAC Item")
plt.colorbar()
plt.show()