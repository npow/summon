"""Tests for pipeline construction."""

import pytest

from forge.config import ForgeConfig
from forge.pipeline import build_pipeline


def test_pipeline_builds_with_gates():
    config = ForgeConfig()
    pipeline = build_pipeline(config, skip_gates=False)
    assert pipeline is not None
    # Check that the graph has nodes
    graph = pipeline.get_graph()
    node_ids = list(graph.nodes)
    assert "stage1" in node_ids
    assert "gate1" in node_ids


def test_pipeline_builds_without_gates():
    config = ForgeConfig()
    pipeline = build_pipeline(config, skip_gates=True)
    assert pipeline is not None
    graph = pipeline.get_graph()
    node_ids = list(graph.nodes)
    assert "stage1" in node_ids
    assert "gate1" not in node_ids


def test_pipeline_until_stage_1():
    config = ForgeConfig()
    pipeline = build_pipeline(config, skip_gates=True, until_stage=1)
    graph = pipeline.get_graph()
    node_ids = list(graph.nodes)
    assert "stage1" in node_ids
    assert "stage1_mark" in node_ids
    assert "stage2" not in node_ids
    assert "stage2_mark" not in node_ids


def test_pipeline_from_stage_2():
    config = ForgeConfig()
    pipeline = build_pipeline(config, skip_gates=True, from_stage=2)
    graph = pipeline.get_graph()
    node_ids = list(graph.nodes)
    assert "stage1" not in node_ids
    assert "stage1_mark" not in node_ids
    assert "stage2" in node_ids
    assert "stage2_mark" in node_ids
    assert "stage6" in node_ids


def test_pipeline_from_stage_2_with_gates():
    config = ForgeConfig()
    pipeline = build_pipeline(config, skip_gates=False, from_stage=2)
    graph = pipeline.get_graph()
    node_ids = list(graph.nodes)
    assert "gate1" not in node_ids
    assert "gate2" in node_ids
    assert "gate6" in node_ids


def test_pipeline_stage_range_3_to_5():
    config = ForgeConfig()
    pipeline = build_pipeline(config, skip_gates=True, from_stage=3, until_stage=5)
    graph = pipeline.get_graph()
    node_ids = list(graph.nodes)
    assert "stage1" not in node_ids
    assert "stage2" not in node_ids
    assert "stage3" in node_ids
    assert "stage4" in node_ids
    assert "stage5" in node_ids
    assert "stage6" not in node_ids


def test_pipeline_invalid_from_stage():
    with pytest.raises(ValueError, match="from_stage must be 1-6"):
        build_pipeline(from_stage=0)


def test_pipeline_invalid_until_stage():
    with pytest.raises(ValueError, match="until_stage must be 1-6"):
        build_pipeline(until_stage=7)


def test_pipeline_from_stage_greater_than_until_stage():
    with pytest.raises(ValueError, match="from_stage.*must be <= until_stage"):
        build_pipeline(from_stage=3, until_stage=1)
