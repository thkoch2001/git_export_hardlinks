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

from dulwich.repo import Repo
from dulwich.objects import parse_tag, parse_commit
from collections import namedtuple
from itertools import imap, chain, dropwhile
import os
import os.path
import stat
import argparse
import sys

ExportedTree = namedtuple('ExportedTree', 'tree, path')

DESCRIPTION="Git export command that reuses already existing exports and hardlinks files from them."
LONG_DESCRIPTION="""This package implements a git export command that can be given a list of
already exported worktrees and the tree SHAs these worktrees correspond
too. For every file to export it then looks in the existing worktrees whether
an identical file is already present and in that case hardlinks to the new
export location instead of writing the same file again.

Use Case: A git based web deployment system that exports git trees to be
served by a web server. Every new deployment is written to a new folder. After
the export, the web server should start serving new requests from the new
folder."""

EPILOG="""Be aware of the dangers of hardlinks. Hardlinks on linux do not
have copy-on-write semantics! This command also does not verify the integrity
of old exported trees. Use git reset --hard after this command to guarantee
a correct export."""

def parse_args(argv):
    class SplitLinkOption(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            exported_trees = []
            for value in values:
                tree, path = value.split(',', 1)
                exported_trees.append(ExportedTree(tree=tree, path=os.path.abspath(path)))
            setattr(namespace, self.dest, exported_trees)

    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG
    )
    parser.add_argument("-l", "--link", help="existing export to hardlink from: TREEISH,PATH. Newest first",
                        action=SplitLinkOption, nargs='*'
                        )

    parser.add_argument("treeish", help="treeish (ref, commit, tree) to export", nargs=1)
    parser.add_argument("target", help="location where to export to", nargs=1)

    return parser.parse_args(argv)


def create_exported_tree_map(repo, treeish, path=""):
    """Returns a map of (mode, sha) tupples to relative paths.

    A tree can contain duplicate files and thus only one of those files will
    be in the map.

    :param repo: dulwich Repo instance
    :param treeish: ref or sha of a treeish
    :param path: private parametery used for recursion
    """
    id2path={}
    tree = repo.tree(_resolve_treeish(repo, treeish))
    for name, mode, sha in tree.iteritems():
        if stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            id2path[(mode, sha)] = os.path.join(path, name)
        elif stat.S_ISDIR(mode):
            id2path.update(create_exported_tree_map(repo, sha, os.path.join(path, name)))
    # TODO: what to do about submodules
    return id2path

def tree_iterator(repo, treeish, path=""):
    """Generates all tree nodes recursively.
    """

    tree = repo.tree(_resolve_treeish(repo, treeish))
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


def export(repo, treeish, target, exported_trees=[]):
    """Export a git tree to a target dir using hardlinks from previous exports.

    :param repo: dulwich git Repo instance to export from
    :param treeish: ref or sha of the treeish to export
    :param target: the target folder
    :param exported_trees: iterable of ExportedTree instances
    """

    _ensure_target_is_empty_dir(target)

    not_found = tree_iterator(repo, treeish)
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


def _get_object_field(sha_file, field):
    """returns the value of a field from a tag or commit sha_file
    """
    values = [item[1] for item in parse_tag(sha_file.as_raw_string()) if item[0] == field]
    # TODO raise for empty values
    return values[0]

def _could_be_sha(treeish):
    try:
        int(treeish, 16)
        return True
    except ValueError:
        return False

def _resolve_treeish(repo, treeish):
    """Resolve a reference or tag/commit/tree sha to a tree sha
    """
    try:
        sha=repo.ref(treeish)
        return _resolve_sha_to_tree(repo, sha)
    except KeyError:
        if(_could_be_sha(treeish)):
            return _resolve_sha_to_tree(repo, treeish)

    raise ValueError("Could not resolve treeish %s" % treeish)

def _resolve_sha_to_tree(repo, sha):
    sha_file = repo.get_object(sha)
    type_name = sha_file.type_name

    if(type_name == 'tree'):
        return sha
    elif(type_name == 'tag'):
        commit_sha = _get_object_field(sha_file, "object")
        return _resolve_sha_to_tree(repo, commit_sha)
    elif(type_name == 'commit'):
        tree_sha = _get_object_field(sha_file, "tree")
        return _resolve_sha_to_tree(repo, tree_sha)
    else:
        pass
        # raise

def _main(argv=sys.argv):
    args = parse_args(argv)
    repo = Repo(os.curdir)
    treeish = _resolve_treeish(repo, args.treeish[0])

    export(repo, treeish, args.target[0], args.link)

if __name__ == '__main__':
    _main()
