from setuptools import setup

setup(
    name='logflake',
    version='1.0.0',
    description='LogFlake Python Client',
    license='MIT',
    packages=['logflake'],
    author='CloudPhoenix Srl',
    author_email='info@cloudphoenix.it',
    keywords=['logflake'],
    url='https://github.com/CloudPhoenix/logflake-client-python',
    install_requires=[
        'requests'
    ]
)