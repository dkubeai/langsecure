import threading
from pathlib import Path
from typing import IO, Sequence
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from langfuse import Langfuse
import json

trace.set_tracer_provider(TracerProvider())
processed_spans = {} # to avoid duplicate spans during export because of threading?

class FileSpanExporter(SpanExporter):
    def __init__(
        self,
        file_path: str | Path | IO,
    ) -> None:
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path.expanduser()
        self._lock = threading.Lock()
        self._file: IO | None = None

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        global processed_spans
        with self._lock:
            if not self._file:
                if isinstance(self.file_path, Path):
                    self._file = self.file_path.open("a")
                else:
                    self._file = self.file_path
            for span in spans:
                if span.context.span_id in processed_spans:
                    continue
                event = json.loads(span.to_json(indent=None))
                self._file.write(
                    f'{event["start_time"]} {event["name"]} {event["events"][0]["attributes"]["output"]}\n'
                )
                processed_spans[span.context.span_id] = True
            self._file.flush()
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self) -> None:
        with self._lock:
            if self._file:
                self._file.flush()
                if self._file is not self.file_path:
                    # don't close the file if it was passed in
                    self._file.close()


class LangsecureSpan:
    def __init__(self, tracer, parent_ctx, name) -> None:
        self.tracer = tracer
        self.name = name
        self.generation = self.event
        self.parent_ctx = parent_ctx

    def event(self, name, output=[], **kwargs):
        with self.tracer.start_span(self.name, context=self.parent_ctx) as span:
            span.add_event(name, attributes={"output": output})

    def span(self, name):
        return LangsecureSpan(self.tracer, self.parent_ctx, name)


class LangsecureTrace:
    def __init__(self, name) -> None:
        self.tracer = trace.get_tracer(name)
        self.root_context = trace.set_span_in_context(self.tracer.start_span(name))

    def span(self, name):
        return LangsecureSpan(self.tracer, self.root_context, name)

    def generation(self, name, output=[], **kwargs):
        with self.tracer.start_span(name, context=self.root_context) as span:
            span.add_event(name, attributes={"output": output})


class LangsecureTracer:
    langfuse: Langfuse = None

    def __init__(self, tracking_server) -> None:
        if isinstance(tracking_server, Path):
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(FileSpanExporter(tracking_server))
            )
        else:
            self.langfuse = Langfuse(tracking_server)

    def trace(self, name):
        if self.langfuse:
            return self.langfuse.trace(name=name)
        return LangsecureTrace(name)
