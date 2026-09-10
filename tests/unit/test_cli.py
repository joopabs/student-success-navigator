from __future__ import annotations

import subprocess
import sys

from ssn.cli import CONTRACT_COMMANDS, EXIT_CONFIG, main


def _run(*args):
    return subprocess.run([sys.executable, "-m", "ssn", *args], capture_output=True, text=True)


def test_help_lists_every_contract_command():
    out = _run("--help").stdout
    for group, name, _ in CONTRACT_COMMANDS:
        assert (group or name) in out


def test_config_validate_ok():
    r = _run("config", "validate")
    assert r.returncode == 0 and "config OK" in r.stdout and "allow-list:" in r.stdout


def test_config_validate_bad_file_exits_2(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("seed: 1\n")
    r = _run("config", "validate", "--config", str(p))
    assert r.returncode == EXIT_CONFIG and "missing required key" in r.stderr


def test_unimplemented_command_exits_2():
    r = _run("app")
    assert r.returncode == EXIT_CONFIG and "not implemented" in r.stderr


def test_unknown_command_is_rejected():
    assert _run("nope").returncode != 0


def test_no_command_prints_help_and_exits_2(capsys):
    assert main([]) == EXIT_CONFIG
    assert "usage: ssn" in capsys.readouterr().out
