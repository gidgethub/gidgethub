import setuptools

NAME = "gidgethub"

tests_require = ['pytest>=3.0.0']

setuptools.setup(
    name=NAME,
    version="0.1.0.dev1",
    description="A sans-I/O GitHub API library",
    url="https://github.com/brettcannon/gidgethub",
    author="Brett Cannon",
    author_email="brett@python.org",
    license="Apache",
    classifiers=[
        'Intended Audience :: Developers',
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 2 - Pre-Alpha",
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
    ],
    keywords="github sans-io",
    packages=setuptools.find_packages(),
    zip_safe=True,
    python_requires=">=3.6.0",
    setup_requires=['pytest-runner>=2.11.0'],
    tests_require=tests_require,
    install_requires=['uritemplate>=3.0.0'],
    extras_require={
        "test": tests_require
    },
)
