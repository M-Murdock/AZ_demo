from setuptools import find_packages
from setuptools import setup

setup(
    name='AZ_demo',
    version='0.0.0',
    packages=find_packages(
        include=('AZ_demo', 'AZ_demo.*')),
)
