<h1 align="center">LogFlake Client Python <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-blue.svg?cacheSeconds=2592000" /></h1>

> This repository contains the sources for the client-side components of the LogFlake product suite for applications logs and performance collection for Python applications.

<h3 align="center">🏠 [LogFlake Website](https://logflake.io) |  🔥 [CloudPhoenix Website](https://cloudphoenix.it)</h3>

## Downloads

|                         PyPI Package Name                          |                                   Version                                   |                          Downloads                           |
|:------------------------------------------------------------------:|:---------------------------------------------------------------------------:|:------------------------------------------------------------:|
| [LogFlake.Client.Python](https://pypi.org/project/logflake/1.0.0/) |          ![PyPI - Version](https://img.shields.io/pypi/v/logflake)          | ![PyPI - Downloads](https://img.shields.io/pypi/dm/logflake) |

## Usage

Retrieve your _application-key_ from Application Settings in LogFlake UI.

```python
from logflake import logflake

logger = logflake.LogFlake('application-key')
logger.send_log(logflake.LogLevels.DEBUG, None, 'Hello World')

logger.shutdown()
```
