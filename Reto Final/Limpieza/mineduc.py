import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURACION DE BASE DE DATOS ---
DB_USER = 'lucasjg'
DB_PASS = 'Lucasjumbolol00_'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'practicum_db'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

def normalizar(serie):
    # Funcion para limpiar textos, espacios y tildes
    return serie.astype(str).str.upper().str.strip() \
        .str.replace('Á', 'A').str.replace('É', 'E') \
        .str.replace('Í', 'I').str.replace('Ó', 'O') \
        .str.replace('Ú', 'U').str.replace('Ñ', 'N')

if __name__ == "__main__":
    print("Iniciando Pipeline ETL: Bloque MINEDUC (Semana 3)...\n")
    
    # 1. CARGAMOS DIMENSIONES
    print("Cargando dimensiones desde la base de datos...")
    dim_tiempo = pd.read_sql("SELECT id_tiempo, anio FROM dim_tiempo", engine)
    dim_tiempo['anio'] = pd.to_numeric(dim_tiempo['anio'], errors='coerce').fillna(-1).astype(int)
    dim_tiempo_anual = dim_tiempo.drop_duplicates(subset=['anio'], keep='last')
    
    dim_geografia = pd.read_sql("SELECT id_geo, provincia FROM dim_geografia WHERE canton = 'PROVINCIA_TOTAL'", engine)
    dim_geografia['provincia_norm'] = normalizar(dim_geografia['provincia'])

    # 2. PROCESAMOS EL ARCHIVO DEL MINEDUC
    print("\nProcesando Registros de Fin de Anio (AMIE)...")
    ruta_mineduc = "../data/Supercias y MINEDUC/2Registro-Administrativo-Historico_2009-2024-Fin.xlsx"
    
    # Lectura directa del archivo
    df_mineduc = pd.read_excel(ruta_mineduc, engine='openpyxl')
    
    # LIMPIEZA
    # Extraccion del anio de finalizacion
    df_mineduc['anio'] = df_mineduc['Año_lectivo'].astype(str).str.extract(r'-(\d{4})')[0]
    df_mineduc['anio'] = pd.to_numeric(df_mineduc['anio'], errors='coerce').fillna(0).astype(int)
    
    df_mineduc['provincia_norm'] = normalizar(df_mineduc['Provincia'])
    df_mineduc['amie'] = df_mineduc['AMIE'].astype(str).str.strip()
    
    # Aseguramos que las metricas sean numeros
    cols_metricas = ['Total_Estudiantes', 'Promovidos', 'No promovidos', 'Abandono']
    for col in cols_metricas:
        df_mineduc[col] = pd.to_numeric(df_mineduc[col], errors='coerce').fillna(0).astype(int)

    # 3. CRUCES CON DIMENSIONES
    print("Cruzando datos con dimensiones en PostgreSQL...")
    df_fact = pd.merge(df_mineduc, dim_tiempo_anual, on='anio', how='inner')
    df_fact = pd.merge(df_fact, dim_geografia, on='provincia_norm', how='inner')

    print(f"\nTotal de registros AMIE listos: {len(df_fact)}")

    # 4. PREPARACION FINAL E INYECCION
    print("\nAjustando columnas al esquema de la base de datos...")
    
    # Renombramos las columnas
    df_fact = df_fact.rename(columns={
        'amie': 'amie_codigo',
        'Nombre_Institucion': 'nombre_institucion',
        'Sostenimiento': 'sostenimiento',
        'Total_Estudiantes': 'total_estudiantes'
    })

    # Seleccion de columnas para la tabla de hechos
    df_final = df_fact[['id_tiempo', 'id_geo', 'amie_codigo', 'nombre_institucion', 'sostenimiento', 'total_estudiantes']]

    print("[INYECCION] Insertando en la tabla fact_bachilleres_mineduc...")
    try:
        df_final.to_sql('fact_bachilleres_mineduc', engine, if_exists='append', index=False)
        print("   Datos de MINEDUC inyectados con exito.")
    except Exception as e:
        print(f"   Fallo en la inyeccion. Error: {e}")

    print("\nFIN DEL BLOQUE MINEDUC Y DEL PIPELINE ETL.")