# 🧹 precommit-xml-tools

This repository provides `pre-commit` hooks for formatting XML files using `xmlstarlet` and sorting attributes using `xsltproc`.

---

## ✅ Hooks Included

### 1. `xmlstarlet-format`

Formats XML files with consistent indentation using `xmlstarlet`.

- **Command:** `xmlstarlet fo --indent-spaces 4`
- **Effect:** Pretty-prints XML with 4-space indentation
- **Requirement:** `xmlstarlet`

### 2. `sort-xml`

Sorts XML element attributes alphabetically using XSLT, and then formats the result with `xmlstarlet`.

- **Command:** `xsltproc sort-attrs.xslt | xmlstarlet fo`
- **Effect:** Alphabetically orders attributes in each element and formats
- **Requirement:** `xsltproc`, `xmlstarlet`

### 3. `github-workflow for robo and unit tests`

```
  - repo: https://github.com/Odoo-Ninjas/precommit-hooks
    rev: main
    hooks:
      - id: make_odoo_robot_tests_githubworkflow
        args:
          - .github/workflows/testing.yml
```

---

## 🔧 Usage

1. Install required tools:
   ```bash
   brew install xmlstarlet libxslt   # macOS
   sudo apt install xmlstarlet xsltproc  # Debian/Ubuntu
---

## Zebroo hooks

### `zebroo-license-header`

Setzt den Zebroo-Lizenz-Header als erste Zeile in jede Quelldatei (py, xml, js,
ts, scss, css) — die Zebroo Sync License verlangt den Hinweis in allen Kopien.
Fehlt er, wird er eingefuegt (Fixer, wie black).

```yaml
- repo: https://github.com/Odoo-Ninjas/precommit-hooks
  rev: <tag>
  hooks:
    - id: zebroo-license-header
```

- In Python steht der Header unter Shebang/Encoding-Zeile, in XML unter der
  XML-Deklaration, in JS unter einem fuehrenden `/** @odoo-module ... */`
  (sonst wuerde Odoo `alias=`/`default=` nicht mehr erkennen).
- `__manifest__.py` wird uebersprungen — dort steht die Lizenz als Key.
- Optionen: `--text "<eigener Text>"`, `--check-only` (nur melden, nichts aendern).

### `zebroo-manifest-lint`

Prueft `__manifest__.py` mit pylint-odoo — nur die Manifest-Checks, kein
Full-Lint. Vor allem: `license` vorhanden und erlaubt.

```yaml
- repo: https://github.com/Odoo-Ninjas/precommit-hooks
  rev: <tag>
  hooks:
    - id: zebroo-manifest-lint
```

- Default: `license` muss `Other proprietary` sein, `author` muss `Zebroo`
  enthalten (Teilstring, case-insensitive).
- Ausserdem aktiv: `manifest-required-key`, `manifest-author-string`,
  `manifest-deprecated-key`, `manifest-superfluous-key`,
  `manifest-summary-multiline`, `manifest-data-duplicated`,
  `manifest-external-assets`.
- Optionen: `--license-allowed "Other proprietary,AGPL-3"`,
  `--required-author "Zebroo"`, `--check-version-format` (aus per Default, weil
  einige Repos noch die kurze Version `1.13` nutzen).

### `zebroo-check-patchnotes`

Jedes geaenderte Odoo-Modul braucht ein `.patchnotes/<name>.yml`-Fragment
(`type`, `breaking`, `description`); vorhandene Fragmente werden validiert.
Loest die bisherigen repo-lokalen Kopien von `res/check_patchnotes.py` ab.

```yaml
- repo: https://github.com/Odoo-Ninjas/precommit-hooks
  rev: <tag>
  hooks:
    - id: zebroo-check-patchnotes
      args: [--ignore, mein_sonderordner]
```
