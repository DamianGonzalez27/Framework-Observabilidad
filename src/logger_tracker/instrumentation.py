"""Instrumentaciones opcionales para integrarse con OpenTelemetry.

Este módulo intenta aplicar instrumentaciones disponibles de forma segura.
Si las dependencias no están presentes, las funciones son no-op.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_requests_available = True
_sqlalchemy_available = True
try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
except Exception:  # pragma: no cover - optional
    _requests_available = False

try:
    # SQLAlchemy instrumentation supports both engine and session
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
except Exception:  # pragma: no cover - optional
    _sqlalchemy_available = False


def instrument_requests() -> None:
    """Instrumentar librería `requests` si está disponible."""
    if not _requests_available:
        logger.debug("requests instrumentation not available")
        return
    try:
        RequestsInstrumentor().instrument()
        logger.info("Requests instrumented for OpenTelemetry")
    except Exception:
        logger.exception("Failed to instrument requests")


def uninstrument_requests() -> None:
    if not _requests_available:
        return
    try:
        RequestsInstrumentor().uninstrument()
        logger.info("Requests uninstrumented")
    except Exception:
        logger.exception("Failed to uninstrument requests")


def instrument_sqlalchemy(engine_or_url: Optional[object] = None) -> None:
    """Instrumentar SQLAlchemy.

    Si se pasa `engine_or_url`, algunos adaptadores pueden usarlo para instrumentar
    (según la versión del instrumentor); en caso contrario se intenta la instrumentación global.
    """
    if not _sqlalchemy_available:
        logger.debug("sqlalchemy instrumentation not available")
        return
    try:
        if engine_or_url is None:
            SQLAlchemyInstrumentor().instrument()
        else:
            # Newer instrumentors accept engine= or engine_and_session=True
            try:
                SQLAlchemyInstrumentor().instrument(engine=engine_or_url)
            except TypeError:
                # Fallback to global instrument
                SQLAlchemyInstrumentor().instrument()

        logger.info("SQLAlchemy instrumented for OpenTelemetry")
    except Exception:
        logger.exception("Failed to instrument SQLAlchemy")


def instrument_all(engine_or_url: Optional[object] = None) -> None:
    """Convenience: instrumenta requests y sqlalchemy (si están instalados)."""
    instrument_requests()
    instrument_sqlalchemy(engine_or_url)
