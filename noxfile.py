import nox

PYPROJECT = nox.project.load_toml("pyproject.toml")


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15"])
def tests(session):
    session.install(
        ".[aiohttp,tornado,httpx2]",
        *nox.project.dependency_groups(PYPROJECT, "test"),
    )
    session.run("pytest", "--cov=gidgethub", "--cov-report=xml", "-n=auto", "tests")


@nox.session(default=False)
def type_check(session):
    session.install(
        ".[aiohttp,tornado,httpx2]",
        *nox.project.dependency_groups(PYPROJECT, "type-check"),
    )
    session.run("pyrefly", "coverage", "check")
    session.run("pyrefly", "check")


@nox.session(default=False)
def docs(session):
    session.install(
        ".",
        *nox.project.dependency_groups(PYPROJECT, "doc"),
    )
    session.run(
        "sphinx-build",
        "-nW",
        "-q",
        "-b",
        "html",
        "-b",
        "linkcheck",
        "-d",
        "docs/_build/doctrees",
        "docs",
        "docs/_build/html",
    )


@nox.session
def lint(session):
    session.install(
        ".",
        *nox.project.dependency_groups(PYPROJECT, "format"),
    )
    session.run("black", "--target-version", "py39", "--check", ".")
    type_check(session)
    docs(session)


@nox.session(default=False)
def format(session):
    session.install(".", *nox.project.dependency_groups(PYPROJECT, "format"))
    session.run("black", "--target-version", "py39", ".")
