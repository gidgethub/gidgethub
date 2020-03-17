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

    def test_set_env(self, capsys):
        actions.command("set-env", "yellow", name="action_state")
        assert self._stdout(capsys) == "::set-env name=action_state::yellow"

    def test_set_output(self, capsys):
        actions.command("set-output", "strawberry", name="action_fruit")
        assert self._stdout(capsys) == "::set-output name=action_fruit::strawberry"

    def test_add_path(self, capsys):
        actions.command("add-path", "/path/to/dir")
        assert self._stdout(capsys) == "::add-path::/path/to/dir"

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
