import logging


class RunIdFilter(logging.Filter):
    """Inject run_id into every log record so the formatter can reference %(run_id)s."""

    _run_id: str = "unset"

    @classmethod
    def set_run_id(cls, run_id: str) -> None:
        cls._run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self._run_id
        return True
