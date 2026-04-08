from setuptools import setup, find_packages

setup(
    name="weather-flask-app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask",
        "requests",
    ],
)
