"""
setup
~~~~~

Script for creating the statuswriter package.
"""
import setuptools

from statuswriter import __version__


with open('requirements.txt') as fh:
    reqs = fh.readlines()

with open('README.rst') as fh:
    long_desc = fh.read()

setuptools.setup(
    name='statuswriter',
    version=__version__.__version__,
    description=__version__.__description__,
    long_description=long_desc,
    long_description_content_type='text/x-rst',
    url='https://github.com/pji/statuswriter',
    author=__version__.__author__,
    install_requires=reqs,
    author_email='pji@mac.com',
    packages=setuptools.find_packages(),
    python_requires='>=3.9',
    zip_safe=False
)
