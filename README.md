# Pipeline ETL y Data Warehouse: Análisis del Macroentorno Ecuatoriano

Este repositorio contiene la implementación técnica del proyecto de Ingeniería de Datos desarrollado para la Dirección General de Tecnologías de la Información y Transformación Digital (DGTITD) de la Universidad Técnica Particular de Loja (UTPL).

El proyecto resuelve la problemática de fragmentación de información gubernamental (BCE, INEC, MINEDUC, Superintendencia de Compañías) mediante la construcción de un Data Warehouse centralizado, un pipeline de datos automatizado y un modelo analítico diseñado para identificar fenómenos socioeconómicos críticos, tales como la brecha laboral y la fuga de talentos.

---

# Estructura del Repositorio

En estricto cumplimiento con las directrices de la DGTITD, el repositorio mantiene la siguiente jerarquía de directorios:

```text
repositorio-del-proyecto/
├── 01_Reto_Inicial_Historico/      # Respaldos y entregables de fases iniciales
├── documentacion/
│   └── presentaciones/             # Archivos de presentación de avances y sustentación final
├── articulo/
│   ├── estado-del-arte/            # Investigación preliminar y marco conceptual
│   └── version-final/              # Documento técnico final (Formato IEEE)
└── codigo-fuente/
    ├── src/                        # Módulos de limpieza, transformación y orquestación
    ├── data/                       # (Ignorado en control de versiones) Insumos estáticos
    ├── RPA/                        # (Ignorado en control de versiones) Volcados de base de datos
    ├── pipeline.py                 # Orquestador principal del flujo de datos (Prefect)
    ├── requirements.txt            # Dependencias del entorno de Python
    └── README.md                   # Documentación técnica y despliegue (Este archivo)
```

---

# Requisitos del Sistema

Para el correcto despliegue y ejecución de este proyecto en un entorno local, se requiere la instalación de las siguientes herramientas:

- Python 3.9 o superior.
- PostgreSQL (instalación local o mediante contenedor Docker).
- Metabase (plataforma de Inteligencia de Negocios para la capa de presentación).

---

# Instrucciones de Instalación y Despliegue

Siga secuencialmente los siguientes pasos para configurar el entorno y ejecutar el pipeline ETL.

## 1. Clonación del repositorio

Descargue el código fuente en su estación de trabajo y navegue hacia el directorio principal de ejecución.

```bash
git clone <URL_DE_SU_REPOSITORIO>
cd repositorio-del-proyecto/codigo-fuente
```

---

## 2. Configuración del entorno virtual

Se requiere el aislamiento de las dependencias mediante un entorno virtual para evitar conflictos de librerías a nivel de sistema.

### Creación del entorno virtual

```bash
python -m venv venv
```

### Activación en Windows

```bash
venv\Scripts\activate
```

### Activación en Linux/macOS

```bash
source venv/bin/activate
```

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

---

## 3. Configuración de la Base de Datos

El proyecto asume una conexión local hacia el motor PostgreSQL. Es indispensable la creación previa de una base de datos denominada **practicum_db**.

**Nota técnica:** Las credenciales de conexión predeterminadas en los scripts apuntan a `localhost`. Para entornos de prueba o producción, modifique las variables `DB_USER`, `DB_PASS`, `DB_HOST` y `DB_PORT` ubicadas en la cabecera de los scripts dentro del directorio `src/`.

---

## 4. Ejecución del Orquestador (Pipeline)

El proyecto implementa el framework Prefect para el control de flujo. Para iniciar el proceso automatizado de extracción, transformación (incluyendo el procesamiento por lotes para archivos RPA masivos) y carga transaccional hacia la base de datos, ejecute:

```bash
python pipeline.py
```

---

## 5. Monitoreo de Procesos

Para supervisar la trazabilidad de los datos, el estado de las tareas y los registros (logs) del orquestador mediante interfaz gráfica, inicie el servidor local de Prefect abriendo una nueva sesión de terminal:

```bash
prefect server start
```

Posteriormente, acceda desde su navegador a:

```text
http://127.0.0.1:4200
```

---

# Capa de Visualización Analítica

Al finalizar la ejecución del pipeline con estado exitoso, las Vistas Materializadas (Capa Gold) en PostgreSQL se actualizan automáticamente.

Estas vistas, diseñadas para prevenir redundancias y productos cartesianos, actúan como fuente de datos directa para Metabase, renderizando el Dashboard Estratégico sin comprometer el rendimiento del motor transaccional.

---

# Autor

**Lucas Darío Jumbo Granda**

Titulación: Ingeniería en Ciencias de la Computación – UTPL

Período Académico: Abril – Agosto 2026
