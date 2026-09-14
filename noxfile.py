# /// script
# dependencies = ["nox"]
# ///

import nox

PYPROJECT = nox.project.load_toml("pyproject.toml")

TEST_PYTHON_VERSIONS = nox.project.python_versions(PYPROJECT)
# Minimum Supported Python Version
MSPV = f"py{TEST_PYTHON_VERSIONS[0].replace('.', '')}"


@nox.session(python=TEST_PYTHON_VERSIONS)
def tests(session):
    """Run the test suite."""
    session.install(
        ".[aiohttp,tornado,httpx2]",
        *nox.project.dependency_groups(PYPROJECT, "test"),
    )
    session.run("pytest", "--cov=gidgethub", "--cov-report=xml", "-n=auto", "tests")


@nox.session(default=False)
def lint(session):
    """Lint the code."""
    session.install(
        ".",
        *nox.project.dependency_groups(PYPROJECT, "code-check"),
    )
    session.run("ruff", "check", "--target-version", MSPV)


@nox.session(default=False)
def type_check(session):
    """Type check all the code."""
    session.install(
        ".[aiohttp,tornado,httpx2]",
        *nox.project.dependency_groups(PYPROJECT, "type-check"),
    )
    session.run("pyrefly", "coverage", "check")
    session.run("pyrefly", "check")


@nox.session(default=False)
def compatibility_type_check(session):
    """Type check for compatibility with other type checkers."""
    session.install(
        ".[aiohttp,tornado,httpx2]",
        *nox.project.dependency_groups(PYPROJECT, "type-check"),
    )
    session.run("mypy", "--check-untyped-defs", "tests")


@nox.session(default=False)
def docs(session):
    """Build the docs."""
    session.install(
        ".",
        *nox.project.dependency_groups(PYPROJECT, "doc"),
    )
    # fmt: off
    session.run(

        "sphinx-build",
        "--jobs", "auto",
        "-nW",
        "-q",
        "-b", "html",
        "-d", "docs/_build/doctrees", "docs", "docs/_build/html",
    )
    # fmt: on


@nox.session
def check(session):
    """Run all linting checks."""
    session.install(
        ".",
        *nox.project.dependency_groups(PYPROJECT, "format"),
    )
    session.run("black", "--target-version", MSPV, "--check", ".")
    lint(session)
    type_check(session)
    compatibility_type_check(session)
    docs(session)


@nox.session(default=False)
def format(session):
    """Format the code."""
    session.install(".", *nox.project.dependency_groups(PYPROJECT, "format"))
    session.run("black", "--target-version", MSPV, ".")


if __name__ == "__main__":
    import sys

    sys.exit(nox.main())
