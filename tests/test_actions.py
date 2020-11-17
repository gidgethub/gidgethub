import json
import os

import pytest

from gidgethub import actions


@pytest.fixture
def tmp_webhook(tmp_path, monkeypatch):
    """Create a temporary file for an actions webhook event."""
    tmp_file_path = tmp_path / "event.json"
    monkeypatch.setenv("GITHUB_EVENT_PATH", os.fspath(tmp_file_path))
    return tmp_file_path


@pytest.fixture
def tmp_envfile(tmp_path, monkeypatch):
    """Create a temporary environment file."""
    tmp_file_path = tmp_path / "setenv.txt"
    monkeypatch.setenv("GITHUB_ENV", os.fspath(tmp_file_path))
    return tmp_file_path


@pytest.fixture
def tmp_pathfile(tmpdir, tmp_path, monkeypatch):
    """Create a temporary system path file and a temporary directory path."""
    tmp_file_path = tmp_path / "addpath.txt"
    monkeypatch.setenv("GITHUB_PATH", os.fspath(tmp_file_path))
    return tmp_file_path, tmpdir


class TestWorkspace:

    """Tests for gidgethub.actions.workspace()."""

    def test_reading(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_WORKSPACE", os.fspath(tmp_path))
        assert actions.workspace() == tmp_path

    def test_caching(self, tmp_path, monkeypatch):
        actions.workspace.cache_clear()
        monkeypatch.setenv("GITHUB_WORKSPACE", os.fspath(tmp_path))
        assert actions.workspace() == tmp_path
        new_path = tmp_path / "DOES NOT EXIST"
        monkeypatch.setenv("GITHUB_WORKSPACE", os.fspath(new_path))
        assert actions.workspace() == tmp_path


class TestEvent:

    """Tests for gidgethub.actions.event()."""

    def test_reading(self, tmp_webhook):
        data = {"something": "going on"}
        tmp_webhook.write_text(json.dumps(data), encoding="utf-8")
        assert actions.event() == data

    def test_caching(self, tmp_webhook):
        actions.event.cache_clear()
        self.test_reading(tmp_webhook)
        original_data = actions.event()
        new_data = {"something": "completely different"}
        tmp_webhook.write_text(json.dumps(new_data), encoding="utf-8")
        assert actions.event() == original_data


class TestCommand:

    """Tests for gidgethub.actions.command()."""

    # https://help.github.com/en/actions/reference/development-tools-for-github-actions#logging-commands

    def _stdout(self, capsys):
        stdout, stderr = capsys.readouterr()
        assert not stderr
        assert stdout
        return stdout.strip()

    def test_set_output(self, capsys):
        actions.command("set-output", "strawberry", name="action_fruit")
        assert self._stdout(capsys) == "::set-output name=action_fruit::strawberry"

    def test_debug(self, capsys):
        actions.command(
            "debug", "Entered octocatAddition method", file="app.js", line="1"
        )
        assert (
            self._stdout(capsys)
            == "::debug file=app.js,line=1::Entered octocatAddition method"
        )

    def test_warning(self, capsys):
        actions.command(
            "warning", "Missing semicolon", file="app.js", line="1", col="5"
        )
        assert (
            self._stdout(capsys)
            == "::warning file=app.js,line=1,col=5::Missing semicolon"
        )

    def test_error(self, capsys):
        actions.command(
            "error", "Something went wrong", file="app.js", line="10", col="15"
        )
        assert (
            self._stdout(capsys)
            == "::error file=app.js,line=10,col=15::Something went wrong"
        )

    def test_add_mask(self, capsys):
        actions.command("add-mask", "Mona The Octocat")
        assert self._stdout(capsys) == "::add-mask::Mona The Octocat"

    def test_stop_commands(self, capsys):
        actions.command("stop-commands", "pause-logging")
        assert self._stdout(capsys) == "::stop-commands::pause-logging"

    def test_resume_command(self, capsys):
        actions.command("pause-logging")
        assert self._stdout(capsys) == "::pause-logging::"


class TestSetenv:

    """Tests for gidgethub.actions.setenv()."""

    def test_creating(self, tmp_envfile):
        actions.setenv("HELLO", "WORLD")
        data = tmp_envfile.read_text(encoding="utf-8")
        assert os.environ["HELLO"] == "WORLD"
        assert data == f"HELLO<<END{os.linesep}WORLD{os.linesep}END{os.linesep}"

    def test_updating(self, tmp_envfile):
        actions.setenv("CHANGED", "FALSE")
        data = tmp_envfile.read_text(encoding="utf-8")
        assert os.environ["CHANGED"] == "FALSE"
        assert data == f"CHANGED<<END{os.linesep}FALSE{os.linesep}END{os.linesep}"
        actions.setenv("CHANGED", "TRUE")
        updated = tmp_envfile.read_text(encoding="utf-8")
        assert os.environ["CHANGED"] == "TRUE"
        # Rendering of the updated variable is done by GitHub.
        assert (
            updated == data + f"CHANGED<<END{os.linesep}TRUE{os.linesep}END{os.linesep}"
        )

    def test_creating_multiline(self, tmp_envfile):
        multiline = """This
                        is
                        a
                        multiline
                        string."""
        actions.setenv("MULTILINE", multiline)
        data = tmp_envfile.read_text(encoding="utf-8")
        assert os.environ["MULTILINE"] == multiline
        assert (
            data
            == f"""MULTILINE<<END{os.linesep}This
                        is
                        a
                        multiline
                        string.{os.linesep}END{os.linesep}"""
        )


class TestAddpath:

    """Tests for gidgethub.actions.addpath()."""

    def test_string_path(self, tmp_pathfile):
        actions.addpath("/path/to/random/dir")
        data = tmp_pathfile[0].read_text(encoding="utf-8")
        assert f"/path/to/random/dir{os.pathsep}" in os.environ["PATH"]
        assert data == f"/path/to/random/dir{os.linesep}"

    def test_path_object(self, tmp_pathfile):
        actions.addpath(tmp_pathfile[1])
        data = tmp_pathfile[0].read_text(encoding="utf-8")
        assert f"{tmp_pathfile[1]!s}{os.pathsep}" in os.environ["PATH"]
        assert data == f"{tmp_pathfile[1]!s}{os.linesep}"

    def test_multiple_paths(self, tmp_pathfile):
        actions.addpath("/path/to/random/dir")
        random_path = tmp_pathfile[1] / "random.txt"
        actions.addpath(random_path)
        data = tmp_pathfile[0].read_text(encoding="utf-8")
        # Last path added comes first.
        assert f"{random_path!s}{os.pathsep}/path/to/random/dir{os.pathsep}"
        assert data == f"/path/to/random/dir{os.linesep}{random_path!s}{os.linesep}"
