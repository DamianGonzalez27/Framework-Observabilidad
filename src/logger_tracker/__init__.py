# -------------------------
# Copyright (c) 2026 Erick Damian Gonzalez Aranda
#
# Este software y su código fuente han sido desarrollados por Erick Damian Gonzalez Aranda, mediante 
# NeuronexoTec Organizacion de desarrollo de Software.
# Todos los derechos están reservados.
#
# Se permite el uso, copia y modificación del código únicamente para fines
# personales, educativos o internos, siempre que se conserve este aviso
# de copyright y no se redistribuya el software, total o parcialmente,
# sin autorización expresa del autor.
#
# Queda estrictamente prohibida la venta, sublicencia, redistribución,
# exposición como servicio (SaaS), o incorporación en productos comerciales
# sin consentimiento previo y por escrito del autor.
#
# Este software se proporciona "tal cual", sin garantía de ningún tipo,
# expresa o implícita, incluyendo pero no limitado a garantías de
# comercialización, idoneidad para un propósito particular o ausencia
# de defectos.
# 
# El autor no será responsable por ningún daño directo o indirecto
# derivado del uso de este software.
# -------------------------

import logging
import os
import threading
import uuid
from typing import Callable

from rich.logging import RichHandler


# -------------------------
# Almacenamiento thread-local
# Responsabilidad:
# Mantener un UUID único por hilo de ejecución
# para trazabilidad de logs en entornos concurrentes
# -------------------------
_request_uuid = threading.local()


# -------------------------
# Filtro de logging con UUID
# Responsabilidad:
# Inyectar un UUID por request/hilo
# en cada registro de log
#
# Uso:
# Se asocia a handlers de logging
# -------------------------
class UUIDLogFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(_request_uuid, "id"):
            _request_uuid.id = str(uuid.uuid4())

        record.uuid = _request_uuid.id

        # Intentar obtener trace/span ids desde OpenTelemetry (si está disponible)
        try:
            from . import otel as _otel
            trace_id, span_id = _otel.get_current_trace_ids()
            record.trace_id = trace_id or ""
            record.span_id = span_id or ""
        except Exception:
            # Si algo falla o OTEL no está instalado, no interrumpir el logging
            record.trace_id = ""
            record.span_id = ""

        return True


# -------------------------
# Configuración del sistema de logging
# Responsabilidad:
# Inicializar logging global con:
# - UUID por request
# - RichHandler para salida en consola
# - Formato uniforme
#
# Side effects:
# - Configura logging root
# - Expone funciones de logging de uso rápido
# -------------------------
def setup_logging() -> None:
    # Obtener el nivel de logging desde la variable de entorno LOG_LEVEL, por defecto DEBUG
    log_level_str = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    log_level = log_level_map.get(log_level_str, logging.DEBUG)

    uuid_filter = UUIDLogFilter()

    handler = RichHandler(
        rich_tracebacks=True,
        tracebacks_suppress=[logging]
    )
    handler.addFilter(uuid_filter)

    logging.basicConfig(
        level=log_level,
        format="[%(uuid)s] %(message)s",
        datefmt="[%X]",
        handlers=[handler]
    )

    # Ensure the level is set even if logging is already configured
    logging.getLogger().setLevel(log_level)


# -------------------------
# API pública de logging
# Responsabilidad:
# Proveer accesos directos a niveles
# de logging estandarizados
# -------------------------
def get_logger(name: str = __name__) -> dict[str, Callable]:
    logger = logging.getLogger(name)
    return {
        "info": logger.info,
        "debug": logger.debug,
        "warning": logger.warning,
        "error": logger.error,
        "critical": logger.critical,
    }


# Re-export funciones de observabilidad (si están disponibles serán no-op si falta dependencia)
try:
    from .otel import setup_observability, get_tracer, attach_flask_instrumentation  # type: ignore
except Exception:
    # Fallback minimal: definir stubs para mantener API
    def setup_observability(*_, **__):
        return None

    def get_tracer(*_, **__):
        class _Noop:
            def start_as_current_span(self, *a, **k):
                class _Ctx:
                    def __enter__(self):
                        return None

                    def __exit__(self, exc_type, exc, tb):
                        return False

                return _Ctx()

        return _Noop()

    def attach_flask_instrumentation(*_, **__):
        return None

# Re-export instrumentations
try:
    from .instrumentation import instrument_requests, instrument_sqlalchemy, instrument_all  # type: ignore
except Exception:
    def instrument_requests(*_, **__):
        return None

    def instrument_sqlalchemy(*_, **__):
        return None

    def instrument_all(*_, **__):
        return None

def get_request_uuid() -> str:
    if not hasattr(_request_uuid, "id"):
        _request_uuid.id = str(uuid.uuid4())
    return _request_uuid.id

def set_request_uuid(custom_uuid: str) -> None:
    _request_uuid.id = custom_uuid

def attach_logger_to_werkzeug():
    werkzeug_logger = logging.getLogger("werkzeug")
    app_logger = logging.getLogger("app")

    werkzeug_logger.handlers = app_logger.handlers
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.propagate = False

# -------------------------
# API LEGACY (compatibilidad)
# Responsabilidad:
# Mantener compatibilidad con imports existentes:
#   logger.logg_info(...)
# -------------------------
_logger = logging.getLogger("app")

logg_info = _logger.info
logg_debug = _logger.debug
logg_warning = _logger.warning
logg_error = _logger.error
logg_critical = _logger.critical

# -------------------------
# Bootstrap automático del logging
# -------------------------
setup_logging()
