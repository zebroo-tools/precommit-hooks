#!/usr/bin/env python3
"""Pre-commit hook: every changed Odoo module needs a patchnote fragment.

For each changed file that belongs to an Odoo module (a top level directory
containing ``__manifest__.py``), verify that the module has at least one
``.patchnotes/*.yml`` fragment and that the fragments are valid.

Fragment format (``<module>/.patchnotes/<name>.yml``)::

    type: minor | major
    breaking: true | false
    description: |
      Short description of the change

The file list comes from pre-commit; when the hook is called without file names
it falls back to the staged files, so it can also be run by hand.

Previously this lived as ``res/check_patchnotes.py`` in every repo separately.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# top level directories that never require patchnotes
DEFAULT_IGNORED = [
    "addons_OCA",
    "addons_robot",
    "addons_tools",
    "odoo",
    "enterprise",
    ".github",
    "res",
    "tests",
    "testdocs",
    "test_flows",
    "sample_flows",
    "robot-output",
    "results",
    "node_modules",
    ".vscode",
]


def repo_root() -> Path:
    return Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
    )


def staged_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        text=True,
    )
    return [Path(f) for f in output.strip().splitlines() if f]


def module_for_file(filepath: Path, root: Path, ignored: set[str]) -> str | None:
    """Return the top level module directory for a file, or None."""
    parts = filepath.parts
    if not parts:
        return None
    top = parts[0]
    if top in ignored or top.startswith("."):
        return None
    if not (root / top / "__manifest__.py").is_file():
        return None
    return top


def module_has_patchnote(module: str, root: Path) -> bool:
    patchnotes_dir = root / module / ".patchnotes"
    return patchnotes_dir.is_dir() and any(patchnotes_dir.glob("*.yml"))


def validate_patchnote_files(module: str, root: Path) -> list[str]:
    """Validate all patchnote fragments of a module, return a list of errors."""
    try:
        import yaml
    except ImportError:
        return []

    errors = []
    for f in sorted((root / module / ".patchnotes").glob("*.yml")):
        try:
            data = yaml.safe_load(f.read_text())
        except Exception as e:
            errors.append(f"{f.name}: invalid YAML: {e}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{f.name}: must be a YAML mapping")
            continue
        if data.get("type") not in ("minor", "major"):
            errors.append(f"{f.name}: 'type' must be 'minor' or 'major'")
        if data.get("breaking") not in (True, False):
            errors.append(f"{f.name}: 'breaking' must be true or false")
        if not str(data.get("description") or "").strip():
            errors.append(f"{f.name}: 'description' must not be empty")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filenames", nargs="*")
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="additional top level directory to ignore (repeatable)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    ignored = set(DEFAULT_IGNORED) | set(args.ignore)
    files = [Path(f) for f in args.filenames] or staged_files()

    modules_changed = set()
    for filepath in files:
        if ".patchnotes" in filepath.parts:
            continue
        module = module_for_file(filepath, root, ignored)
        if module:
            modules_changed.add(module)

    missing = []
    validation_errors = {}
    for module in sorted(modules_changed):
        if not module_has_patchnote(module, root):
            missing.append(module)
            continue
        errs = validate_patchnote_files(module, root)
        if errs:
            validation_errors[module] = errs

    if not missing and not validation_errors:
        return 0

    if missing:
        print("\n\033[1;31m✗ Missing patchnotes for changed modules:\033[0m\n")
        for module in missing:
            print(f"  \033[1m{module}\033[0m")
        print(
            "\n  Create a patchnote fragment file:\n"
            "\n"
            "    mkdir -p <module>/.patchnotes\n"
            "    cat > <module>/.patchnotes/<short-name>.yml << 'EOF'\n"
            "    type: minor        # minor | major\n"
            "    breaking: false\n"
            "    description: |\n"
            "      Short description of the change\n"
            "    EOF\n"
        )

    if validation_errors:
        print("\n\033[1;31m✗ Invalid patchnote files:\033[0m\n")
        for module, errs in validation_errors.items():
            print(f"  \033[1m{module}\033[0m:")
            for err in errs:
                print(f"    {err}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
