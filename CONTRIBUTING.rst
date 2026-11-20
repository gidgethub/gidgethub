Contributing and Maintenance Guide
==================================

As of v6.0.0 (September 25, 2026), this project is in maintenance-only mode.
We welcome bug reports and will make a best-effort attempt at fixing them.
We do **not** accept feature requests or pull requests from external
contributors.

Maintenance Guide
-----------------

This is only pertinent to maintainers of this project.

Merging a pull request
''''''''''''''''''''''

Ensure that the tests are all passing, and that the coverage remains at
100% before merging the pull request.

Squash the commits. Rewrite the commit message if necessary.

Documentation build
'''''''''''''''''''

The documentation is hosted at Read the Docs. Documentation build is triggered
immediately after each commit to the main branch.

The up-to-date list of maintainers who can deploy or debug the documentation
build can be seen on the project's `Read the Docs page
<https://readthedocs.org/projects/gidgethub/>`_.

Releasing the library
'''''''''''''''''''''

Pre-release:

- Ensure that the changelog is up-to-date.

- Ensure that the ``__version__`` number in ``gidgethub/__init__.py``, ignoring
  the ``.dev`` suffix, is the version you intend to release.

- Ensure the tests have passed and that coverage is at 100%.

Preparing for a release:

- Create a new branch for the release. Remove the ``.dev`` suffix from
  ``__version__`` and rename the "Unreleased" changelog section to the new
  version number.

- Open a pull request for the release branch, and merge it into ``main`` once
  the checks pass.

- Publish the package to PyPI. Run the "Release" GitHub Actions workflow from
  the ``main`` branch, before anything else is merged into ``main``, since the
  workflow builds whatever ``main`` points to. Only ``main`` is allowed to
  deploy to the ``release`` environment, and a maintainer must approve the
  deployment.

- `Create a new release <https://github.com/gidgethub/gidgethub/releases/new>`_
  on GitHub, with a ``vX.Y.Z`` tag targeting the squash-merge commit of the
  release pull request. Include the changelog, and attach the binaries (the
  ``Packages`` artifact from the "Release" workflow run).

Post-release:

- In a pull request, bump the ``__version__`` number in
  ``gidgethub/__init__.py`` to the next version with a ``.dev`` suffix, and add
  an "Unreleased" section to the changelog.

- Announce the release. (optional).

