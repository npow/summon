"""Tests for agent base factory."""

import json

from summon.agents.base import _extract_json, _DefaultDict


def test_extract_json_plain():
    result = _extract_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_extract_json_markdown_block():
    text = 'Some text\n```json\n{"key": "value"}\n```\nMore text'
    result = _extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_code_block():
    text = 'Here is the result:\n```\n{"key": "value"}\n```'
    result = _extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_embedded():
    text = 'The answer is {"key": "value"} as shown above.'
    result = _extract_json(text)
    assert result == {"key": "value"}


def test_extract_json_array():
    text = '[1, 2, 3]'
    result = _extract_json(text)
    assert result == [1, 2, 3]


def test_default_dict():
    d = _DefaultDict({"a": "1", "b": "2"})
    assert d["a"] == "1"
    assert d["missing"] == "(not available)"


def test_extract_json_with_surrounding_text():
    text = 'Sure! Here is the spec:\n\n{"project_name": "test", "version": "1.0"}\n\nLet me know if you need changes.'
    result = _extract_json(text)
    assert result["project_name"] == "test"
