# Proyecto de Data Engineering - Macroentorno Ecuador

## Descripción general
Este repositorio implementa un pipeline ETL orientado a la integración de fuentes de datos macroeconómicos, sociales y empresariales del Ecuador en una base de datos PostgreSQL. El flujo permite consolidar información proveniente del Banco Central del Ecuador (BCE), INEC, MINEDUC y datos de Supercias procesados a partir de un dump de Oracle, con el fin de apoyar análisis de negocio y generación de vistas analíticas de alto nivel.

## Objetivo del proyecto
El proyecto busca transformar datos crudos en información estructurada y utilizable para análisis, mediante la implementación de procesos de extracción, limpieza, transformación y carga (ETL). Entre sus objetivos principales se encuentran:
- centralizar información dispersa en múltiples fuentes,
- estandarizar la preparación de datos para su carga,
- facilitar el acceso a datos analíticos a través de una base relacional,
- habilitar la generación de vistas gold para consultas de negocio.

## Arquitectura del flujo
La solución está organizada en tres capas principales:
- ETL: módulos encargados de la extracción, transformación y carga de cada fuente de datos.
- datos_macroentorno: archivos y componentes asociados al procesamiento del flujo de RPA/Supercias.
- DB: definiciones del esquema SQL y las vistas gold del modelo analítico.

### Componentes principales
- ETL/bce.py: carga de indicadores macroeconómicos del BCE.
- ETL/inec.py: carga de datos de empleo y actividad económica.
- ETL/mineduc.py: carga de datos educativos y de estudiantes.
- ETL/supercias.py: limpieza y carga de datos derivados de Supercias.
- pipeline.py: orquestador principal del flujo ETL.
- datos_macroentorno/procesador_rpa_masivo.py: procesamiento del dump SQL de RPA.

## Requisitos
- Python 3.10 o superior
- PostgreSQL en ejecución
- Dependencias de Python: pandas, sqlalchemy, prefect y psycopg2
- Docker opcional para levantar la base de datos localmente

## Configuración de la base de datos
El proyecto asume una instancia de PostgreSQL con los siguientes valores por defecto:
- usuario: lucasjg
- contraseña: Lucasjumbolol00_
- host: localhost
- puerto: 5432
- base: practicum_db

Estas opciones pueden sobrescribirse mediante variables de entorno:
- DB_USER
- DB_PASS
- DB_HOST
- DB_PORT
- DB_NAME

## Ejecución del pipeline
Desde la raíz del proyecto, ejecute:

```bash
python pipeline.py
```

El pipeline detecta el archivo de RPA en la carpeta datos_macroentorno, procesa las fuentes públicas y carga los datos en PostgreSQL.

## Estructura del repositorio
```text
Arquitectura/
DB/
data/
ETL/
datos_macroentorno/
pipeline.py
README.md
tests/
```

## Consideraciones de implementación
- El flujo está diseñado para ejecutarse de forma secuencial y reproducible.
- Los datos se almacenan en tablas de hechos y dimensiones del modelo analítico.
- Se incluyen vistas gold para facilitar consultas analíticas y reportes de negocio.

## Estado del proyecto
El proyecto se encuentra funcional para la carga de datos y la generación de la base analítica asociada al caso de estudio.
