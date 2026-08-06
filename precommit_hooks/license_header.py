#!/usr/bin/env python3
"""Pre-commit hook: ensure every source file carries the Zebroo license header.

The Zebroo Sync License requires the copyright/license notice to be present in
all copies of the software, so every source file starts with it:

    # Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

The hook inserts the header when it is missing (and reports the file as
changed, like any other pre-commit fixer). Comment syntax is derived from the
file extension. ``__manifest__.py`` is skipped -- the license is a manifest key
there.

In Python files the header goes below a shebang and/or an encoding line, in XML
below the XML declaration; everywhere else it becomes the very first line.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_TEXT = (
    "Part of Zebroo GmbH. See LICENSE file for full copyright and licensing "
    "details (www.zebroo.de/license)."
)

# extension -> (prefix, suffix)
COMMENT_STYLES = {
    ".py": ("# ", ""),
    ".xml": ("<!-- ", " -->"),
    ".js": ("// ", ""),
    ".ts": ("// ", ""),
    ".scss": ("// ", ""),
    ".css": ("/* ", " */"),
}

SKIP_NAMES = {"__manifest__.py"}


def header_line(suffix: str, text: str) -> str:
    prefix, closing = COMMENT_STYLES[suffix]
    return f"{prefix}{text}{closing}"


def insert_at(lines: list[str], suffix: str) -> int:
    """Return the index the header must be inserted at."""
    if suffix == ".xml":
        # the XML declaration has to stay on line 1
        for i, line in enumerate(lines[:2]):
            if line.lstrip().startswith("<?xml"):
                return i + 1
        return 0
    if suffix == ".py":
        idx = 0
        if lines and lines[0].startswith("#!"):
            idx = 1
        if len(lines) > idx and "coding" in lines[idx] and lines[idx].startswith("#"):
            idx += 1
        return idx
    if suffix in (".js", ".ts"):
        # Odoo matches /** @odoo-module ... */ at the very beginning of the
        # file (ODOO_MODULE_RE.match), so alias=/default= would be lost if we
        # pushed it down -- the header goes below it.
        for i, line in enumerate(lines[:2]):
            if "@odoo-module" in line:
                return i + 1
    return 0


def process(path: Path, text: str, check_only: bool) -> bool:
    """Return True if the file was missing the header."""
    suffix = path.suffix
    if suffix not in COMMENT_STYLES or path.name in SKIP_NAMES:
        return False

    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False

    if not content.strip():
        return False
    if text in "\n".join(content.splitlines()[:5]):
        return False

    lines = content.splitlines()
    idx = insert_at(lines, suffix)
    new = header_line(suffix, text)
    # keep a blank line between header and code, unless there already is one
    block = [new] if idx < len(lines) and not lines[idx].strip() else [new, ""]
    lines[idx:idx] = block

    if not check_only:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filenames", nargs="*")
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="header text without comment characters",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="only report missing headers, do not modify files",
    )
    args = parser.parse_args(argv)

    touched = [p for p in map(Path, args.filenames) if process(p, args.text, args.check_only)]
    if not touched:
        return 0

    verb = "missing in" if args.check_only else "added to"
    print(f"License header {verb}:")
    for path in touched:
        print(f"  {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
