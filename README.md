# gidgethub
A [sans-I/O](https://sans-io.readthedocs.io/) [GitHub API](https://developer.github.com/) library

[![Build Status](https://travis-ci.org/brettcannon/gidgethub.svg?branch=master)](https://travis-ci.org/brettcannon/gidgethub)
[![codecov](https://codecov.io/gh/brettcannon/gidgethub/branch/master/graph/badge.svg)](https://codecov.io/gh/brettcannon/gidgethub)
[![Documentation Status](https://readthedocs.org/projects/gidgethub/badge/?version=latest)](http://gidgethub.readthedocs.io/en/latest/?badge=latest)

## Installation
No wheels have been uploaded to PyPI _yet_. Until then, you can install from
source, e.g. `python3 -m pip install .` or `python3 -m pip install ".[aiohttp]`.

## Goals
The key goal is to provide a base library for the
[GitHub API](https://developer.github.com/) which performs no I/O of its own (a
"[sans-I/O](https://sans-io.readthedocs.io/)" library). This allows users to
choose whatever HTTP library they prefer while parceling out GitHub-specific
details to this library. This base library is then built upon to provide an
abstract base class to a cleaner API to work with. Finally, implementations of
the abstract base class are provided for asynchronous HTTP libraries for
immediate usage.

## Alternative libraries
If you think you want a different approach to the GitHub API,
[GitHub maintains a list of libraries](https://developer.github.com/libraries/).

## Aside: what's with the name?
I couldn't think of a good name that was somehow a play on "GitHub" or somehow
tied into [Monty Python](http://www.montypython.com/). And so I decided to play
off of GitHub's [octocat](https://octodex.github.com/) as a theme and use my
cat's name, Gidget, as part of the name. Since "Gidget" somewhat sounds like
"git", I decided to go with "gidgethub".

