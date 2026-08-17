> [!WARNING]
> **This project has been discontinued.**
>
> LogFlake was decommissioned in August 2026. This repository is archived and read-only:
> it receives no further development, bug fixes or security updates.
> The published package is deprecated — please do not use it in new projects.

<h1 align="center">LogFlake Client Python</h1>

> This repository contains the sources for the client-side components of the LogFlake product suite for applications logs and performance collection for Python applications.

<h3 align="center">🏠 <a href="https://logflake.io">LogFlake Website</a> |  🔥 <a href="https://cloudphoenix.it">CloudPhoenix Website</a></h3>

## Downloads

|                      PyPI Package Name                       |                                   Version                                   |                          Downloads                           |
|:------------------------------------------------------------:|:---------------------------------------------------------------------------:|:------------------------------------------------------------:|
| [LogFlake.Client.Python](https://pypi.org/project/logflake/) |          ![PyPI - Version](https://img.shields.io/pypi/v/logflake)          | ![PyPI - Downloads](https://img.shields.io/pypi/dm/logflake) |

## Usage

Retrieve your _application-key_ from Application Settings in LogFlake UI.

```python
from logflake import logflake

logger = logflake.LogFlake('application-key')
logger.send_log(logflake.LogLevels.DEBUG, None, 'Hello World')

logger.shutdown()
```

### Use logging handler example

```python
LOGGING = {
    "version": 1,
    "formatters": {
        "logflake": {
            "()": "django.utils.log.ServerFormatter",
            "format": f"%(name)s %(module)s.%(funcName)s() %(message)s",
        },
    },
    "handlers": {
        "logflake": {
            "class": "logflake.logflake.LogFlakeHandler", # REQUIRED
            "app_id": "application-key",                  # REQUIRED
            "formatter": "logflake",                      # OPTIONAL: Use custom formatter
            "server": "https://app.logflake.io",          # OPTIONAL: Use custom logging server
            "level": logging.ERROR,                       # OPTIONAL: Set minimum severity
        }
    },
    "root": {
        "handlers": ["logflake"], # REQUIRED
    },
}
```
