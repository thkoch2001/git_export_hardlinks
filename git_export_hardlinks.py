#!python

from dulwich.repo import Repo
from collections import namedtuple
from itertools import imap, chain
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
    """Generates all tree nodes recursively.
    """

    tree = repo.tree(tree_sha)
    for entry in tree.iteritems():
        mode = entry.mode
        if stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            yield entry.in_path(path)
        elif stat.S_ISDIR(mode):
            yield entry.in_path(path)
            for inner_entry in tree_iterator(repo, entry.sha, os.path.join(path, entry.path)):
                yield inner_entry

def _gen_exported_tree_producer(repo, exported_tree):
    id2path = create_exported_tree_map(repo, exported_tree.tree)

    def trylink(entry, abs_path):
        link_source = id2path.get((entry.mode, entry.sha))
        if link_source:
            abs_link_source = os.path.join(exported_tree.path, link_source)
            try:
                os.link(abs_link_source, abs_path)
            except OSError as e:
                if not os.path.exists(abs_link_source):
                    raise IOError("Link source does not exist: %s" % abs_link_source)
                elif not os.path.isdir(os.path.basename(abs_path)):
                    raise IOError("Target dir does not exist for: %s" % abs_path)
                raise IOError("Could not link %s to %s" % (abs_link_source, abs_path))
            return True
        else:
            return False

    return trylink

def _write_file(abs_path, content):
    fd = open(abs_path, 'w')
    fd.write(content)
    fd.close()

def _gen_repo_producer(repo):
    def produce(entry, abs_path):
        blob = repo.get_blob(entry.sha)
        _write_file(abs_path, blob.as_raw_string())
        return True
    return produce

def _ensure_target_is_empty_dir(target):
    if os.path.isdir(target):
        if os.listdir(target):
            raise IOError("Not empty: %s" % target)
    else:
        os.mkdir(target)


def export(repo, tree_sha, target, exported_trees=[]):
    """Export a git tree to a target dir using hardlinks from previous exports.

    :param repo: dulwich git Repo instance to export from
    :param tree_sha: the sha of the git tree object to export
    :param target: the target folder
    :param exported_trees: iterable of ExportedTree instances
    """

    _ensure_target_is_empty_dir(target)

    not_found = tree_iterator(repo, tree_sha)
    producers = chain(imap(lambda _:_gen_exported_tree_producer(repo, _), exported_trees),
                       [_gen_repo_producer(repo)]
                       )

    for produce in producers:

        export_iter = not_found
        not_found = []

        for entry in export_iter:

            abs_path = os.path.join(target, entry.path)

            if stat.S_ISDIR(entry.mode) and not os.path.isdir(abs_path):
                os.mkdir(abs_path)
            elif stat.S_ISREG or stat.S_ISLNK:
                written = produce(entry, abs_path)
                if(not written):
                    not_found.append(entry)

    if not_found:
        raise IOError("Some files could not be exported: %s" % ", ".join(map(repr, not_found)))

if __name__ == '__main__':
    args=parse_args()
    repo=Repo(os.curdir)
    # TODO resolve treeish to tree_sha1
    tree_sha1=args.treeish[0]

    export(repo, tree_sha1, args.target[0], args.link)
