#!/usr/bin/env python3
"""
load_bdc_complete.py — Gera fixture BDC + carrega via CLI em um passo.
"""
import subprocess
import sys
from pathlib import Path

def main():
    # 1. Gerar fixture
    print("🔧 Generating BDC fixture...")
    result = subprocess.run([sys.executable, "scripts/generate_bdc_fixture.py"])
    if result.returncode != 0:
        print("❌ Failed to generate fixture")
        return False
    
    # 2. Carregar via CLI
    print("\n📦 Loading into database...")
    fixture = Path("fixtures/LAMBDA_AMZ_TS_bdc.json")
    result = subprocess.run([
        "bdc-catalog", "load-data",
        "--ifile", str(fixture),
        "-v"
    ], env={**dict(os.environ), "SQLALCHEMY_DATABASE_URI": os.getenv("SQLALCHEMY_DATABASE_URI")})
    
    if result.returncode == 0:
        print("\n✨ Load completed successfully!")
        return True
    else:
        print("\n❌ Load failed")
        return False

if __name__ == "__main__":
    import os
    success = main()
    sys.exit(0 if success else 1)