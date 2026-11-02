# E-Commerce API (FastAPI) - Reto IA UIS

API RESTful de comercio electrónico de alto rendimiento desarrollada con **FastAPI** y **SQLAlchemy**. Diseñada para ofrecer operaciones transaccionales seguras y concurrentes, control riguroso de inventario, cálculo automatizado de descuentos, paginación eficiente y trazabilidad de pedidos.

---

## 🚀 Funcionalidades Principales

* **Gestión de Usuarios:**
  * Registro de usuarios con validación de datos.
  * Restricción de unicidad estricta para evitar cuentas duplicadas con el mismo correo electrónico (código HTTP `409 Conflict`).
* **Catálogo de Productos y Paginación:**
  * Consulta del catálogo optimizada para alto volumen mediante paginación con `limit` (por defecto: 10, máximo: 100) y `offset` (mínimo: 0).
  * Validación automática de parámetros de consulta con FastAPI y Pydantic (HTTP `422 Unprocessable Entity`).
* **Procesamiento Concurrente de Pedidos:**
  * Prevención del problema de consultas $N+1$ consultando productos en lote mediante `Product.id.in_()`.
  * Control de concurrencia y prevención de sobreventa (*overselling*) de la última unidad mediante bloqueo pesimista a nivel de fila con `.with_for_update()`.
  * Validación de disponibilidad de stock antes de descontar inventario, rechazando pedidos con stock insuficiente (HTTP `400 Bad Request`).
  * Aplicación automática de regla de negocio: **10% de descuento** sobre productos con precio superior a 100.
* **Historial de Compras por Usuario:**
  * Endpoint `GET /users/{user_id}/orders` para listar todas las órdenes de un usuario con ID de orden, total y nombres de productos comprados.
  * Optimización mediante *Eager Loading* (`joinedload`) para resolver relaciones en una única consulta SQL `JOIN`, eliminando consultas redundantes en bucles.
  * Manejo de usuario inexistente con HTTP `404 Not Found`.

---

## 📁 Estructura del Proyecto

```text
ecommerce_api_reto_ia-main/
│
├── .coveragerc              # Configuración de exclusiones y reportes para pytest-cov
├── .dockerignore            # Archivos excluidos del contexto de construcción de Docker
├── .env.example             # Plantilla de variables de entorno segura para desarrollo y Docker
├── .gitignore               # Archivos y directorios ignorados por Git
├── database.py              # Configuración del motor SQLAlchemy, sesiones y get_db()
├── Dockerfile               # Definición de imagen de contenedor optimizada para FastAPI
├── docker-compose.yml       # Orquestación de servicios de API y base de datos MySQL
├── main.py                  # Aplicación FastAPI, definición de rutas, OpenAPI y lógica
├── models.py                # Modelos ORM relacionales (User, Product, Order)
├── pytest.ini               # Configuración del ejecutor de pruebas pytest y cobertura
├── README.md                # Documentación técnica completa del proyecto
├── requirements.txt         # Dependencias del proyecto y paquetes de testing
├── schemas.py               # Esquemas de validación y documentación Pydantic
│
└── tests/                   # Suite completa de pruebas automatizadas
    ├── __init__.py          # Inicializador del paquete de pruebas
    ├── conftest.py          # Fixtures de BD aislada en memoria (SQLite) y TestClient
    ├── test_history.py      # Pruebas de integración de historial de pedidos
    ├── test_orders.py       # Pruebas de procesamiento de órdenes y concurrencia
    ├── test_products.py     # Pruebas de catálogo de productos y paginación
    ├── test_units.py        # Pruebas unitarias de funciones independientes (descuentos, get_db)
    └── test_users.py        # Pruebas de registro de usuarios y validación de unicidad
```

---

## 🛠️ Requisitos Previos

* **Python:** Versión 3.10 o superior (compatible y probado hasta Python 3.14).
* **Base de Datos:** Servidor MySQL 8.0+ o MariaDB (o SQLite para ejecución de pruebas en memoria).
* **Gestor de paquetes:** `pip`.

---

## ⚙️ Instalación y Configuración

### 1. Clonar o abrir el directorio del proyecto
```bash
cd ecommerce_api_reto_ia-main
```

### 2. Crear y activar un entorno virtual

* En **Linux / macOS**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

* En **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

