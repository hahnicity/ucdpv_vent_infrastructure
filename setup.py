from setuptools import setup, find_packages

__version__ = "1.0"


setup(
    name="ucdpv",
    author="Edward Guo, Gregory Rehm",
    version=__version__,
    description="UCD Pulminary Ventilator Project",
    packages=find_packages(),
    package_data={"*": ["*.html"]},
    install_requires=[
        "ansible<2.0",
        "cryptography",
        "Flask-WTF",
        "mock",
        "netifaces",
        "nose",
        "pyserial",
        "sqlalchemy",
    ],
    entry_points={
    }
)
