# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
"""Generated jobs use the transferred workflow repository and retain versions."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


def test_generated_workflows_use_new_owner(tmp_path, monkeypatch):
    source = Path(__file__).parents[1] / "precommit_hooks/make_odoo_tests.py"
    spec = importlib.util.spec_from_file_location("generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    workflow = tmp_path / "tests.yml"
    workflow.write_text(yaml.safe_dump({"name": "CI", "jobs": {}}))
    monkeypatch.setattr(sys, "argv", [str(source), str(workflow), "7", "3"])

    def list_tests(command, **kwargs):
        case = "tests/suite.robot" if "robot" in command else "tests/model.py"
        return f"!!!\n{case}\n!!!"

    monkeypatch.setattr(subprocess, "check_output", list_tests)
    generator.main()
    parsed = yaml.safe_load(workflow.read_text())
    jobs = parsed["jobs"]
    assert len(jobs) == 4
    assert jobs["run_robo_tests_suite_robot"]["uses"] == (
        "zebroo-tools/git-workflows/.github/workflows/robotests.yml@v9.4"
    )
    assert jobs["run_unit_tests_model_py"]["uses"] == (
        "zebroo-tools/git-workflows/.github/workflows/unittests.yml@v9.4"
    )
    assert jobs["all_robotests"]["needs"] == ["run_robo_tests_suite_robot"]
    assert jobs["all_unittests"]["needs"] == ["run_unit_tests_model_py"]
