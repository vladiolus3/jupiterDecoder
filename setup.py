from setuptools import setup

setup(
    name='py-jup-decoder',
    version='1.0.0',
    description='Copied from https://github.com/jup-ag/instruction-parser',
    url='https://github.com/vladiolus3/jupiterDecoder',
    packages=['src'],
    install_requires=['solana', 'solders', 'anchorpy', 'aiohttp', 'base58'],
)
