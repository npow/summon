"""Tests for workspace manager."""

import tempfile
from pathlib import Path

from oneshot.workspace import Workspace


def test_workspace_creates_temp_dir():
    ws = Workspace()
    assert ws.path.exists()
    assert ws.path.is_dir()
    ws.cleanup()
    assert not ws.path.exists()


def test_workspace_custom_dir():
    with tempfile.TemporaryDirectory() as d:
        ws = Workspace(d)
        assert ws.path == Path(d)


def test_write_and_read_file():
    ws = Workspace()
    try:
        ws.write_file("src/main.py", "print('hello')")
        content = ws.read_file("src/main.py")
        assert content == "print('hello')"
    finally:
        ws.cleanup()


def test_file_exists():
    ws = Workspace()
    try:
        assert not ws.file_exists("nope.py")
        ws.write_file("nope.py", "x")
        assert ws.file_exists("nope.py")
    finally:
        ws.cleanup()


def test_list_files():
    ws = Workspace()
    try:
        ws.write_file("a.py", "a")
        ws.write_file("src/b.py", "b")
        files = ws.list_files()
        assert "a.py" in files
        assert "src/b.py" in files
    finally:
        ws.cleanup()
