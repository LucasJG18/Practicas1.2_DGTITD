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


def asegurar_geografia_nacional():
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO dim_geografia (id_geo, provincia, cod_provincia, canton, cod_canton)
            VALUES (0, 'NACIONAL', 0, 'NACIONAL', 0)
            ON CONFLICT (id_geo) DO NOTHING;
        """))
        conn.commit()


def procesar_pib_real(ruta_archivo):
    try:
        df = pd.read_csv(ruta_archivo, sep=',')
        df = df.rename(columns={'Período': 'fecha', 'Crecimiento Anual PIB en Porcentaje': 'variacion_pib_pct'})
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['anio'] = df['fecha'].dt.year
        return df
    except Exception as e:
        print(f"Error PIB Real: {e}"); return None

def procesar_pib_percapita(ruta_archivo):
    try:
        df = pd.read_csv(ruta_archivo, sep=',')
        df.columns = ['fecha', 'pib_percapita_nominal']
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['anio'] = df['fecha'].dt.year
        return df
    except Exception as e:
        print(f"Error PIB Per Capita: {e}"); return None

def procesar_wti(ruta_archivo):
    try:
        df = pd.read_csv(ruta_archivo, sep=',')
        df.columns = ['fecha', 'precio_petroleo_wti']
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except Exception as e:
        print(f"Error WTI: {e}"); return None

def procesar_iee(ruta_archivo):
    try:
        df = pd.read_csv(ruta_archivo, sep=',')
        df.columns = ['fecha', 'iee_global']
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except Exception as e:
        print(f"Error IEE: {e}"); return None

def procesar_vab(ruta_archivo):
    try:
        xls = pd.ExcelFile(ruta_archivo, engine='openpyxl')
        hojas_vab = [hoja for hoja in xls.sheet_names if hoja.startswith('VAB_')]
        dataframes_anuales = []
        
        for hoja in hojas_vab:
            anio_corto = hoja.split('_')[1]
            anio_real = 2000 + int(anio_corto) if int(anio_corto) < 50 else 1900 + int(anio_corto)
            df = pd.read_excel(xls, sheet_name=hoja, skiprows=10)
            df = df.dropna(axis=1, how='all')
            df = df.rename(columns={df.columns[0]: 'id_geo', df.columns[1]: 'nombre_provincia'})
            
            df['id_geo'] = df['id_geo'].astype(str).str.strip()
            df = df[df['id_geo'].str.match(r'^(?:[1-9]|1[0-9]|2[0-4])$')]
            df['id_geo'] = df['id_geo'].astype(int)
            df['anio'] = anio_real
            
            identificadores = ['id_geo', 'nombre_provincia', 'anio']
            columnas_industrias = [col for col in df.columns if col not in identificadores]
            
            df_melted = pd.melt(df, id_vars=identificadores, value_vars=columnas_industrias,
                                var_name='ciiu_sector', value_name='vab_industria_musd')
            df_melted['vab_industria_musd'] = pd.to_numeric(df_melted['vab_industria_musd'], errors='coerce')
            df_melted = df_melted.dropna(subset=['vab_industria_musd'])
            dataframes_anuales.append(df_melted)
            
        return pd.concat(dataframes_anuales, ignore_index=True)
    except Exception as e:
        print(f"Error VAB: {e}"); return None

# ==========================================
# CAPA LOAD: SEMILLAS Y ESCRITURA EN BD
# ==========================================

def cargar_dimensiones(df_vab, fechas_diarias, fechas_anuales):
    print("   Poblando dimensiones (Tiempo y Geografia)...")
    asegurar_geografia_nacional()
    
    # 1. Poblar dim_geografia con los datos unicos del VAB
    df_geo_unique = df_vab[['id_geo', 'nombre_provincia']].drop_duplicates().sort_values(by='id_geo')
    with engine.connect() as conn:
        for _, row in df_geo_unique.iterrows():
            query = text("""
                INSERT INTO dim_geografia (id_geo, provincia, cod_provincia, canton, cod_canton)
                VALUES (:id_geo, :provincia, :cod, 'PROVINCIA_TOTAL', 0)
                ON CONFLICT (id_geo) DO NOTHING;
            """)
            conn.execute(query, {"id_geo": row['id_geo'], "provincia": row['nombre_provincia'], "cod": row['id_geo']})
        conn.commit()
    print("   Dimensión geográfica actualizada.")

    # 2. Generar y poblar dim_tiempo combinando todas las fechas del dataset
    todas_las_fechas = pd.concat([fechas_diarias, fechas_anuales]).drop_duplicates()
    df_tiempo = pd.DataFrame({'fecha': todas_las_fechas})
    df_tiempo['fecha'] = pd.to_datetime(df_tiempo['fecha']).dt.date
    df_tiempo['anio'] = pd.to_datetime(df_tiempo['fecha']).dt.year
    df_tiempo['mes'] = pd.to_datetime(df_tiempo['fecha']).dt.month
    df_tiempo['trimestre'] = pd.to_datetime(df_tiempo['fecha']).dt.quarter
    
    # Subimos las fechas mapeando directamente a dim_tiempo
    df_tiempo_db = df_tiempo.drop_duplicates(subset=['fecha'])
    df_tiempo_db.to_sql('dim_tiempo', engine, if_exists='append', index=False)
    print("   Dimensión temporal actualizada.")

# --- LA NUEVA FUNCIÓN PRINCIPAL QUE LLAMARÁ EL ORQUESTADOR ---
def ejecutar_etl():
    print("Iniciando ETL: Bloque Banco Central (BCE)...")
    # Rutas
    ruta_pib_real = BASE_DIR / "data" / "BCE" / "crecimiento-anual-pib.csv"
    ruta_pib_nominal = BASE_DIR / "data" / "BCE" / "pib-per-cpita-nominal.csv"
    ruta_wti = BASE_DIR / "data" / "BCE" / "precio-petrleo-wti.csv"
    ruta_iee = BASE_DIR / "data" / "BCE" / "figura-1-ndice-de-expect.csv"
    ruta_vab = BASE_DIR / "data" / "BCE" / "CtasProv2007-2020.xlsx"
    
    # Extraccion y Transformacion
    df_real = procesar_pib_real(ruta_pib_real)
    df_nominal = procesar_pib_percapita(ruta_pib_nominal)
    df_wti = procesar_wti(ruta_wti)
    df_iee = procesar_iee(ruta_iee)
    df_vab_total = procesar_vab(ruta_vab)
    
    if all(df is not None for df in [df_real, df_nominal, df_wti, df_iee, df_vab_total]):
        # Uniones logicas en memoria
        df_macro_nacional = pd.merge(df_real, df_nominal, on=['fecha', 'anio'], how='outer')
        df_diarios_total = pd.merge(df_wti, df_iee, on='fecha', how='outer')
        
        # Carga de Dimensiones Transversales
        cargar_dimensiones(df_vab_total, df_diarios_total['fecha'], df_macro_nacional['fecha'])
        
        # --- OBTENER IDs DE TIEMPO DESDE LA BD ---
        df_dim_tiempo = pd.read_sql("SELECT id_tiempo, fecha FROM dim_tiempo", engine)
        df_dim_tiempo['fecha'] = pd.to_datetime(df_dim_tiempo['fecha'])
        
        print("   Volcando datos en tablas de hechos...")
        
        # 1. Carga de Indicadores Diarios
        df_diarios_final = pd.merge(df_diarios_total, df_dim_tiempo, on='fecha', how='inner')
        df_diarios_final = df_diarios_final[['id_tiempo', 'precio_petroleo_wti', 'iee_global']]
        # Vaciamos la tabla de forma segura antes de insertar
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE fact_indicadores_diarios CASCADE;"))
            conn.commit()
        df_diarios_final.to_sql('fact_indicadores_diarios', engine, if_exists='append', index=False)
        print("   fact_indicadores_diarios cargada correctamente.")
        
        # 2. Carga de Hechos Macro Nacionales y Regionales (VAB)
        df_macro_final = pd.merge(df_macro_nacional, df_dim_tiempo, on='fecha', how='inner')
        df_macro_final['id_geo'] = 0  # El registro comodin nacional
        df_macro_final = df_macro_final[['id_tiempo', 'id_geo', 'pib_percapita_nominal', 'variacion_pib_pct']]
        
        df_vab_total['fecha'] = pd.to_datetime(df_vab_total['anio'].astype(str) + '-01-01')
        df_vab_final = pd.merge(df_vab_total, df_dim_tiempo, on='fecha', how='inner') 
        if 'id_geo_x' in df_vab_final.columns:
            df_vab_final = df_vab_final.rename(columns={'id_geo_x': 'id_geo'})
        df_vab_final = df_vab_final[['id_tiempo', 'id_geo', 'ciiu_sector', 'vab_industria_musd']]
        
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE fact_macro_anual CASCADE;"))
            conn.commit()
            
        df_macro_final.to_sql('fact_macro_anual', engine, if_exists='append', index=False)
        df_vab_final.to_sql('fact_macro_anual', engine, if_exists='append', index=False)
        print("   fact_macro_anual cargada correctamente.")
        print("FIN DEL BLOQUE BCE.\n")

if __name__ == "__main__":
    ejecutar_etl()