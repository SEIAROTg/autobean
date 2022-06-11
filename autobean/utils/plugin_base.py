from autobean.utils import error_lib


class PluginBase:
    _error_logger: error_lib.ErrorLogger

    def __init__(self) -> None:
        self._error_logger = error_lib.ErrorLogger()
