from setuptools import setup, find_packages

__version__ = "1.0"


setup(
    name="ucdpv",
    author="Monica Lieng, Edward Guo, Gregory Rehm",
    version=__version__,
    description="UCD Pulminary Ventilator Project",
    packages=find_packages(),
    package_data={"*": ["*.html"]},
    install_requires=[
        "ansible",
        "cryptography",
        "Flask-WTF",
        "mock",
        "netifaces",
        "nose",
        "pyserial",
    ],
    entry_points={
    }
)
