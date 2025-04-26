from setuptools import setup, find_packages

setup(
    name='EngineProject',
    version='2.7.0',
    packages=find_packages('src'),
    package_dir={'':'src'},
    install_requires=[
        'Flask>=2.0,<3.0',
        'flask-socketio>=5.0,<6.0',
        'kafka-python>=2.0,<3.0',
        'pymodbus>=3.0,<4.0',
        'redis>=4.5,<5.0',
        'requests>=2.20,<3.0',
        'uvloop>=0.17,<1.0',
        'graphene>=3.0',
        'flask-graphql>=2.0',
        'flask-caching>=2.0',
        'grpcio>=1.50.0',
        'grpcio-tools>=1.50.0',
        'cryptography>=40.0.0',
    ],
    entry_points={
        'console_scripts': [
            'engine=app.run_async_engine:main',
        ],
    },
)
