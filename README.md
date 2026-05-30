# Logger Tracker

Una librería de logging estandarizada para Python que proporciona trazabilidad mediante UUIDs únicos por hilo de ejecución, con soporte para salida enriquecida en consola.

## Descripción

Logger Tracker es un módulo de logging diseñado para entornos concurrentes y aplicaciones web. Proporciona:

- **UUIDs únicos por hilo**: Cada log incluye un identificador único para trazabilidad en entornos multi-hilo
- **Salida enriquecida**: Usa Rich para tracebacks y formateo mejorado en consola
- **Configuración automática**: Se configura al importar el módulo
- **Nivel de logging configurable**: Soporte para variable de entorno LOG_LEVEL
- **API simple**: Funciones de logging estandarizadas con acceso directo
- **Integración con frameworks**: Soporte nativo para Flask/Werkzeug

## Instalación

Instala desde PyPI:

```bash
pip install logguer-tracker
```

O desde el código fuente:

```bash
git clone https://github.com/tu-usuario/logguer-tracker.git
cd logguer-tracker
pip install -e .
```

## Configuración

### Nivel de Logging

El nivel de logging se puede configurar mediante la variable de entorno `LOG_LEVEL`. Si no se establece, por defecto es `DEBUG`.

Niveles disponibles: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

#### Ejemplos de configuración:

**En Linux/macOS:**
```bash
export LOG_LEVEL=INFO
python tu_aplicacion.py
```

**En Windows (Command Prompt):**
```cmd
set LOG_LEVEL=INFO
python tu_aplicacion.py
```

**En Windows (PowerShell):**
```powershell
$env:LOG_LEVEL = 'INFO'
python tu_aplicacion.py
```

**En un script Python:**
```python
import os
os.environ['LOG_LEVEL'] = 'WARNING'
import logger_tracker  # Importar después de configurar la variable
```

**En un archivo .env (usando python-dotenv):**
```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

import logger_tracker
```

Archivo `.env`:
```
LOG_LEVEL=INFO
```

**En Docker:**
```dockerfile
ENV LOG_LEVEL=WARNING
```

**En docker-compose.yml:**
```yaml
services:
  tu_app:
    environment:
      - LOG_LEVEL=ERROR
```

## Uso Básico

### Importación y configuración automática

Simplemente importa el módulo para configurar el logging automáticamente:

```python
import logger_tracker

# El logging ya está configurado con UUIDs y Rich handler
```

### Uso de la API principal

```python
from logger_tracker import get_logger

# Obtener un logger con funciones de logging
logger = get_logger("mi_modulo")

logger["info"]("Mensaje informativo")
logger["debug"]("Mensaje de debug")
logger["warning"]("Mensaje de advertencia")
logger["error"]("Mensaje de error")
logger["critical"]("Mensaje crítico")
```

### Uso de funciones legacy

Para compatibilidad con código existente:

```python
from logger_tracker import logg_info, logg_debug, logg_warning, logg_error, logg_critical

logg_info("Mensaje informativo")
logg_debug("Mensaje de debug")
logg_warning("Mensaje de advertencia")
logg_error("Mensaje de error")
logg_critical("Mensaje crítico")
```

## Características

- **Thread-safe**: UUIDs únicos por hilo de ejecución
- **Trazabilidad**: Cada log incluye un UUID para seguimiento
- **Salida enriquecida**: Tracebacks coloreados y formateados con Rich
- **Configuración automática**: No requiere configuración manual
- **Nivel de logging configurable**: Control del nivel mediante variable de entorno LOG_LEVEL
- **Integración con Flask**: Soporte automático para logging de Werkzeug
- **API flexible**: Tanto dict-based como funciones directas

## Observabilidad (OpenTelemetry)

Logger Tracker ofrece integración opcional con OpenTelemetry para trazas y métricas.
Las dependencias OTEL son opt-in y se instalan con el extra `otel`.

Instalación con Poetry (incluye instrumentaciones):

```bash
poetry install --extras "otel"
```

Instalación con pip (wheel/pyproject):

```bash
pip install .[otel]
```

Variables de entorno relevantes (puedes cargar con `config-mounter` antes de importar):

- `OTEL_SERVICE_NAME` o `SERVICE_NAME` — nombre del servicio
- `OTEL_EXPORTER_OTLP_ENDPOINT` — endpoint OTLP para exportar trazas (si no está, usa consola)
- `LOG_LEVEL` — nivel de logging (DEBUG, INFO, ...)

Uso básico de observabilidad:

```python
import os
import config_mounter
from logger_tracker import setup_observability, instrument_all, attach_flask_instrumentation, get_tracer

# config-mounter debe haber cargado las variables de entorno
setup_observability()  # configura tracer provider y exporter basado en env vars

# instrumenta requests y sqlalchemy (si están instalados)
instrument_all()

# En una app Flask
from flask import Flask
app = Flask(__name__)
attach_flask_instrumentation(app)

# Usar tracer en código
tracer = get_tracer("my.module")
with tracer.start_as_current_span("operation"):
    # tu código instrumentado
    pass
```

