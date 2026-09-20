"""Regression wrapper for the deterministic final-acceptance scenario."""

from scripts.final_acceptance import run_acceptance


def test_final_acceptance_scenario_passes():
    result = run_acceptance()
    assert result["results"]["passed"] is True
    assert result["results"]["checks_passed"] == result["results"]["checks_total"]
    assert result["results"]["primary_bridge"]["node_id"] == "X"
    assert result["results"]["workflow_status"] == "COMPLETED"