* En **Windows (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
El proyecto utiliza `python-dotenv` para cargar variables de entorno en desarrollo. Crea un archivo `.env` a partir de la plantilla `.env.example`:

* En **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

* En **Windows**:
  ```cmd
  copy .env.example .env
  ```

Edita el archivo `.env` para ajustar las credenciales a tu servidor MySQL local:
```env
DATABASE_URL=mysql+pymysql://usuario_mysql:contraseña_mysql@localhost:3306/ecommerce_db
```

> **Nota de seguridad:** La aplicación valida en el arranque la existencia de `DATABASE_URL`. Si la variable no está definida en el sistema ni en el archivo `.env`, se detendrá arrojando un error claro `RuntimeError`.

---

## 🏃 Ejecución Local de la API

Inicia el servidor de desarrollo Uvicorn con recarga en caliente (*hot-reload*):

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

La API quedará escuchando peticiones en:
`http://127.0.0.1:8000`

---

## 🐳 Ejecución con Docker y Docker Compose

Para desplegar la API junto con su base de datos MySQL en contenedores aislados y reproducibles:

### 1. Construir e iniciar los servicios en segundo plano
```bash
docker compose up --build -d
```
> **Nota de arranque seguro:** La aplicación FastAPI esperará automáticamente a que el contenedor de MySQL esté completamente inicializado y en estado saludable (*healthy*) antes de iniciar, gracias al `healthcheck` de MySQL y la directiva `depends_on: { db: { condition: service_healthy } }`.

### 2. Consultar el estado de los servicios
```bash
docker compose ps
```

### 3. Visualizar los registros (logs) en tiempo real
* Todos los servicios:
  ```bash
  docker compose logs -f
  ```
* Solo el servicio de la API:
  ```bash
  docker compose logs -f api
  ```
* Solo la base de datos MySQL:
  ```bash
  docker compose logs -f db
  ```

### 4. Acceso a los servicios desplegados
* API FastAPI: `http://localhost:8000`
* Swagger UI interactivo: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`
* Servidor MySQL: `localhost:3306`

### 5. Detener los servicios
* Detener contenedores conservando los datos de la base de datos (volumen `mysql_data` persistido):
  ```bash
  docker compose down
  ```
* Detener y eliminar los volúmenes (reinicio total desde cero):
  ```bash
  docker compose down -v
  ```

### 6. Ejecutar pruebas automatizadas dentro del contenedor
```bash
docker compose exec api pytest
```

---

## 📖 Documentación Interactiva (Swagger y ReDoc)

FastAPI genera automáticamente documentación interactiva basada en la especificación OpenAPI 3.0:

* **Swagger UI (Pruebas interactivas en navegador):**  
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
  Permite explorar los endpoints, ver esquemas JSON, ejemplos y probar las solicitudes en tiempo real desde la interfaz web.

* **ReDoc (Documentación técnica detallada y limpia):**  
  [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)  
  Ideal para lectura y especificación formal de la API.

* **Esquema OpenAPI en formato JSON:**  
  [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 📌 Endpoints Disponibles

| Tag | Método | Ruta | Parámetros / Payload | Códigos de Respuesta | Descripción |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Usuarios** | `POST` | `/users/` | Body JSON: `{"name": str, "email": str}` | `200`, `409`, `422` | Registra un usuario verificando unicidad de correo. |
| **Usuarios** | `GET` | `/users/{user_id}/orders` | Path: `user_id` (int $\ge 1$) | `200`, `404`, `422` | Retorna el historial de compras (`order_id`, `total`, `products`). |
| **Productos** | `GET` | `/products/` | Query: `limit` (int, 1-100, def: 10), `offset` (int, $\ge 0$, def: 0) | `200`, `422` | Lista el catálogo de productos con paginación controlada. |
| **Pedidos** | `POST` | `/orders/` | Body JSON: `{"user_id": int, "product_ids": [int, ...]}` | `200`, `400`, `404`, `422` | Procesa orden con bloqueo de stock y regla del 10% de descuento. |

---

## 🧪 Pruebas Automatizadas y Cobertura

El proyecto incluye una suite completa de pruebas unitarias y de integración construida con `pytest`, `pytest-cov` y `TestClient`, utilizando una base de datos SQLite en memoria aislada para no alterar datos reales.

### Ejecutar todas las pruebas con reporte de cobertura en terminal:
```bash
pytest
```

### Ejecutar pruebas mostrando el desglose línea por línea:
```bash
pytest -v --cov=. --cov-report=term-missing
```

### Generar reporte visual en HTML:
```bash
pytest --cov=. --cov-report=html
```
El reporte detallado se generará en la carpeta `htmlcov/index.html`.
