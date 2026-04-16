#!/bin/bash
set -e

echo "🔍 Testing BDC-STAC Local Stack..."

# 1. Health dos containers
echo -n "🐳 Containers: "
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -q "healthy" && echo "✅ OK" || echo "❌ FAIL"

# 2. API STAC
echo -n "🌐 STAC API: "
curl -sf http://localhost:8080/ > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# 3. Coleções
echo -n "📚 Collections: "
COLS=$(curl -s http://localhost:8080/collections | jq -r '.collections | length')
[ "$COLS" -ge 1 ] && echo "✅ $COLS collection(s)" || echo "⚠️ Empty (run loader)"

# 4. Itens
echo -n "🔎 Items: "
ITEMS=$(curl -s "http://localhost:8080/search?collections=LAMBDA_AMZ_TS" | jq -r '.features | length')
[ "$ITEMS" -ge 1 ] && echo "✅ $ITEMS item(s)" || echo "⚠️ Empty (run loader)"

echo "🎉 Test completed!"