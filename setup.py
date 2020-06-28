import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="pymeritrade",
    version="0.1.0",
    author="Shrivu Shankar",
    author_email="shrivu1122@gmail.com",
    description="A Python API for TD Ameritrade.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sshh12/pymeritrade",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
