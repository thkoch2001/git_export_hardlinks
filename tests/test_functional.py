
from . import context

from dulwich.repo import Repo
import unittest
import os
import os.path
import git_export_hardlinks
from git_export_hardlinks import ExportedTree

class TestFunctional(unittest.TestCase):

    # the tree_shas of all commits from newest to oldest
    tree_log = ["53c7060628b9bb17553dbbdefa9c875437ff0396",
                "11cbc0a257d3f2c7631066b812710427bb8457e4",
                "fbbbe80634adab189ee4721b2127236a40a6ca49",
                "11cbc0a257d3f2c7631066b812710427bb8457e4",
                "d7b458537d4460d149a331bccbe4aa7131622de9",
                "c49897f29f9819a0ab6850d7e22443508a1a29d5"]

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
        git_export_hardlinks.export(self.repo, self.tree_log[0], repr(self.tmp_dir))
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
        git_export_hardlinks.export(self.repo, self.tree_log[1], parent_dir)
        git_export_hardlinks.export(self.repo, self.tree_log[0], head_dir, [ExportedTree(path=parent_dir, tree=self.tree_log[1])])
        self.assertSameINode(self.tmp_dir.join("head/dir/b"), self.tmp_dir.join("head/dir2/a"))
        self.assertSameINode(self.tmp_dir.join("head/dir2/b"), self.tmp_dir.join("head/dir3/subdir/fdsa"))

    def test_raises_ioerror_on_non_empty_target(self):
        self.tmp_dir.write("touched")
        with self.assertRaises(IOError):
            git_export_hardlinks.export(None, None, repr(self.tmp_dir))

    assertFileExists = context.assertFileExists
    assertFileContains = context.assertFileContains
    assertSameINode = context.assertSameINode
