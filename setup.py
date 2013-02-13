#!/usr/bin/env python

# Copyright 2013 Thomas Koch <thomas@koch.ro>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from distutils.core import setup
import sys
from os.path import dirname, join, abspath

sys.path.insert(0, dirname(abspath(__file__)))

from git_export_hardlinks import DESCRIPTION, LONG_DESCRIPTION, EPILOG

setup(
  name="git_export_hardlink",
  version="0.1.0",
  author="Thomas Koch",
  author_email="thomas@koch.ro",
  url="https://github.com/thkoch2001/git_export_hardlinks",
  keywords="git deployment".split(),
  requires = ["dulwich (>=0.8.6)"],
  scripts = ["scripts/git_export_hardlinks"],
  description=DESCRIPTION,
  long_description=LONG_DESCRIPTION + "\n\n" + EPILOG,
  classifiers=[ # http://pypi.python.org/pypi?:action=list_classifiers
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    # TODO "Programming Language :: Python :: 3",
    "License :: OSI Approved :: Apache Software License",
    "Environment :: Console",
    "Intended Audience :: System Administrators",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Version Control",
    "Topic :: System :: Software Distribution",
    "Development Status :: 3 - Alpha"
  ],
#  packages=[?]
  py_modules=['git_export_hardlinks']
)
