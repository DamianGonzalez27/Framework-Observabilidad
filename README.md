# 📊 Logger-Tracker - Observabilidad unificada para Python

[![PyPI version](https://badge.fury.io/py/logger-tracker.svg)](https://badge.fury.io/py/logger-tracker)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-ready-blue)](https://opentelemetry.io/)

**Logger-Tracker** es una librería que unifica logs estructurados, trazas distribuidas y métricas en una sola API sencilla. Está construida sobre **OpenTelemetry** (opcional) para que puedas exportar tus datos de telemetría a cualquier backend (Datadog, Jaeger, Prometheus, Elasticsearch, OpenSearch, etc.) sin cambiar tu código.

## ✨ Características

- 📝 **Logging estructurado** (JSON o texto) con niveles y contexto enriquecido.
- 🔗 **Correlación automática** entre logs y trazas (inyecta `trace_id` y `span_id` en cada log).
- 🧭 **Trazas distribuidas** con spans manuales y automáticos (Flask, SQLAlchemy, requests).
- 📈 **Métricas básicas** (contadores, histogramas) vía OpenTelemetry Metrics API.
- ⚙️ **Configuración 100% mediante variables de entorno**.
- 🧩 **Integración nativa con Flask** (middleware automático).
- 🚀 **Ligero** por defecto; solo activa OpenTelemetry cuando instalas `[otel]`.

## 📦 Instalación

```bash
# Instalación mínima (solo logs estructurados)
poetry add logger-tracker

# Instalación completa con OpenTelemetry (trazas + métricas + instrumentaciones automáticas)
poetry add "logger-tracker[otel]"
```

Con pip:

```bash
pip install logger-tracker[otel]
```

## 🚀 Inicio rápido

### 1. Configuración por variables de entorno
Crea un archivo .env o exporta las variables:

```bash
# Obligatorias (recomendadas)
OTEL_SERVICE_NAME="mi-servicio"
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"   # Si omites, consola

# Opcionales
LOG_LEVEL="INFO"                      # DEBUG, INFO, WARNING, ERROR
OTEL_TRACES_SAMPLER="parentbased_always_on"
OTEL_METRICS_EXPORTER="otlp"          # o "none"
```

### 2. Inicialización en tu aplicación

```bash
# app.py
from logger_tracker import setup_observability, instrument_all, get_logger

# ⚠️ Esto debe ser lo PRIMERO antes de importar cualquier otro módulo
setup_observability()
instrument_all()   # Activa instrumentación automática de Flask, SQLAlchemy, requests

logger = get_logger(__name__)

logger.info("Aplicación iniciada correctamente")
```

### 3. Uso básico de logging
```bash
from logger_tracker import get_logger

logger = get_logger("modulo_pagos")
logger.debug("Depurando conexión")
logger.info("Procesando pago", extra={"user_id": 123, "amount": 99.99})
logger.error("Error de red", exc_info=True)
```
Cada entrada de log incluirá automáticamente trace_id, span_id y service.name si OpenTelemetry está activo.

## 🧭 Trazas distribuidas (spans manuales)

```bash
from logger_tracker import get_tracer, get_logger

tracer = get_tracer("mi_aplicacion")
logger = get_logger(__name__)

def hacer_pedido(producto_id, cantidad):
    with tracer.start_as_current_span("procesar_pedido") as span:
        span.set_attribute("producto.id", producto_id)
        span.set_attribute("cantidad", cantidad)
        
        logger.info(f"Iniciando pedido de {cantidad} unidades")
        # ... lógica de negocio ...
        logger.info("Pedido completado")
```

## 🌐 Integración con Flask

```bash
from flask import Flask
from logger_tracker import attach_flask_instrumentation

app = Flask(__name__)
attach_flask_instrumentation(app)   # Crea spans automáticos para cada request

@app.route("/health")
def health():
    return {"status": "ok"}
```

## 📡 Exportación de datos (OTLP)
Por defecto, los datos se envían al endpoint definido en OTEL_EXPORTER_OTLP_ENDPOINT. Puedes usar un OpenTelemetry Collector o enviar directamente a:
| Backend	| Endpoint ejemplo |
|-------------------------------|
| Datadog	| https://api.datadoghq.com + header dd-api-key |
| Jaeger	| http://jaeger:4317 |
| Grafana Cloud	| https://otlp-gateway-prod-us-central-0.grafana.net/otlp |
| Local collector	| http://localhost:4317 (gRPC) o 4318 (HTTP) |

Ejemplo con Datadog (sin collector):
```bash
OTEL_EXPORTER_OTLP_ENDPOINT="https://api.datadoghq.com"
OTEL_EXPORTER_OTLP_HEADERS="dd-api-key=TU_API_KEY"
OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
```

## 🔌 Instrumentación de adaptadores externos

Si tu proyecto usa Redis, Elasticsearch, Kafka o RabbitMQ, puedes instrumentarlos fácilmente después de setup_observability().

```bash
poetry add opentelemetry-instrumentation-redis \
            opentelemetry-instrumentation-elasticsearch \
            opentelemetry-instrumentation-confluent-kafka \
            opentelemetry-instrumentation-pika
```

### Código de instrumentación (en tu punto de entrada)

```bash
from logger_tracker import setup_observability, instrument_all

setup_observability()
instrument_all()   # Flask, SQLAlchemy, requests

# Redis
from opentelemetry.instrumentation.redis import RedisInstrumentor
RedisInstrumentor().instrument()

# Elasticsearch
from opentelemetry.instrumentation.elasticsearch import ElasticsearchInstrumentor
ElasticsearchInstrumentor().instrument()

# Kafka (confluent_kafka)
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
ConfluentKafkaInstrumentor().instrument()

# RabbitMQ (pika)
from opentelemetry.instrumentation.pika import PikaInstrumentor
PikaInstrumentor().instrument()
```
Ahora cada operación de Redis, Elasticsearch, Kafka o RabbitMQ generará spans hijos del contexto actual.

## 📈 Métricas
Actualmente logger-tracker expone métricas básicas vía OpenTelemetry Metrics API. Puedes registrar contadores e histogramas:

```bash
from logger_tracker import get_meter

meter = get_meter("mi_app")
contador_peticiones = meter.create_counter("peticiones_totales")
duracion = meter.create_histogram("duracion_procesamiento")

def mi_endpoint():
    contador_peticiones.add(1, {"endpoint": "/api"})
    with duracion.record(automatic=True):
        # lógica...
```
Estas métricas se exportan al mismo OTLP endpoint.

### 🧪 Ejemplo completo con Flask + Redis + Trazas

```bash
# app.py
import os
from flask import Flask
from logger_tracker import (
    setup_observability, instrument_all, get_logger, get_tracer,
    attach_flask_instrumentation
)
from opentelemetry.instrumentation.redis import RedisInstrumentor
import redis

setup_observability()
instrument_all()
attach_flask_instrumentation(app)  # se define app después? mejor orden

app = Flask(__name__)
RedisInstrumentor().instrument()
r = redis.Redis(host='localhost', port=6379)

logger = get_logger(__name__)
tracer = get_tracer("flask_redis")

@app.route("/cache/<key>")
def get_cache(key):
    with tracer.start_as_current_span("consultar_cache") as span:
        span.set_attribute("cache.key", key)
        value = r.get(key)
        logger.info(f"Valor obtenido para key {key}: {value}")
        return {"key": key, "value": value}
```

### 🛠️ Variables de entorno completas

| Variable	| Descripción	| Default |
|-------------------------------------|
| OTEL_SERVICE_NAME	| Nombre del servicio (obligatorio para tracing)	| "unknown_service" |
| OTEL_EXPORTER_OTLP_ENDPOINT	| Endpoint OTLP (gRPC) para exportar trazas, métricas y logs	| None (consola) |
| LOG_LEVEL	| Nivel de logging (DEBUG, INFO, WARNING, ERROR)	| INFO |
| OTEL_TRACES_SAMPLER	| Estrategia de muestreo (always_on, always_off, parentbased_always_on)	| parentbased_always_on |
| OTEL_METRICS_EXPORTER	| otlp o none	| otlp si hay endpoint |
| OTEL_LOGS_EXPORTER	| otlp o none	| otlp si hay endpoint |
| OTEL_PYTHON_LOG_CORRELATION	| Inyectar trace_id en logs (siempre activo)	| true |

## 🔧 Solución de problemas

### Los logs no muestran trace_id

- Verifica que setup_observability() se ejecute antes de cualquier import de get_logger.
- Asegúrate de que OTEL_EXPORTER_OTLP_ENDPOINT esté definido y sea accesible.

### Las trazas no aparecen en Jaeger/Datadog

- Comprueba que el endpoint OTLP esté correcto y el backend lo soporte.
- Revisa que el muestreo no esté desactivado (OTEL_TRACES_SAMPLER=always_on).

### Conflictos con otras librerías de logging
- logger-tracker usa los handlers estándar de Python. Puedes añadir tus propios handlers y seguirá funcionando.

## 📚 Recursos adicionales

- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Ejemplo completo en GitHub](https://github.com/DamianGonzalez27/Transactional-Service-Framework)
