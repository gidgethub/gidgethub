"""Support for GitHub Actions."""
import functools
import json
import os
import pathlib
from typing import Any, Union


@functools.lru_cache(maxsize=1)
def workspace() -> pathlib.Path:
    """Return the action workspace as a pathlib.Path object."""
    return pathlib.Path(os.environ["GITHUB_WORKSPACE"])


@functools.lru_cache(maxsize=1)
def event() -> Any:
    """Return the webhook event data for the running action."""
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as file:
        return json.load(file)


# https://github.com/actions/toolkit/blob/b0e01b71c0e630eb4b420f763029a7476c6cf075/packages/core/src/command.ts#L76-L81
_DATA_ESCAPE = [("%", "%25"), ("\r", "%0D"), ("\n", "%0A")]
# https://github.com/actions/toolkit/blob/b0e01b71c0e630eb4b420f763029a7476c6cf075/packages/core/src/command.ts#L83-L90
_VALUE_ESCAPE = [("%", "%25"), ("\r", "%0D"), ("\n", "%0A"), (":", "%3A"), (",", "%3A")]


def command(cmd: str, data: str = "", **parameters: str) -> None:
    """Issue a logging command."""
    cmd_parts = [f"::{cmd}"]
    if parameters:
        cmd_parts.append(" ")
        param_list = []
        for param, val in parameters.items():
            val = functools.reduce(
                lambda accum, args: accum.replace(*args), _VALUE_ESCAPE, val
            )
            param_list.append(f"{param}={val}")
        cmd_parts.append(",".join(param_list))
    data = functools.reduce(
        lambda accum, args: accum.replace(*args), _DATA_ESCAPE, data
    )
    cmd_parts.append(f"::{data}")
    print("".join(cmd_parts))


_DELIMITER = "__GIDGETHUB_DELIMITER__"


def setenv(name: str, value: str) -> None:
    """Create or update an environment variable.

    The change applies to this action and future actions running in the job.
    """
    # https://github.com/actions/toolkit/blob/af821474235d3c5e1f49cee7c6cf636abb0874c4/packages/core/src/core.ts#L35-L53
    os.environ[name] = value
    # https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#multiline-strings
    write_value = f"{name}<<{_DELIMITER}{os.linesep}{value}{os.linesep}{_DELIMITER}"
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as file:
        file.write(write_value + os.linesep)


def addpath(path: Union[str, "os.PathLike[str]"]) -> None:
    """Prepend to PATH.

    This affects this action and all subsequent actions in the current job.
    """
    # https://github.com/actions/toolkit/blob/af821474235d3c5e1f49cee7c6cf636abb0874c4/packages/core/src/core.ts#L63-L75
    os.environ["PATH"] = f"{path!s}{os.pathsep}{os.environ['PATH']}"
    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as file:
        file.write(os.fspath(path) + os.linesep)
