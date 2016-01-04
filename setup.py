#!/usr/bin/env python
# Encoding: utf-8
# See: <http://docs.python.org/distutils/introduction.html>
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name             = "cooker",
    version          = '0.1.0',
    description      = "Ansible-like functionality with Fabric",
    author           = "Kheshav Sewnundun",
    author_email     = "kheshavsewnundun@gmail.com",
    url              = "http://github.com/",
    keywords         = ["fabric", "ansible", "ssh",],
    install_requires = ["fabric","ansible",],
    package_dir      = {"":"src"},
    py_modules       = ["cooker"],
    license          = "BSD License",
    classifiers      = [
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Utilities"
    ],
)

