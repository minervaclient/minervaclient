#!/usr/bin/env python

from setuptools import setup
# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README')) as f:
    long_description = f.read()

setup(name='minervaclient',
    version='1.3.0',
    description='Tools and Utilities that can be used to access McGill University\'s Minerva service',
    author='Ryan B Au',
    author_email='auryan898@gmail.com',
    url='https://github.com/auryan898/minervaclient',
    download_url='https://github.com/auryan898/minervaclient/archive/master.zip',
    keywords=['minerva','banner','mcgill','college','schedule'],
    packages=['minervaclient','minervaclient3'],
    scripts=['scripts/minervac','scripts/minervac.bat'],
    classifiers=[],
    install_requires=[
        'requests', 'beautifulsoup4','future','icalendar','pyyaml','EasySettings'
    ],
    dependency_links=[
        'https://github.com/frispete/keyrings.cryptfile/archive/v1.2.1.zip',
    ],
    extras_require={
        'full_cli_support':['keyring','keyrings.cryptfile'],
        'html5_parse':['html5lib']
    },
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data = True
    )
print( "The packages 'html5lib' and 'keyring' are needed for full support")
