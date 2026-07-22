import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN ---
DB_USER = 'lucasjg'
DB_PASS = 'Lucasjumbolol00_'  # <--- ¡Pon tu clave real de Postgres!
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@localhost:5432/practicum_db')
BASE_DIR = Path(__file__).resolve().parent.parent

print("\n" + "="*50)
print(" 📑 LÍNEAS EN CRUDO - ENEMDU (2. Tasas.csv)")
print("="*50)
# Leemos las primeras 10 líneas exactamente como están escritas en el disco
ruta_tasas = BASE_DIR / "data" / "INEC" / "2. Tasas.csv"
with open(ruta_tasas, "r", encoding="latin1") as f:
    for i in range(12):
        print(f"Línea {i+1}: {f.readline().strip()}")

print("\n" + "="*50)
print(" 🔌 CONTENIDO REAL DE DIM_GEOGRAFIA EN BD")
print("="*50)
with engine.connect() as conn:
    df_geo = pd.read_sql(text("SELECT * FROM dim_geografia LIMIT 10"), conn)
print(df_geo.to_string())

print("\n" + "="*50)
print(" 🔌 CONTENIDO REAL DE DIM_TIEMPO EN BD")
print("="*50)
with engine.connect() as conn:
    df_tiempo = pd.read_sql(text("SELECT * FROM dim_tiempo LIMIT 10"), conn)
print(df_tiempo.to_string())