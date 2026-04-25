#!/usr/bin/env python3
"""
yaml_to_csv.py — Convert Anki entry YAML files to Anki-importable CSV files.

Each YAML entry file must live inside an `entries/` directory that also
contains an `entries-config.yaml` file defining the canonical field list
for that Note Type.

Usage:
    # Convert all YAML entry files in the repository
    python tools/yaml_to_csv.py

    # Convert a single file
    python tools/yaml_to_csv.py --file note-types/Japanese_Mined_Vocab/entries/001_明日は遠足.yaml

See tools/README.md for full documentation.
"""

import argparse
import csv
import io
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Error: PyYAML is not installed. Run: pip install pyyaml")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONFIG_FILENAME = "entries-config.yaml"
ENTRIES_DIR_NAME = "entries"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_config(entries_dir: Path) -> dict:
    """Load and validate entries-config.yaml from the given directory."""
    config_path = entries_dir / CONFIG_FILENAME
    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing config file: {config_path}\n"
            f"Every entries/ directory must contain an '{CONFIG_FILENAME}'."
        )

    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(
            f"Invalid config file (expected a YAML mapping): {config_path}"
        )

    notetype = config.get("notetype")
    if not notetype:
        raise ValueError(
            f"Config file is missing required key 'notetype': {config_path}"
        )

    raw_fields = config.get("fields")
    if not raw_fields or not isinstance(raw_fields, list):
        raise ValueError(
            f"Config file is missing or has empty 'fields' list: {config_path}"
        )

    fields = []
    for i, field in enumerate(raw_fields):
        if not isinstance(field, dict) or "name" not in field:
            raise ValueError(
                f"Config file field #{i + 1} is missing 'name' key: {config_path}"
            )
        fields.append(
            {
                "name": field["name"],
                "required": bool(field.get("required", False)),
            }
        )

    if not fields:
        raise ValueError(f"Config file defines zero fields: {config_path}")

    return {
        "notetype": notetype,
        "fields": fields,
        "config_path": config_path,
    }


# ---------------------------------------------------------------------------
# YAML entry file loading
# ---------------------------------------------------------------------------


def load_entry_yaml(yaml_path: Path) -> dict:
    """
    Parse a YAML entry file.

    Lines beginning with '#' are stripped before parsing so that legacy
    files with Anki CSV-style comment headers at the top are handled
    gracefully.
    """
    raw = yaml_path.read_text(encoding="utf-8")
    stripped_lines = [line for line in raw.splitlines() if not line.startswith("#")]
    content = "\n".join(stripped_lines)

    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError(f"Entry file does not contain a YAML mapping: {yaml_path}")

    return data


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_entries(entries: list | None, fields: list, yaml_path: Path) -> None:
    """
    Validate all entries against the field config.

    Raises ValueError with a descriptive message on the first violation.
    """
    if not isinstance(entries, list) or len(entries) == 0:
        raise ValueError(
            f"Entry file has no entries under the 'entries' key: {yaml_path}"
        )

    id_field_name = fields[0]["name"]
    field_names = {f["name"] for f in fields}
    required_field_names = {f["name"] for f in fields if f["required"]}

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry #{idx + 1} in {yaml_path} is not a YAML mapping.")

        # Determine a human-readable label for error messages.
        id_value = entry.get(id_field_name)
        entry_label = f"'{id_value}'" if id_value else f"entry #{idx + 1} (no ID)"

        # Rule 1: The first field (ID field) must never be empty.
        if not id_value or (isinstance(id_value, str) and not id_value.strip()):
            raise ValueError(
                f"[{yaml_path.name}] {entry_label}: "
                f"The ID field '{id_field_name}' must not be empty."
            )

        # Rule 1b: The ID field must be a string.
        # YAML parses unquoted values like 001_0001 as octal integers.
        # Require authors to quote ID values (e.g. VocabID: "001_0001").
        if not isinstance(id_value, str):
            raise ValueError(
                f"[{yaml_path.name}] entry #{idx + 1}: "
                f"The ID field '{id_field_name}' has value {id_value!r} which was "
                f"parsed by YAML as a {type(id_value).__name__}, not a string. "
                f"Wrap the value in quotes to force string parsing "
                f'(e.g. {id_field_name}: "{id_value}").'
            )

        # Rule 2: Unknown fields (present in entry but not in config).
        unknown = set(entry.keys()) - field_names
        if unknown:
            raise ValueError(
                f"[{yaml_path.name}] {entry_label}: "
                f"Unknown field(s) not declared in '{CONFIG_FILENAME}': "
                f"{', '.join(sorted(unknown))}"
            )

        # Rule 3: Required fields must be present and non-empty.
        for field_name in required_field_names:
            value = entry.get(field_name)
            is_empty = value is None or (isinstance(value, str) and not value.strip())
            if is_empty:
                raise ValueError(
                    f"[{yaml_path.name}] {entry_label}: "
                    f"Required field '{field_name}' is missing or empty."
                )


