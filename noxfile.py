import nox


def install_flit_dev_deps(session):
    session.install("flit")
    # TEMP for 3.11
    if session.python == "3.11":
        env = {
            # https://github.com/aio-libs/aiohttp/issues/6600
            "AIOHTTP_NO_EXTENSIONS": "1",
            # https://github.com/aio-libs/frozenlist/issues/285
            "FROZENLIST_NO_EXTENSIONS": "1",
            # https://github.com/aio-libs/yarl/issues/680
            "YARL_NO_EXTENSIONS": "1",
        }
    else:
        env = {}
    session.run("flit", "install", "--deps", "develop", env=env)


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"])
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
