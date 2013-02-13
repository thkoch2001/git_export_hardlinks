- Support git-attributes to limit the files to export

  - Do not export files with attribute export-ignore

  - Add an attribute "deploy-ignore". One might have files that make sense in
    a release tarball (tests, docus) but which should not be deployed to the
    server.

- Support the export-subst attribute. This depends on an implementation of the
  pretty-format logic of git. This does not make sense to be coded in python
  but should rather be implemented in libgit2.

- Move git utility methods out to dulwich or GitPython

- Upload to PyPi
