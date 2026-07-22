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


def ejecutar_etl():
    print("Iniciando Pipeline ETL: Bloque Supercias (Semana 3)...\n")
    
    print("Cargando dimensiones desde la base de datos...")
    
    # TRUCO ANTI-CLONES: Sacamos solo un ID de tiempo por anio (el ultimo)
    dim_tiempo = pd.read_sql("SELECT id_tiempo, anio FROM dim_tiempo", engine)
    dim_tiempo['anio'] = pd.to_numeric(dim_tiempo['anio'], errors='coerce').fillna(-1).astype(int)
    dim_tiempo_anual = dim_tiempo.drop_duplicates(subset=['anio'], keep='last')
    
    dim_geografia = pd.read_sql("SELECT id_geo, provincia FROM dim_geografia WHERE canton = 'PROVINCIA_TOTAL'", engine)
    dim_geografia['provincia_norm'] = normalizar(dim_geografia['provincia'])

    # 2. PROCESAMOS EL RANKING FINANCIERO (CSV)
    print("\n[1/2] Procesando el Ranking de Supercias...")
    df_ranking = pd.read_csv(BASE_DIR / "data" / "Supercias y MINEDUC" / "bi_ranking.csv", 
                             sep=',', encoding='latin1', on_bad_lines='skip', low_memory=False)
    df_ranking.columns = [str(c).strip() for c in df_ranking.columns]
    
    cols_ranking = ['anio', 'expediente', 'ingresos_ventas', 'activos', 'ciiu_n6']
    df_ranking = df_ranking[cols_ranking].copy()
    
    df_ranking['expediente'] = df_ranking['expediente'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df_ranking['ingresos'] = pd.to_numeric(df_ranking['ingresos_ventas'], errors='coerce').fillna(0)
    df_ranking['activos'] = pd.to_numeric(df_ranking['activos'], errors='coerce').fillna(0)
    df_ranking['ciiu_codigo'] = df_ranking['ciiu_n6'].astype(str).str.strip()
    df_ranking['anio'] = pd.to_numeric(df_ranking['anio'], errors='coerce').fillna(0).astype(int)

    # 3. PROCESAMOS EL DIRECTORIO DE COMPANIAS (Excel)
    print("[2/2] Procesando el Directorio de Companias...")
    df_directorio = pd.read_excel(BASE_DIR / "data" / "Supercias y MINEDUC" / "directorio_companias.xlsx", skiprows=4, engine='openpyxl')
    df_directorio.columns = [str(c).upper().strip().replace('Ó', 'O') for c in df_directorio.columns]
    
    cols_dir = ['EXPEDIENTE', 'RUC', 'NOMBRE', 'SITUACION LEGAL', 'PROVINCIA']
    df_directorio = df_directorio[cols_dir].copy()
    
    df_directorio['EXPEDIENTE'] = df_directorio['EXPEDIENTE'].astype(str).str.strip().str.replace('.0', '', regex=False)
    
    # BLINDAJE CONTRA RUCs NULOS (Eliminacion de empresas fantasma)
    df_directorio['RUC'] = df_directorio['RUC'].astype(str).str.strip().str.replace('.0', '', regex=False)
    df_directorio['RUC'] = df_directorio['RUC'].replace({'nan': pd.NA, 'None': pd.NA, '': pd.NA})
    df_directorio = df_directorio.dropna(subset=['RUC'])
    
    df_directorio['PROVINCIA_NORM'] = normalizar(df_directorio['PROVINCIA'])

    # 4. CRUCE MAESTRO
    print("\nCruzando el Ranking con el Directorio...")
    df_empresas = pd.merge(df_ranking, df_directorio, left_on='expediente', right_on='EXPEDIENTE', how='inner')
    
    print("Cruzando con dimensiones de PostgreSQL...")
    # Cruce de tiempo corregido
    df_empresas = pd.merge(df_empresas, dim_tiempo_anual, on=['anio'], how='inner')
    
    # Cruce geografico
    df_empresas = pd.merge(df_empresas, dim_geografia, left_on='PROVINCIA_NORM', right_on='provincia_norm', how='inner')

    # 5. PREPARACION FINAL E INYECCION
    df_empresas = df_empresas.rename(columns={
        'RUC': 'ruc',
        'NOMBRE': 'nombre_empresa',
        'SITUACION LEGAL': 'situacion_legal'
    })
    
    df_final = df_empresas[['id_tiempo', 'id_geo', 'ruc', 'nombre_empresa', 'situacion_legal', 'ingresos', 'activos', 'ciiu_codigo']]
    
    print(f"\nTotal real de empresas listas para inyectar: {len(df_final)}")
    print("\n[INYECCION] Insertando en la tabla fact_empresas_supercias...")
    
    try:
        # TRUCO SENIOR: Vaciamos la tabla vieja manteniendo el DDL y las FKs
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE fact_empresas_supercias CASCADE;"))
            conn.commit()
            
        df_final.to_sql('fact_empresas_supercias', engine, if_exists='append', index=False)
        print("   Datos cargados correctamente en la base de datos.")
    except Exception as e:
        print(f"   ❌ Fallo en la inyeccion. Error: {e}")

    print("\nFIN DEL BLOQUE SUPERCIAS.")


if __name__ == "__main__":
    ejecutar_etl()