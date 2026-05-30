"""Integración opcional con OpenTelemetry.

Este módulo intenta importar OpenTelemetry de forma perezosa.
Si no está disponible, las funciones expuestas son no-op para
mantener compatibilidad con entornos que no instalen las dependencias.
"""
from __future__ import annotations

import os
import logging
from typing import Tuple, Optional

_otel_available = True
try:
    from opentelemetry import trace, metrics, propagators
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
except Exception:  # pragma: no cover - optional dependency
    _otel_available = False


logger = logging.getLogger(__name__)


def _format_hex_id(value: int) -> str:
    if value is None:
        return ""
    try:
        return format(value, '032x') if isinstance(value, int) else str(value)
    except Exception:
        return str(value)


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """Return (trace_id, span_id) as hex strings if OpenTelemetry is active.

    If OTEL is not installed or no current span, returns (None, None).
    """
    if not _otel_available:
        return None, None

    span = trace.get_current_span()
    if not span or not span.get_span_context().is_valid:
        return None, None

    ctx = span.get_span_context()
    trace_id = _format_hex_id(ctx.trace_id)
    span_id = _format_hex_id(ctx.span_id)
    return trace_id, span_id


def setup_observability(service_name: str | None = None) -> None:
    """Configure TracerProvider + OTLP exporter based on environment variables.

    This is optional: if OpenTelemetry packages are not installed, this is no-op.
    """
    if not _otel_available:
        logger.debug("OpenTelemetry not available; setup_observability is no-op")
        return

    # Resource
    service = service_name or os.environ.get('OTEL_SERVICE_NAME') or os.environ.get('SERVICE_NAME')
    resource = Resource.create({"service.name": service or "logger-tracker"})

    # Tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Exporter selection via OTLP endpoint env var
    otlp_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')
    exporter = None
    if otlp_endpoint:
        try:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        except Exception:
            exporter = None

    if exporter is None:
        exporter = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    logger.info("OpenTelemetry tracer configured (exporter=%s)", exporter.__class__.__name__)


def get_tracer(name: str = __name__):
    if not _otel_available:
        def _noop_tracer(*_, **__):
            class _Noop:
                def start_as_current_span(self, *a, **k):
                    class _Ctx:
                        def __enter__(self):
                            return None

                        def __exit__(self, exc_type, exc, tb):
                            return False

                    return _Ctx()

            return _Noop()

        return _noop_tracer()
    return trace.get_tracer(name)


def attach_flask_instrumentation(app) -> None:
    """Attach automatic instrumentation for Flask if available."""
    if not _otel_available:
        logger.debug("OpenTelemetry Flask instrumentation unavailable")
        return

    try:
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask instrumented with OpenTelemetry")
    except Exception as e:
        logger.exception("Failed to instrument Flask: %s", e)
