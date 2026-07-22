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

def transformar_fecha_enemdu(txt_fecha):
    meses_map = {
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
    }
    try:
        partes = str(txt_fecha).lower().split('-')
        if len(partes) == 2:
            mes_txt = partes[0].strip()
            anio_txt = partes[1].strip()
            mes = meses_map.get(mes_txt)
            anio = int(f"20{anio_txt}") if len(anio_txt) == 2 else int(anio_txt)
            return pd.Series([anio, mes])
    except:
        pass
    return pd.Series([None, None])

def normalizar(serie):
    return serie.astype(str).str.upper().str.strip() \
        .str.replace('Á', 'A').str.replace('É', 'E') \
        .str.replace('Í', 'I').str.replace('Ó', 'O') \
        .str.replace('Ú', 'U').str.replace('Ñ', 'N')

# --- LA NUEVA FUNCIÓN PRINCIPAL ---
def ejecutar_etl():
    print("Iniciando ETL: Bloque Empleo e Industria (INEC)...")
    
    print("   Cargando dimensiones desde la base de datos...")
    dim_tiempo = pd.read_sql("SELECT id_tiempo, anio, mes FROM dim_tiempo", engine)
    dim_geografia = pd.read_sql("SELECT id_geo, provincia FROM dim_geografia WHERE canton = 'PROVINCIA_TOTAL'", engine)
    
    dim_tiempo['anio'] = pd.to_numeric(dim_tiempo['anio'], errors='coerce').fillna(-1).astype(int)
    dim_tiempo['mes'] = pd.to_numeric(dim_tiempo['mes'], errors='coerce').fillna(-1).astype(int)
    dim_geografia['provincia_norm'] = normalizar(dim_geografia['provincia'])

    # =========================================================================
    # 1. ENEMDU
    # =========================================================================
    print("   [1/2] Procesando tasas de la ENEMDU...")
    ruta_enemdu = BASE_DIR / "data" / "INEC" / "2. Tasas.csv"
    df_enemdu = pd.read_csv(ruta_enemdu, skiprows=2, sep=';', usecols=[1, 2, 3, 4, 5], 
                            names=['fecha', 'indicador', 'nacional', 'urbana', 'rural'], encoding='latin1')
    
    df_enemdu = df_enemdu.dropna(subset=['fecha', 'indicador'])
    df_enemdu = df_enemdu[~df_enemdu['fecha'].astype(str).str.contains('Periodo', case=False, na=False)]
    
    df_empleo_long = df_enemdu.melt(id_vars=['fecha', 'indicador'], value_vars=['nacional', 'urbana', 'rural'], var_name='area', value_name='tasa_pct')
    
    df_empleo_long['tasa_pct'] = df_empleo_long['tasa_pct'].astype(str).str.replace(',', '.').str.strip()
    df_empleo_long['tasa_pct'] = pd.to_numeric(df_empleo_long['tasa_pct'], errors='coerce')
    df_empleo_long = df_empleo_long.dropna(subset=['tasa_pct'])
    
    df_empleo_long[['anio', 'mes']] = df_empleo_long['fecha'].apply(transformar_fecha_enemdu)
    df_empleo_long = df_empleo_long.dropna(subset=['anio', 'mes'])
    df_empleo_long['anio'] = df_empleo_long['anio'].astype(int)
    df_empleo_long['mes'] = df_empleo_long['mes'].astype(int)
    
    df_fact_empleo = pd.merge(df_empleo_long, dim_tiempo, on=['anio', 'mes'], how='inner')
    df_fact_empleo = df_fact_empleo[['id_tiempo', 'indicador', 'area', 'tasa_pct']]

    # =========================================================================
    # 2. CENSO 2022
    # =========================================================================
    print("   [2/2] Procesando Censo 2022 (Actividad Economica)...")
    ruta_censo = BASE_DIR / "data" / "INEC" / "5.1.csv"
    
    df_headers = pd.read_csv(ruta_censo, encoding='latin1', skiprows=9, nrows=1, header=None)
    industrias = df_headers.iloc[0, 6:].tolist()
    
    df_censo = pd.read_csv(ruta_censo, encoding='latin1', skiprows=11, header=None)
    cols_base = ['vacio', 'provincia', 'canton', 'sexo', 'grupo_edad', 'total_ocupados_grupo']
    df_censo.columns = cols_base + industrias
    df_censo = df_censo.drop(columns=['vacio'])
    
    df_censo = df_censo[~df_censo['canton'].astype(str).str.contains('Total', case=False, na=False)]
    df_censo = df_censo[~df_censo['provincia'].astype(str).str.contains('Nacional', case=False, na=False)]
    
    df_censo_long = df_censo.melt(id_vars=['provincia', 'sexo', 'grupo_edad'], value_vars=industrias, var_name='ciiu_codigo', value_name='personas_ocupadas')
    df_censo_long['personas_ocupadas'] = df_censo_long['personas_ocupadas'].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    
    df_censo_prov = df_censo_long.groupby(['provincia', 'sexo', 'grupo_edad', 'ciiu_codigo'])['personas_ocupadas'].sum().reset_index()
    df_censo_prov['provincia_norm'] = normalizar(df_censo_prov['provincia'])
    
    df_fact_censo = pd.merge(df_censo_prov, dim_geografia, on=['provincia_norm'], how='inner')
    df_fact_censo = df_fact_censo[['id_geo', 'sexo', 'grupo_edad', 'personas_ocupadas', 'ciiu_codigo']]

    # =========================================================================
    # INYECCION CON TRUNCATE SEGURO
    # =========================================================================
    print("   [INYECCION] Insertando datos en PostgreSQL...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE fact_empleo_enemdu CASCADE;"))
        conn.execute(text("TRUNCATE TABLE fact_censo_actividad CASCADE;"))
        conn.commit()

    if len(df_fact_empleo) > 0:
        df_fact_empleo.to_sql('fact_empleo_enemdu', engine, if_exists='append', index=False)
        print("   Datos de ENEMDU cargados correctamente.")
    if len(df_fact_censo) > 0:
        df_fact_censo.to_sql('fact_censo_actividad', engine, if_exists='append', index=False)
        print("   Datos del censo 2022 cargados correctamente.")
    print("FIN DEL BLOQUE INEC.\n")

if __name__ == "__main__":
    ejecutar_etl()