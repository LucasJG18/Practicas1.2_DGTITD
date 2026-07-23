# Pipeline ETL y Data Warehouse: Análisis del Macroentorno Ecuatoriano

Este repositorio contiene la implementación técnica del proyecto de Ingeniería de Datos desarrollado para la **Dirección General de Tecnologías de la Información y Transformación Digital (DGTITD)** de la **Universidad Técnica Particular de Loja (UTPL)**.

El proyecto resuelve la problemática de fragmentación de información gubernamental (**BCE, INEC, MINEDUC y Superintendencia de Compañías**) mediante la construcción de un **Data Warehouse** centralizado, un **pipeline ETL automatizado** y un **modelo analítico** diseñado para identificar fenómenos socioeconómicos críticos, tales como la **brecha laboral** y la **fuga de talentos**.

---

# Estructura del Repositorio

En estricto cumplimiento con las directrices de la DGTITD, el repositorio mantiene la siguiente jerarquía de directorios:

```text
Practicas1.2_DGTITD/
├── 01_Historico/                   # Respaldos y entregables de fases iniciales (Reto 1)
├── documentacion/
│   └── presentaciones/             # Archivos de presentación de sustentación final
├── articulo/
│   └── version-final/              # Documento técnico final (Formato IEEE)
├── codigo-fuente/
│   ├── src/                        # Entorno principal de ejecución (Scripts y Orquestador)
│   │   ├── Arquitectura/           # Diagramas y referencias de la arquitectura
│   │   ├── ETL/                    # Scripts de extracción (BCE, INEC, MINEDUC, etc.)
│   │   ├── Limpieza/               # Módulos de normalización y estandarización
│   │   ├── RPA/                    # Algoritmos de procesamiento masivo por lotes
│   │   ├── tests/                  # Pruebas unitarias de integridad y dependencias
│   │   └── pipeline.py             # Orquestador maestro del flujo de datos (Prefect)
│   ├── .gitignore                  # Reglas de exclusión de control de versiones
│   └── requirements.txt            # Dependencias oficiales del entorno de Python
└── README.md                       # Documentación técnica y despliegue (Este archivo)
```

> **Nota:** Los directorios de bases de datos locales, entornos virtuales y volcados de información cruda se excluyen mediante `.gitignore` por motivos de seguridad y límites de almacenamiento.

---

# Requisitos del Sistema

Para el correcto despliegue y ejecución del proyecto se requiere:

- Python **3.10** o superior.
- PostgreSQL (instalación local o mediante Docker).
- Metabase (plataforma de Business Intelligence).

---

# Instalación y Despliegue

Siga secuencialmente los siguientes pasos para configurar el entorno y ejecutar el pipeline ETL.

## 1. Clonar el repositorio

Descargue el código fuente y navegue hacia el directorio del proyecto.

```bash
git clone https://github.com/LucasJG18/Practicas1.2_DGTITD.git
cd Practicas1.2_DGTITD/codigo-fuente
```

---

## 2. Configurar el entorno virtual

Se recomienda utilizar un entorno virtual para aislar las dependencias del proyecto.

### Crear el entorno virtual

```bash
python -m venv venv
```

### Activar el entorno en Windows

```bash
venv\Scripts\activate
```

### Activar el entorno en Linux/macOS

```bash
source venv/bin/activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 3. Configuración de PostgreSQL

El proyecto asume una conexión local hacia PostgreSQL.

Antes de ejecutar el pipeline, cree una base de datos denominada:

```text
practicum_db
```

> **Nota técnica:** Las credenciales de conexión predeterminadas apuntan a `localhost`. Para entornos de desarrollo, pruebas o producción, modifique las variables de conexión ubicadas en los scripts contenidos en los directorios `ETL/` y `Limpieza/`.

---

## 4. Ejecutar el Pipeline ETL

El proyecto utiliza **Prefect** como orquestador del flujo de datos.

Desde el directorio `codigo-fuente`, navegue a `src/` y ejecute:

```bash
cd src
python pipeline.py
```

Este proceso ejecutará automáticamente las etapas de:

- Extracción de datos.
- Limpieza y normalización.
- Transformación.
- Carga hacia PostgreSQL.
- Actualización de la capa analítica.

---

## 5. Monitoreo del Pipeline

Para visualizar el estado de las tareas, registros (logs) y trazabilidad del proceso, inicie el servidor local de Prefect en una nueva terminal.

```bash
prefect server start
```

Posteriormente acceda desde su navegador a:

```text
http://127.0.0.1:4200
```

---

# Capa de Visualización Analítica

Una vez finalizada exitosamente la ejecución del pipeline:

- Las **Vistas Materializadas (Capa Gold)** en PostgreSQL se actualizan automáticamente.
- Dichas vistas actúan como fuente de datos para **Metabase**.
- Los dashboards estratégicos consumen directamente estas vistas optimizadas, evitando redundancias y productos cartesianos, garantizando un mejor rendimiento del motor relacional.

---

# Tecnologías Utilizadas

- Python
- PostgreSQL
- Prefect
- Metabase
- Pandas
- SQLAlchemy
- Docker (opcional)

---

# Autor

**Lucas Darío Jumbo Granda**

**Ingeniería en Ciencias de la Computación**  
Universidad Técnica Particular de Loja (UTPL)

**Período Académico:** Abril – Agosto 2026
