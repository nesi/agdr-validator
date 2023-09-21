import pathlib
from setuptools import find_packages, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text().splitlines()

# This call to setup() does all the work
setup(
    name="agdrvalidator",
    version="0.0.1",
    description="Spreadsheet Validation App",
    long_description=README,
    long_description_content_type="text/markdown",
    url="",
    author="Eirian Perkins",
    author_email="eirian.perkins@nesi.org.nz",
    license="Copyright NeSI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    packages=find_packages("src"),
    package_dir = {"": "src"},
    # from https://stackoverflow.com/a/57749691
    package_data = {'dictionary' : ['data/dicionaries/i*.json']},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    entry_points={
        "console_scripts": [
            "agdrvalidator=agdrvalidator.__main__:main",
        ]
    },
)