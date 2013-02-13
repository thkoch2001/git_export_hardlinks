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

# this context.py should be included by all tests
# idea from http://kennethreitz.com/repository-structure-and-python.html

import os
import shutil
import sys
import tempfile
import dulwich

source_tree_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_resources_path = os.path.join(source_tree_path, "test_resources")

sys.path.insert(0, source_tree_path)

_chdir_backup = None
_tmpdirs = []

def chdir(dir):
    global _chdir_backup
    if not _chdir_backup:
        _chdir_backup = os.path.abspath(os.curdir)
    os.chdir(str(dir))

def new_tmpdir(name):
    global _tmpdirs
    prefix='gbp_%s_' % name
    tmpdir=TmpDir(prefix)
    _tmpdirs.append(tmpdir)
    return tmpdir

def teardown():
    if _chdir_backup:
        os.chdir(_chdir_backup)
    for tmpdir in _tmpdirs:
        tmpdir.rmdir()
    del _tmpdirs[:]

class TmpDir(object):

    def __init__(self, suffix='', prefix='tmp'):
        self.path = tempfile.mkdtemp(suffix=suffix, prefix=prefix)

    def rmdir(self):
        if self.path and not os.getenv("TESTS_NOCLEAN"):
            shutil.rmtree(self.path)
            self.path = None

    def __repr__(self):
        return self.path

    def join(self, *args):
        return os.path.join(self.path, *args)

    def write(self, filename, content=""):
        fd = open(self.join(filename), "w")
        fd.write(content)
        fd.close()

def assertFileExists(self, filename):
    if(not os.path.exists(filename)):
        self.fail("File does not exist: %s" % filename)

def assertFileContains(self, filename, content):
    assertFileExists(self, filename)
    fd = open(filename)
    filecontent = fd.read()
    fd.close()
    if(not filecontent == content):
        self.fail("File %s does not contain:\n%r\nbut:\n%r" % (filename, content, filecontent))

def assertSameINode(self, file1, file2):
    stat1 = os.lstat(file1)
    stat2 = os.lstat(file2)
    if(not os.path.samestat(stat1, stat2)):
        self.fail("Files have different inodes:\n%s %s\n%s %s" % (stat1.st_ino, file1, stat2.st_ino, file2))
