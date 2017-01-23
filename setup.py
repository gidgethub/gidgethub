import setuptools

NAME = "gidgethub"

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
        "Development Status :: 1 - Planning",
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
    ],
    keywords="github sans-io",
    packages=[NAME],
    zip_safe=True,
    python_requires=">=3.6.0",
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
