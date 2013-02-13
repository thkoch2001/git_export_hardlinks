Git export with hardlinks
=========================

This package implements a git export command that can be given a list of
already exported worktrees and the tree SHAs these worktrees correspond
too. For every file to export it then looks in the existing worktrees whether
an identical file is already present and in that case hardlinks to the new
export location instead of writing the same file again.

Use Case: A git based web deployment system that exports git trees to be
served by a web server. Every new deployment is written to a new folder. After
the export, the web server should start serving new requests from the new
folder.

Usage
-----

::

  usage: git_export_hardlinks.py [-h] [-l [LINK [LINK ...]]] treeish target
  
  git export that reuses already existing exports and hardlinks files from them.
  
  positional arguments:
    treeish               treeish (ref, commit, tree) to export
    target                location where to export to
  
  optional arguments:
    -h, --help            show this help message and exit
    -l [LINK [LINK ...]], --link [LINK [LINK ...]]
                          existing export to hardlink from: TREEISH,PATH. Newest
                          first
  
  Be aware of the dangers of hardlinks. Hardlinks on linux do not have copy-on-
  write semantics! This command also does not verify the integrity of old
  exported trees. Use git reset --hard after this command to guarantee a correct
  export.

Examples
--------

Export a git tag::

  ./git_export_hardlinks.py v0.1 /var/lib/deployments/v0.1/export

Export a git commit::

  ./git_export_hardlinks.py b86a93d9ca0d272410586f18a95b41c3b9a600ab /var/lib/deployments/2012-02-05

Export a git branch and link to previous trees::

  ./git_export_hardlinks.py \
      -l 0b96bf5f72d2c282b31726b3fbff279a89220b14,/srv/deploy/2013-02-13_10-08-13 \
      -l aae9deb62ad0c8d1ba64c75845a0809da485f42e,/srv/deploy/2013-02-12_14-09-15 \
      -l fe2665df0df31da3098de376268d4cd25ea6a6b7,/srv/deploy/2013-02-12_12-57-55 \
      -- 2013-02-14_17-44-12 /srv/deploy/2013-02-14_17-44-12

Notes:

- The double dash (--) before the positional arguments works around a `python argparse issue`__.

- The exported trees are listed from newest to oldest. It is assumed that the
  newest tree is also the most similar tree.

- You might want to generate the options for this commands with some shell scripting.

- The command can not parse git refspecs like HEAD{2}.

- You might want to limit the number of -l arguments. Otherwise
  git_export_hardlink will search all trees before giving up and writing the
  file from the git object store.

.. __: http://bugs.python.org/issue9338
