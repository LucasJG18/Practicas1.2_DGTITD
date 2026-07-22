from pathlib import Path

from prefect import flow, task

# Importaciones adaptadas a la estructura formal del proyecto
from datos_macroentorno import procesador_rpa_masivo
from ETL import bce
from ETL import inec
from ETL import mineduc
from ETL import supercias

BASE_DIR = Path(__file__).resolve().parent
CARPETA_RPA = BASE_DIR / "datos_macroentorno"
ARCHIVOS_RPA_CANDIDATOS = ("tab_consolidado_supercias.sql", "tab_consolidado_export.sql")


@task(name="1. Sensor RPA", retries=3, retry_delay_seconds=5)
def detectar_archivo_rpa():
    """Busca un archivo de entrada RPA en la carpeta designada."""
    print(f"Revisando la carpeta de RPA: {CARPETA_RPA}")

    for archivo in ARCHIVOS_RPA_CANDIDATOS:
        ruta_completa = CARPETA_RPA / archivo
        if ruta_completa.exists():
            print(f"Archivo detectado: {archivo}")
            return str(ruta_completa)

    raise FileNotFoundError(
        f"No se encontró ningún archivo RPA esperado en {CARPETA_RPA}. "
        f"Se buscó: {', '.join(ARCHIVOS_RPA_CANDIDATOS)}"
    )


@task(name="2. Extracción y limpieza RPA")
def procesar_rpa(ruta_archivo):
    """Procesa el dump de Oracle y carga los datos de Supercias."""
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo RPA no existe: {ruta}")

    print(f"Procesando dump RPA: {ruta.name}")
    procesador_rpa_masivo.procesar_dump_gigante(str(ruta), tamaño_lote=50000)

    print("Aplicando limpieza de Supercias y cargando en la base de datos...")
    supercias.ejecutar_etl()

    return f"RPA procesado: {ruta.name}"


@task(name="3. Limpieza de fuentes públicas")
def limpiar_fuentes_estaticas():
    """Ejecuta la carga de las fuentes públicas BCE, INEC y MINEDUC."""
    print("Procesando datos del Banco Central...")
    bce.ejecutar_etl()

    print("Procesando datos de empleo (INEC)...")
    inec.ejecutar_etl()

    print("Procesando datos de estudiantes (MINEDUC)...")
    mineduc.ejecutar_etl()

    return "Fuentes públicas cargadas"


@task(name="4. Actualización de vistas gold")
def refrescar_business_intelligence():
    """Marca la finalización del flujo para BI."""
    print("Actualizando vistas Gold en PostgreSQL...")
    print("BI lista para consultar.")
    return "BI actualizada"


@flow(name="Pipeline UTPL - Macroentorno Ecuador")
def pipeline_principal():
    print("--- INICIANDO PIPELINE DE DATOS DGTITD-UTPL ---")

    try:
        ruta_rpa = detectar_archivo_rpa()
        resultado_publicas = limpiar_fuentes_estaticas()
        resultado_rpa = procesar_rpa(ruta_rpa)
        resultado_bi = refrescar_business_intelligence()

        print("Resumen del pipeline:")
        print(f" - {resultado_publicas}")
        print(f" - {resultado_rpa}")
        print(f" - {resultado_bi}")
        print("--- PIPELINE EJECUTADO CON ÉXITO ---")

        return {
            "estado": "exitoso",
            "ruta_rpa": ruta_rpa,
            "resultado_publicas": resultado_publicas,
            "resultado_rpa": resultado_rpa,
            "resultado_bi": resultado_bi,
        }
    except Exception as exc:
        print(f"Pipeline detenido por error: {exc}")
        raise


if __name__ == "__main__":
    pipeline_principal()
