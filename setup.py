#!/usr/bin/env python

from setuptools import setup

setup(name='minervaclient',
      version='1.0.0',
      description='Tools and Utilities that can be used to access McGill University\'s Minerva service',
      author='Ryan B Au',
      author_email='auryan898@gmail.com',
      url='https://github.com/nicholaspaun/minervaclient',
      # download_url='https://github.com/auryan898/nxt-python-tools/archive/0.1.tar.gz',
      keywords=['minerva','banner','mcgill','college','schedule'],
      packages=['minervaclient'],
      scripts=['scripts/minervac'],
      classifiers=[],
      install_requires=[
          'requests', 'beautifulsoup4', 'html5lib'
      ],
      license='MIT'
     )
