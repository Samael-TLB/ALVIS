from setuptools import setup
from Cython.Build import cythonize
import numpy
'graph.pyx'
setup(
    ext_modules=cythonize('quadtree.pyx',annotate=True,),
    include_dirs = [numpy.get_include()],
    )
