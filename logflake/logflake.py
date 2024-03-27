import json
import threading
import requests
from enum import Enum
from queue import Queue
from time import sleep
from logging import exception


class LogLevels(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'
    FATAL = 'FATAL'
    EXCEPTION = 'EXCEPTION'


class Queues(Enum):
    LOGS = 'logs'
    PERFORMANCES = 'performances'


class Servers(Enum):
    PRODUCTION = 'https://app.logflake.io'
    TEST = 'https://app-test.logflake.io'


class LogFlakeException(Exception):
    pass


class PendingLog:
    def __init__(self, queue_name, json_string):
        self.queue_name = queue_name
        self.json_string = json_string
        self.retries = 0


class LogObject:
    def __init__(self, level, hostname, content, correlation=None, parameters=None, label=None, duration=None):
        self.level = level
        self.hostname = hostname
        self.content = content
        self.correlation = correlation
        self.parameters = parameters
        self.label = label
        self.duration = duration

    def to_string(self):
        return json.dumps(self.__dict__)


class PerformanceCounter:
    def __init__(self, log_flake, label):
        self.log_flake = log_flake
        self.label = label
        self.start_time = None

    def __enter__(self):
        self.start_time = time()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.start_time is not None:
            duration = time() - self.start_time
            self.log_flake.send_performance(self.label, duration)


class LogFlake:
    def __init__(self, app_id, log_flake_server=Servers.PRODUCTION.value):
        if not app_id:
            raise LogFlakeException("appId missing")

        self.server = log_flake_server.rstrip('/')
        self._hostname = None
        self.app_id = app_id

        self._logs_queue = Queue()
        self._process_logs = threading.Event()
        self._logs_processor_thread = threading.Thread(target=self._logs_processor)
        self._logs_processor_thread.start()

        self.failed_post_retries = 3
        self.post_timeout_seconds = 3
        self.is_shutting_down = False

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        self.is_shutting_down = True
        self._logs_processor_thread.join()

    def _logs_processor(self):
        self.send_log(LogLevels.DEBUG, f"LogFlake started on {self.get_hostname()}")
        self._process_logs.wait()

        while not self._logs_queue.empty():
            log = self._logs_queue.get()
            log.retries += 1

            success = self._post(log.queue_name, log.json_string)
            if not success and log.retries < self.failed_post_retries:
                self._logs_queue.put(log)

            self._process_logs.clear()
            if self._logs_queue.empty() and not self.is_shutting_down:
                self._process_logs.wait()

    def _post(self, queue_name, json_string):
        if queue_name not in (Queues.LOGS.value, Queues.PERFORMANCES.value):
            return False

        try:
            url = f"{self.server}/api/ingestion/{self.app_id}/{queue_name}"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, data=json_string, headers=headers, timeout=self.post_timeout_seconds)
            return response.status_code == 200
        except Exception:
            return False

    def send_log(self, content, parameters=None):
        self.send_log(LogLevels.DEBUG, content, parameters)

    def send_log(self, level, content, parameters=None):
        self.send_log(level, None, content, parameters)

    def send_log(self, level, correlation, content, parameters=None):
        log_object = LogObject(
            level=level.value,
            hostname=self.get_hostname(),
            content=content,
            correlation=correlation,
            parameters=parameters
        )
        json_string = log_object.to_string()

        self._logs_queue.put(PendingLog(Queues.LOGS.value, json_string))
        self._process_logs.set()

    def send_exception(self, exception, correlation=None):
        additional_trace = ""
        if exception.data:
            additional_trace = f"{Environment.NewLine}Data:{Environment.NewLine}{json.dumps(exception.data, indent=2)}"

        log_object = LogObject(
            level=LogLevels.EXCEPTION.value,
            hostname=self.get_hostname(),
            content=f"{exception}{additional_trace}",
            correlation=correlation
        )
        json_string = log_object.to_string()

        self._logs_queue.put(PendingLog(Queues.LOGS.value, json_string))
        self._process_logs.set()

    def send_performance(self, label, duration):
        log_object = LogObject(
            label=label,
            duration=duration
        )
        json_string = log_object.to_string()

        self._logs_queue.put(PendingLog(Queues.PERFORMANCES.value, json_string))
        self._process_logs.set()

    def measure_performance(self, label):
        return PerformanceCounter(self, label)

    def set_hostname(self, hostname=None):
        self._hostname = None if not hostname else hostname

    def get_hostname(self):
        return self._hostname or Environment.MachineName


# Esempio di utilizzo:
log_flake = LogFlake(app_id='your_app_id', log_flake_server=Servers.PRODUCTION.value)
log_flake.send_log(content='This is a test log')
log_flake.send_performance(label='API_Request', duration=5)
