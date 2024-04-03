from logflake import logflake
from random import randint
from time import time
from time import sleep

# initialize logger with AppID and server optionally address
logger = logflake.LogFlake('65b3cbbbf9ff405014e88230', logflake.Servers.TEST.value)

# send debug log
logger.send_log(logflake.LogLevels.DEBUG, None, 'TEST Simple')

# send logs with correlation and severity
correlation = "PY" + str(time())
logger.send_log(logflake.LogLevels.INFO, correlation, 'TEST Correlation INFO')
logger.send_log(logflake.LogLevels.WARN, correlation, 'TEST Correlation WARN')
logger.send_log(logflake.LogLevels.ERROR, correlation, 'TEST Correlation ERROR')
logger.send_log(logflake.LogLevels.FATAL, correlation, 'TEST Correlation FATAL')

# send logs with parameters
logger.send_log(logflake.LogLevels.DEBUG, None, 'TEST Parameters', {
  'param_string': 'string value',
  'param_numeric': 1234.56,
  'param_bool': True,
  'param_json': {
    'nested_string': 'string value',
    'nested_numeric': 1234.56,
    'nested_bool': True
  }
})

# send exceptions
try:
    print(x)
except:
    logger.send_exception()
    pass

# send performance metrics
for x in range(100):
    logger.send_performance('Testing', randint(0, 1000))

# measure performance with a counter
perf = logger.measure_performance('Test')
sleep(randint(100,3000)/1000)
perf.stop()

# gracefully shutdown processing thread
logger.shutdown()
