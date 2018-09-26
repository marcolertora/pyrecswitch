import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyrecswitch",
    version="1.0.2",
    author="Marco Lertora",
    author_email="marco.lertora@gmail.com",
    description="A pure-python interface for controlling Ankuoo RecSwitch MS6126",
    license="AGPLv3+",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/marcolertora/pyrecswitch",
    packages=setuptools.find_packages(),
    install_requires=[
            "pycryptodome>=3.6.6",
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ),
)