# ---------------------------------------------------------------------------
# CSV generation
# ---------------------------------------------------------------------------


def entry_to_row(entry: dict, fields: list) -> list:
    """Convert a single entry dict to a CSV row (list of strings)."""
    row = []
    for field in fields:
        value = entry.get(field["name"])
        if value is None:
            row.append("")
        else:
            # Always stringify and strip trailing whitespace/newlines.
            # Stripping handles YAML block scalars (|) which append a newline.
            cell = str(value).strip()
            # Convert internal newlines to <br> tags for HTML rendering in Anki.
            cell = cell.replace("\r\n", "\n").replace("\n", "<br>")
            row.append(cell)
    return row


def compute_tags_column(fields: list) -> int | None:
    """Return the 1-based column index of the Tags field, or None if absent."""
    for i, field in enumerate(fields):
        if field["name"] == "Tags":
            return i + 1
    return None


def build_csv(data: dict, fields: list) -> str:
    """
    Build the full CSV content string (including Anki header lines) for one
    entry YAML file.
    """
    notetype = data.get("notetype", "")
    deck = data.get("deck", "")
    entries = data.get("entries", [])

    field_names = [f["name"] for f in fields]
    tags_col = compute_tags_column(fields)

    buf = io.StringIO()

    # Anki import directive headers.
    buf.write(f"#notetype:{notetype}\n")
    buf.write(f"#deck:{deck}\n")
    buf.write("#separator:Comma\n")
    buf.write("#html:true\n")
    if tags_col is not None:
        buf.write(f"#tags column:{tags_col}\n")
    buf.write(f"#columns:{','.join(field_names)}\n")

    # Data rows.
    writer = csv.writer(buf, lineterminator="\n")
    for entry in entries:
        writer.writerow(entry_to_row(entry, fields))

    return buf.getvalue()


# ---------------------------------------------------------------------------
# File conversion
# ---------------------------------------------------------------------------


def convert_file(yaml_path: Path) -> None:
    """Convert a single YAML entry file to its CSV counterpart."""
    entries_dir = yaml_path.parent

    config = load_config(entries_dir)
    fields = config["fields"]

    data = load_entry_yaml(yaml_path)

    # Validate that the file's declared notetype matches the config.
    file_notetype = data.get("notetype", "")
    if file_notetype != config["notetype"]:
        raise ValueError(
            f"[{yaml_path.name}] 'notetype' value '{file_notetype}' does not match "
            f"the config's notetype '{config['notetype']}'."
        )

    if not data.get("deck"):
        raise ValueError(f"[{yaml_path.name}] Missing required top-level key 'deck'.")

    entries = data.get("entries")
    validate_entries(entries, fields, yaml_path)

    csv_content = build_csv(data, fields)

    csv_path = yaml_path.with_suffix(".csv")
    csv_path.write_text(csv_content, encoding="utf-8")

    print(
        f"Converted {len(entries)} entr{'y' if len(entries) == 1 else 'ies'} -> {csv_path}"
    )


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def find_entry_yaml_files(repo_root: Path) -> list[Path]:
    """
    Recursively find all *.yaml files whose parent directory is named
    'entries', excluding entries-config.yaml itself.
    """
    results = []
    for yaml_path in sorted(repo_root.rglob("*.yaml")):
        if (
            yaml_path.parent.name == ENTRIES_DIR_NAME
            and yaml_path.name != CONFIG_FILENAME
        ):
            results.append(yaml_path)
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Anki entry YAML files to Anki-importable CSV files."
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="Convert a single YAML entry file instead of discovering all files.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent

    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = Path.cwd() / target
        try:
            convert_file(target)
        except (ValueError, FileNotFoundError) as exc:
            sys.exit(f"Error: {exc}")
    else:
        yaml_files = find_entry_yaml_files(repo_root)
        if not yaml_files:
            print("No YAML entry files found.")
            return

        success = 0
        failure = 0
        for yaml_path in yaml_files:
            try:
                convert_file(yaml_path)
                success += 1
            except (ValueError, FileNotFoundError) as exc:
                print(f"Error: {exc}", file=sys.stderr)
                failure += 1

        print(f"\nDone: {success} succeeded, {failure} failed.")
        if failure:
            sys.exit(1)


if __name__ == "__main__":
    main()
