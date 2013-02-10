#!python

from dulwich.repo import Repo
from collections import namedtuple
import os
import os.path
import stat
import argparse

ExportedTree = namedtuple('ExportedTree', 'tree, path')

def parse_args():
    class SplitLinkOption(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            exported_trees = []
            for value in values:
                tree, path = value.split(',', 1)
                exported_trees.append(ExportedTree(tree=tree, path=os.path.abspath(path)))
            setattr(namespace, self.dest, exported_trees)

    parser = argparse.ArgumentParser(
        description="git export that reuses already existing exports and hardlinks files from them.",
        epilog="Be aware of the dangers of hardlinks. Hardlinks on linux do not have copy-on-write semantics!"
    )
    parser.add_argument("-l", "--link", help="existing export to hardlink from: TREE_SHA1,PATH. Newest first",
                        action=SplitLinkOption, nargs='*'
                        )

    parser.add_argument("treeish", help="treeish to export TODO: resolve to TREE_SHA1", nargs=1)
    parser.add_argument("target", help="location where to export to", nargs=1)

    return parser.parse_args()


def create_exported_tree_map(repo, tree_sha, path=""):
    id2path={}
    tree = repo.tree(tree_sha)
    for name, mode, sha in tree.iteritems():
        if stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            id2path[(mode, sha)] = os.path.join(path, name)
        elif stat.S_ISDIR(mode):
            id2path.update(create_exported_tree_map(repo, sha, os.path.join(path, name)))
    # ignore submodules
    return id2path

def tree_iterator(repo, tree_sha, path=""):
    tree = repo.tree(tree_sha)
    for entry in tree.iteritems():
        mode = entry.mode
        if stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            yield entry.in_path(path)
        elif stat.S_ISDIR(mode):
            yield entry.in_path(path)
            for inner_entry in tree_iterator(repo, entry.sha, entry.path):
                yield inner_entry


def export(repo, tree_sha, target, exported_trees):
    not_found = tree_iterator(repo, tree_sha)

    for exported_tree in exported_trees:
        id2path = create_exported_tree_map(repo, exported_tree.tree)
        export_iter = not_found
        not_found = []
        for entry in export_iter:
            if stat.S_ISDIR(entry.mode):
                #  mkdir -p
                continue

            link_target = id2path.get((entry.mode, entry.sha))
            if link_target:
                pass
                # link
            else:
                not_found.append(entry)

if __name__ == '__main__':
    args=parse_args()
    repo=Repo(os.curdir)
    # TODO resolve treeish to tree_sha1
    tree_sha1=args.treeish[0]

    export(repo, tree_sha1, args.target[0], args.link)
