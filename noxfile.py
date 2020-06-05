import nox


def install_flit_dev_deps(session):
    session.install("flit")
    session.run("flit", "install", "--deps", "develop")


@nox.session(python=["3.6", "3.7", "3.8"])
def tests(session):
    install_flit_dev_deps(session)
    session.run("pytest", "--cov=gidgethub", "--cov-report=xml", "-n=auto", "tests")


@nox.session
def lint(session):
    install_flit_dev_deps(session)
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
