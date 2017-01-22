# gidgethub
A [sans-I/O](https://sans-io.readthedocs.io/) [GitHub API](https://developer.github.com/) library

## Goals
The key goal is to provide a library for the
[GitHub API](https://developer.github.com/) which performs no I/O of its own (a
"[sans-I/O](https://sans-io.readthedocs.io/)" library). This allows users to
choose whatever HTTP library they prefer while parceling out GitHub-specific
details to this library.

Long-term the hope is to provide an abstract base class which implements as many
details as possible on behalf of an asynchronous HTTP library.

## Alternative libraries
If you think you want a different approach to the GitHub API,
[GitHub maintains a list of libraries](https://developer.github.com/libraries/).

## Aside: what's with the name?
I couldn't think of a good name that was somehow a play on "GitHub" or somehow
tied into [Monty Python](http://www.montypython.com/). And so I decided to play
off of GitHub's [octocat](https://octodex.github.com/) as a theme and use my
cat's name, Gidget, as part of the name. Since "Gidget" somewhat sounds like
"git", I decided to go with "gidgethub".
