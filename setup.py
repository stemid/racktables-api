import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Racktables API",
    version = "0.20.8",
    author = "Stefan Midjich",
    author_email = "swehack@gmail.com",
    description = ("Library to provide an API for Racktables database."),
    license = "GPLv2",
    keywords = "racktables rack inventory API",
    url = "https://github.com/stemid/racktables-api",
    packages = ['rtapi'],
    long_description = read('README.md'),
    classifiers = [
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Libraries",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
)
