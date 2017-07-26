##############################################################################
#
# Copyright (c) 2008-2011 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

def _read(filename):
    try:
        with open(os.path.join(here, filename)) as f:
            return f.read()
    except IOError:
        return ''

README = _read('README.rst')
CHANGES = _read('CHANGES.rst')

install_requires = [
    'pyramid',
    'zodburi',
]

docs_extras = ['Sphinx', 'pylons-sphinx-themes']
testing_extras = ['nose', 'coverage', 'pyramid_tm', 'webtest']

setup(name='pyramid_zodbconn',
      version='0.8.1',
      description=('Provide integration betwen Pyramid and ZODB'),
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "License :: Repoze Public License",
      ],
      keywords='wsgi pylons pyramid zodb zodbconn',
      author="Chris McDonough",
      author_email="pylons-devel@googlegroups.com",
      url="http://docs.pylonsproject.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=install_requires,
      test_suite="pyramid_zodbconn",
      entry_points='',
      extras_require={
          'testing':testing_extras,
          'docs':docs_extras,
      },
)
