import nox

PYPROJECT = nox.project.load_toml("pyproject.toml")


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15"])
def tests(session):
    session.install(
        ".[aiohttp,tornado,httpx]",
        *nox.project.dependency_groups(PYPROJECT, "test"),
    )
    session.run("pytest", "--cov=gidgethub", "--cov-report=xml", "-n=auto", "tests")


@nox.session
def lint(session):
    session.install(".", *nox.project.dependency_groups(PYPROJECT, "lint", "doc"))
    session.run("black", "--check", ".")
    session.run("mypy", "--ignore-missing-imports", "--strict", "gidgethub")
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
