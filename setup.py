import pathlib

import setuptools

docs_requires = ["sphinx"]
tests_requires = ['pytest>=3.0.0', 'pytest-asyncio']
aiohttp_requires = ["aiohttp"]
treq_requires = ["treq", "twisted"]

long_description = pathlib.Path("README.rst").read_text("utf-8")

setuptools.setup(
    name="gidgethub",
    version="2.0.0.dev1",
    description="An async GitHub API library",
    long_description=long_description,
    url="https://gidgethub.readthedocs.io",
    author="Brett Cannon",
    author_email="brett@python.org",
    license="Apache",
    classifiers=[
        'Intended Audience :: Developers',
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 4 - Beta",
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
    ],
    keywords="github sans-io async",
    packages=setuptools.find_packages(),
    zip_safe=True,
    python_requires=">=3.6.0",
    setup_requires=['pytest-runner>=2.11.0'],
    tests_require=tests_requires,
    install_requires=['uritemplate>=3.0.0'],
    extras_require={
        "docs": docs_requires,
        "tests": tests_requires,
        "aiohttp": aiohttp_requires,
        "treq": treq_requires,
        "dev": docs_requires + tests_requires + aiohttp_requires + treq_requires,
    },
)