Correlación logs ↔ trazas
- `logger_tracker` añade automáticamente `trace_id` y `span_id` a los registros si OpenTelemetry está activo.
- Además mantiene un `UUID` por hilo (`get_request_uuid()`), útil como `correlation_id`.

Instrumentaciones disponibles
- `instrument_requests()` — instrumenta la librería `requests`.
- `instrument_sqlalchemy(engine_or_url=None)` — intenta instrumentar SQLAlchemy. Si pasas un `engine` se intentará instrumentar ese motor.
- `instrument_all()` — convenience que aplica ambas.

Ejemplo con `config-mounter` (WSL / entorno Docker):

```bash
# Cargar variables con config-mounter en tu proyecto
# (ejemplo conceptual)
python -c "import config_mounter, os; print('envs loaded')"

# Ejecutar tests con poetry
poetry run pytest -q
```

Notas
- Si no instalas el extra `otel`, todas las APIs de observabilidad son no-op y la librería sigue funcionando solo como logger.
- Para enviar datos a Datadog, CloudWatch u OpenSearch, configura un collector/receiver OTLP apropiado o instala el exporter específico en tu runtime.

## API

### Funciones principales

- `setup_logging()`: Configura el sistema de logging (llamado automáticamente al importar)
- `get_logger(name: str) -> dict`: Devuelve un diccionario con funciones de logging
- `get_request_uuid() -> str`: Obtiene el UUID único del hilo actual
- `set_request_uuid(custom_uuid: str)`: Establece un UUID personalizado para el hilo actual
- `attach_logger_to_werkzeug()`: Integra el logging con Flask/Werkzeug

### Funciones legacy

- `logg_info(message)`
- `logg_debug(message)`
- `logg_warning(message)`
- `logg_error(message)`
- `logg_critical(message)`

## Ejemplos

### En una aplicación Flask

```python
from flask import Flask
from logger_tracker import get_logger, attach_logger_to_werkzeug

app = Flask(__name__)

# Configurar logging para Flask
attach_logger_to_werkzeug()

logger = get_logger("flask_app")

@app.route('/')
def hello():
    logger["info"]("Solicitud a la ruta principal")
    return "Hello World!"

if __name__ == '__main__':
    app.run()
```

### En un script multi-hilo

```python
import threading
import time
from logger_tracker import get_logger

def worker(worker_id):
    logger = get_logger(f"worker_{worker_id}")
    logger["info"](f"Trabajador {worker_id} iniciado")
    time.sleep(1)
    logger["info"](f"Trabajador {worker_id} finalizado")

# Crear múltiples hilos
threads = []
for i in range(3):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

Cada hilo tendrá su propio UUID en los logs, permitiendo trazabilidad completa.

### Acceso al UUID para correlacionar datos

El UUID de cada hilo es accesible mediante `get_request_uuid()`, permitiendo almacenar datos correlacionados:

```python
from logger_tracker import get_logger, get_request_uuid, set_request_uuid

logger = get_logger("app")

# Opción 1: Usar el UUID auto-generado
logger["info"]("Iniciando procesamiento")
transaction_id = get_request_uuid()
# Almacenar datos con este UUID
db.save_transaction(uuid=transaction_id, status="started")

# Opción 2: Usar un UUID personalizado (e.g., de una request HTTP)
request_uuid = "req-12345-abc"
set_request_uuid(request_uuid)
logger["info"]("Procesando request")  # Los logs llevarán "req-12345-abc"
db.save_request_log(uuid=get_request_uuid(), action="processed")
```

**Caso de uso en Flask:**

```python
from flask import Flask, request
from logger_tracker import get_logger, set_request_uuid, get_request_uuid

app = Flask(__name__)
logger = get_logger("flask_app")

@app.before_request
def set_uuid():
    # Usar el header X-Request-ID si existe, sino auto-generar
    request_id = request.headers.get('X-Request-ID', None)
    if request_id:
        set_request_uuid(request_id)
    logger["info"](f"Nuevo request: {request.method} {request.path}")

@app.route('/api/process')
def process():
    # El UUID está disponible en toda la request
    correlation_id = get_request_uuid()
    logger["info"](f"Procesando con ID: {correlation_id}")
    
    # Guardar logs correlacionados en BD
    db.save_audit_log(
        correlation_id=correlation_id,
        action="process_api",
        user_id=get_user_id()
    )
    
    return {"id": correlation_id}
```

## Formato de salida

Los logs se muestran en el formato:

```
[UUID] Mensaje
```

Ejemplo:

```
[550e8400-e29b-41d4-a716-446655440000] Aplicación iniciada
[550e8400-e29b-41d4-a716-446655440000] Procesando solicitud
[6ba7b810-9dad-11d1-80b4-00c04fd430c8] Nuevo hilo iniciado
```

## Requisitos

- Python >= 3.13
- rich
- pytest (para tests)

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.
