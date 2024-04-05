
import os
import threading
from logging import Handler
from json import dumps
from enum import Enum
from queue import Queue
from sys import exc_info
from traceback import format_exc
from platform import node
from time import time
from requests import post


class LogLevels(Enum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    FATAL = 4
    EXCEPTION = 5


class Queues(Enum):
    LOGS = 'logs'
    PERFORMANCES = 'perf'


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
    def __init__(self, level=None, content=None, hostname=None, correlation=None, params=None, label=None, duration=None):
        self.level = level
        self.content = content
        self.hostname = hostname
        self.correlation = correlation
        self.params = params
        self.label = label
        self.duration = duration

    def to_string(self):
        return dumps(self.__dict__)


class PerformanceCounter:
    def __init__(self, log_flake, label):
        self.instance = log_flake
        self.label = label
        self.start_time = time()

    def stop(self):
        duration = time() - self.start_time
        self.instance.send_performance(self.label, duration)


class LogFlake:
    def __init__(self, app_id, log_flake_server=Servers.PRODUCTION.value):
        if not app_id:
            raise LogFlakeException("appId missing")

        self.server = log_flake_server.rstrip('/')
        self._hostname = node()
        self.app_id = app_id
        self._logs_queue = Queue()
        self._process_logs = threading.Event()
        self.failed_post_retries = 3
        self.post_timeout_seconds = 3
        self.is_shutting_down = False
        self._logs_processor_thread = threading.Thread(target=self._logs_processor)
        self._logs_processor_thread.start()

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        self.is_shutting_down = True
        self._logs_processor_thread.join()

    def _logs_processor(self):
        self.send_log(level=LogLevels.DEBUG, correlation=None, content=f"LogFlake started on {self.get_hostname()}")
        self._process_logs.wait()

        while not self._logs_queue.empty():
            log = self._logs_queue.get()
            log.retries += 1

            success = self._post(log.queue_name, log.json_string)
            if not success and log.retries < self.failed_post_retries:
                self._logs_queue.put(log)

            self._process_logs.clear()
            if self._logs_queue.empty():
                if self.is_shutting_down:
                    break
                else:
                    self._process_logs.wait()

    def _post(self, queue_name, json_string):
        if queue_name not in (Queues.LOGS.value, Queues.PERFORMANCES.value):
            return False

        try:
            url = f"{self.server}/api/ingestion/{self.app_id}/{queue_name}"
            headers = {'Content-Type': 'application/json'}
            response = post(url, data=json_string, headers=headers, timeout=self.post_timeout_seconds)
            return response.status_code == 200
        except:
            return False

    def send_log(self, level, correlation, content, params=None):
        obj = LogObject(
            level=level.value,
            hostname=self.get_hostname(),
            content=content,
            correlation=correlation,
            params=params
        )
        json_string = obj.to_string()

        self._logs_queue.put(PendingLog(Queues.LOGS.value, json_string))
        self._process_logs.set()

    def send_exception(self, correlation=None):
        obj = LogObject(
            level=LogLevels.EXCEPTION.value,
            hostname=self.get_hostname(),
            content=f"{exc_info()[1]}{os.linesep}{format_exc()}",
            correlation=correlation
        )
        json_string = obj.to_string()

        self._logs_queue.put(PendingLog(Queues.LOGS.value, json_string))
        self._process_logs.set()

    def send_performance(self, label, duration):
        obj = LogObject(
            label=label,
            duration=duration
        )
        json_string = obj.to_string()

        self._logs_queue.put(PendingLog(Queues.PERFORMANCES.value, json_string))
        self._process_logs.set()

    def measure_performance(self, label):
        return PerformanceCounter(self, label)

    def set_hostname(self, hostname=None):
        self._hostname = None if not hostname else hostname

    def get_hostname(self):
        return self._hostname or node()


def is_jsonable(x):
    try:
        dumps(x)
        return True
    except:
        return False


class LogFlakeHandler(Handler):
    def __init(self, app_id, log_flake_server=Servers.PRODUCTION.value) -> None:
        self.log_flake = LogFlake(app_id, log_flake_server)
        self.log_level_mapping = {
            'DEBUG': LogLevels.DEBUG,
            'INFO': LogLevels.INFO,
            'WARNING': LogLevels.WARN,
            'ERROR': LogLevels.ERROR,
            'CRITICAL': LogLevels.FATAL,
            'EXCEPTION': LogLevels.EXCEPTION
        }

    def emit(self, record):
        try:
            self.format(record)

            if record.exc_info:
                self.log_flake.send_exception()

            self.log_flake.send_log(
                level=self.log_level_mapping[record.levelname],
                content=self.format(record),
                correlation=None,
                params=record.args if is_jsonable(record.args) else None
            )

        except:
            self.log_flake.send_exception()
            self.handleError(record)
