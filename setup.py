from setuptools import setup, find_packages

DESCRIPTION = 'm3u8 playlist downloader'
VERSION = "0.5.0"


with open("README.md") as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name="m3u8dl",
    version=VERSION,
    zip_safe=False,
    author="Kevin Rohan Vaz",
    author_email="excalibur.krv@gmail.com",
    maintainer='Kevin Rohan Vaz',
    maintainer_email='excalibur.krv@gmail.com',
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/excalibur-kvrv/m3u8-dl",
    packages=find_packages(),
    install_requires=[
        "hyper==0.7.0",
        "requests==2.26.0",
        "tqdm==4.62.3"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
