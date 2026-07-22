import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURACION DE BASE DE DATOS ---
BASE_DIR = Path(__file__).resolve().parent.parent
DB_USER = os.getenv('DB_USER', 'lucasjg')
DB_PASS = os.getenv('DB_PASS', 'Lucasjumbolol00_')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'practicum_db')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def normalizar(serie):
    return serie.astype(str).str.upper().str.strip() \
        .str.replace('Á', 'A').str.replace('É', 'E') \
        .str.replace('Í', 'I').str.replace('Ó', 'O') \
        .str.replace('Ú', 'U').str.replace('Ñ', 'N')

# --- LA NUEVA FUNCIÓN PRINCIPAL ---
def ejecutar_etl():
    print("Iniciando ETL: Bloque Estudiantes (MINEDUC)...")
    
    print("   Cargando dimensiones desde la base de datos...")
    dim_tiempo = pd.read_sql("SELECT id_tiempo, anio FROM dim_tiempo", engine)
    dim_tiempo['anio'] = pd.to_numeric(dim_tiempo['anio'], errors='coerce').fillna(-1).astype(int)
    dim_tiempo_anual = dim_tiempo.drop_duplicates(subset=['anio'], keep='last')
    
    dim_geografia = pd.read_sql("SELECT id_geo, provincia FROM dim_geografia WHERE canton = 'PROVINCIA_TOTAL'", engine)
    dim_geografia['provincia_norm'] = normalizar(dim_geografia['provincia'])

    print("   Procesando Registros de Fin de Anio (AMIE)...")
    ruta_mineduc = BASE_DIR / "data" / "Supercias y MINEDUC" / "2Registro-Administrativo-Historico_2009-2024-Fin.xlsx"
    df_mineduc = pd.read_excel(ruta_mineduc, engine='openpyxl')
    
    df_mineduc['anio'] = df_mineduc['Año_lectivo'].astype(str).str.extract(r'-(\d{4})')[0]
    df_mineduc['anio'] = pd.to_numeric(df_mineduc['anio'], errors='coerce').fillna(0).astype(int)
    df_mineduc['provincia_norm'] = normalizar(df_mineduc['Provincia'])
    df_mineduc['amie'] = df_mineduc['AMIE'].astype(str).str.strip()
    
    cols_metricas = ['Total_Estudiantes', 'Promovidos', 'No promovidos', 'Abandono']
    for col in cols_metricas:
        df_mineduc[col] = pd.to_numeric(df_mineduc[col], errors='coerce').fillna(0).astype(int)

    df_fact = pd.merge(df_mineduc, dim_tiempo_anual, on='anio', how='inner')
    df_fact = pd.merge(df_fact, dim_geografia, on='provincia_norm', how='inner')

    df_fact = df_fact.rename(columns={
        'amie': 'amie_codigo',
        'Nombre_Institucion': 'nombre_institucion',
        'Sostenimiento': 'sostenimiento',
        'Total_Estudiantes': 'total_estudiantes'
    })

    df_final = df_fact[['id_tiempo', 'id_geo', 'amie_codigo', 'nombre_institucion', 'sostenimiento', 'total_estudiantes']]

    print("   [INYECCION] Insertando en la tabla fact_bachilleres_mineduc...")
    try:
        # Vaciamos la tabla de forma segura manteniendo relaciones
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE fact_bachilleres_mineduc CASCADE;"))
            conn.commit()
            
        # Inyectamos
        df_final.to_sql('fact_bachilleres_mineduc', engine, if_exists='append', index=False)
        print("   Datos de MINEDUC cargados correctamente.")
    except Exception as e:
        print(f"   ❌ Fallo en la inyección. Error: {e}")

    print("FIN DEL BLOQUE MINEDUC.\n")

if __name__ == "__main__":
    ejecutar_etl()