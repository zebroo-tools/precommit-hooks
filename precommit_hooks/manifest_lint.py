#!/usr/bin/env python3
"""Pre-commit hook: lint ``__manifest__.py`` files with pylint-odoo.

Only the manifest-related checks are enabled -- the goal is a correct manifest
(above all a correct ``license``), not a full pylint run over the code base.

Default policy:

* ``license`` must be present and must be ``Other proprietary``
* ``author`` must be a string containing ``Zebroo GmbH``
* no deprecated keys (``description``), no keys that just repeat the default
* ``summary`` on one line, no file listed twice in ``data``/``demo``

The version-format check is off by default: several of our repos use the short
form (``1.13``) which Odoo accepts because it prepends the series. Enable it
per repo with ``--check-version-format`` once the repo has been converted.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CHECKS = [
    "manifest-required-key",
    "license-allowed",
    "manifest-author-string",
    "manifest-deprecated-key",
    "manifest-superfluous-key",
    "manifest-summary-multiline",
    "manifest-data-duplicated",
    "manifest-external-assets",
]

VERSION_CHECK = "manifest-version-format"

DEFAULT_AUTHOR = "Zebroo"
DEFAULT_LICENSES = "Other proprietary"


def check_author(paths, needle):
    """Check that the author key mentions us.

    pylint-odoo's own ``manifest-required-author`` compares the comma separated
    authors exactly, which does not work for the different spellings in our
    repos (``Zebroo GmbH (hello@zebroo.de)``). A case insensitive substring is
    what we actually mean.
    """
    import ast

    errors = []
    for path in paths:
        manifest = Path(path) / "__manifest__.py"
        try:
            data = ast.literal_eval(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError, SyntaxError) as e:
            errors.append(f"{manifest}: cannot be parsed: {e}")
            continue
        author = data.get("author") if isinstance(data, dict) else None
        if not isinstance(author, str) or needle.lower() not in author.lower():
            errors.append(f"{manifest}: 'author' must mention {needle!r}, found {author!r}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filenames", nargs="*", help="__manifest__.py paths")
    parser.add_argument("--required-author", default=DEFAULT_AUTHOR)
    parser.add_argument(
        "--license-allowed",
        default=DEFAULT_LICENSES,
        help="comma separated list of allowed licenses",
    )
    parser.add_argument("--check-version-format", action="store_true")
    args = parser.parse_args(argv)

    modules = sorted(
        {str(Path(f).parent) for f in args.filenames if Path(f).name == "__manifest__.py"}
    )
    if not modules:
        return 0

    author_errors = check_author(modules, args.required_author)

    checks = CHECKS + ([VERSION_CHECK] if args.check_version_format else [])
    cmd = [
        sys.executable,
        "-m",
        "pylint",
        "--load-plugins=pylint_odoo",
        "--disable=all",
        f"--enable={','.join(checks)}",
        f"--license-allowed={args.license_allowed}",
        "--score=no",
        *modules,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout + proc.stderr).strip()

    if proc.returncode == 0 and not author_errors:
        return 0
    if output:
        print(output)
    for err in author_errors:
        print(err)
    return 1


if __name__ == "__main__":
    sys.exit(main())
