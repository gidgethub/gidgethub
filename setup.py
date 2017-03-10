import pathlib

import setuptools


tests_require = ['pytest>=3.0.0', 'pytest-asyncio']

long_description = pathlib.Path("README.rst").read_text("utf-8")

setuptools.setup(
    name="gidgethub",
    version="1.1.0",
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
    tests_require=tests_require,
    install_requires=['uritemplate>=3.0.0'],
    extras_require={
        "docs": ["sphinx"],
        "test": tests_require,
        "aiohttp": ["aiohttp"],
        "treq": ["treq", "twisted"],
    },
)
