
from . import context

from dulwich.repo import Repo
import unittest
import os
import os.path
import git_export_hardlinks
from git_export_hardlinks import ExportedTree, _resolve_treeish

class TestFunctional(unittest.TestCase):

    # the shas of all commits from newest to oldest
    log = ["379129ffe13bf3300f9a507a9ed269ce4d7fec62",
           "db880f831aab007fcbfdce3a63edc95fd8f18500",
           "5806ddc55fac7cae1bcd6256495b829bf8137a0b",
           "f4d1365f6e1496ff19c5507081750772617ed6df",
           "cf1e1969c0531759836530a44ac2e17ce69278ef",
           "9dd7f8c4764ef753bbad595199fd9068b60d77f2"]

    head_files = [ "a", "b", "c", "dir/a", "dir/b", "dir2/a", "dir2/b",
                   "dir3/subdir/ephemeral_new",
                   "dir3/subdir/fdsa",
                   "dir3/subdir2/fdsa",
                   "dir3/subdir2/uuj"]

    def setUp(self):
        self.repo = Repo(os.path.join(context.test_resources_path, "bare_git_repo"))
        self.tmp_dir = context.new_tmpdir(__name__)

    def tearDown(self):
        context.teardown()

    def test_export_head(self):
        git_export_hardlinks.export(self.repo, self.log[0], repr(self.tmp_dir))
        # test that all files are there
        for exported_file in self.head_files:
            self.assertFileExists(self.tmp_dir.join(exported_file))
        # test that no additional files are there
        for dirpath, _, filenames in os.walk(repr(self.tmp_dir)):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(dirpath, filename), repr(self.tmp_dir))
                self.assertTrue(rel_path in self.head_files)

        self.assertFileContains(self.tmp_dir.join("dir3/subdir/ephemeral_new"), "ephemeral\n")

    def test_equal_files_in_head_have_same_inode(self):
        parent_dir = self.tmp_dir.join("parent")
        head_dir = self.tmp_dir.join("head")

        git_export_hardlinks.export(self.repo, self.log[1], parent_dir)
        git_export_hardlinks.export(self.repo, self.log[0], head_dir, [ExportedTree(path=parent_dir, tree=self.log[1])])
        self.assertSameINode(self.tmp_dir.join("head/dir/b"), self.tmp_dir.join("head/dir2/a"))
        self.assertSameINode(self.tmp_dir.join("head/dir2/b"), self.tmp_dir.join("head/dir3/subdir/fdsa"))

    def test_raises_ioerror_on_non_empty_target(self):
        self.tmp_dir.write("touched")
        with self.assertRaises(IOError):
            git_export_hardlinks.export(None, None, repr(self.tmp_dir))

    def test_export_all_trees(self):
        already_exported = []
        for tree in reversed(self.log):
            target = self.tmp_dir.join(tree)
            git_export_hardlinks.export(self.repo, tree, target, reversed(already_exported))
            already_exported.append(ExportedTree(path=target, tree=tree))

        head = lambda _: os.path.join(already_exported[-1].path, _)
        parent = lambda x,y: os.path.join(already_exported[-1-x].path, y)

        self.assertSameINode(head("dir3/subdir/ephemeral_new"), parent(2, "dir/ephemeral"))
        self.assertSameINode(parent(2, "dir/b"), parent(2, "dir2/a"))

    assertFileExists = context.assertFileExists
    assertFileContains = context.assertFileContains
    assertSameINode = context.assertSameINode
