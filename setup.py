from setuptools import setup
from Cython.Build import cythonize
import os

path = os.path.join("core", "utils", "write_file_no_gil.pyx")

setup(
    name="c_file_write",
    ext_modules=cythonize(path),
    zip_safe=False,
)
