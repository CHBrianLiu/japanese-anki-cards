"""
test_yaml_to_csv.py — Regression tests for yaml_to_csv.py.

Run from the repository root:
    python tools/test_yaml_to_csv.py
"""

import sys
import textwrap
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the module under test (same directory as this file).
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
import yaml_to_csv as m  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_config(
    tmp_path: Path, fields: list[dict], notetype: str = "TestType"
) -> None:
    """Write a minimal entries-config.yaml into tmp_path."""
    lines = [f"notetype: {notetype}", "fields:"]
    for f in fields:
        req = "true" if f.get("required", False) else "false"
        lines.append(f"  - name: {f['name']}")
        lines.append(f"    required: {req}")
    (tmp_path / m.CONFIG_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_entry(tmp_path: Path, content: str, name: str = "deck.yaml") -> Path:
    """Write a YAML entry file into tmp_path and return its Path."""
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


DEFAULT_FIELDS = [
    {"name": "ID", "required": True},
    {"name": "Word", "required": True},
    {"name": "Reading", "required": True},
    {"name": "Meaning", "required": True},
    {"name": "Notes", "required": False},
    {"name": "Tags", "required": False},
]


# ---------------------------------------------------------------------------
# Tests: load_config
# ---------------------------------------------------------------------------


class TestLoadConfig(unittest.TestCase):
    def test_valid_config(self, tmp_path=None):
        import tempfile

        tmp = Path(tempfile.mkdtemp()) if tmp_path is None else tmp_path
        write_config(tmp, DEFAULT_FIELDS)
        config = m.load_config(tmp)
        self.assertEqual(config["notetype"], "TestType")
        self.assertEqual(len(config["fields"]), 6)
        self.assertTrue(config["fields"][0]["required"])
        self.assertFalse(config["fields"][4]["required"])

    def test_missing_config_file(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        with self.assertRaises(FileNotFoundError) as ctx:
            m.load_config(tmp)
        self.assertIn("entries-config.yaml", str(ctx.exception))

    def test_missing_notetype_key(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        (tmp / m.CONFIG_FILENAME).write_text(
            "fields:\n  - name: ID\n    required: true\n"
        )
        with self.assertRaises(ValueError) as ctx:
            m.load_config(tmp)
        self.assertIn("notetype", str(ctx.exception))

    def test_missing_fields_key(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        (tmp / m.CONFIG_FILENAME).write_text("notetype: Test\n")
        with self.assertRaises(ValueError) as ctx:
            m.load_config(tmp)
        self.assertIn("fields", str(ctx.exception))

    def test_field_missing_name_key(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        (tmp / m.CONFIG_FILENAME).write_text(
            "notetype: Test\nfields:\n  - required: true\n"
        )
        with self.assertRaises(ValueError) as ctx:
            m.load_config(tmp)
        self.assertIn("name", str(ctx.exception))


# ---------------------------------------------------------------------------
# Tests: load_entry_yaml
# ---------------------------------------------------------------------------


class TestLoadEntryYaml(unittest.TestCase):
    def test_pure_yaml(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = write_entry(
            tmp,
            """\
            notetype: TestType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
        """,
        )
        data = m.load_entry_yaml(p)
        self.assertEqual(data["notetype"], "TestType")
        self.assertEqual(data["deck"], "TestDeck")
        self.assertEqual(len(data["entries"]), 1)

    def test_legacy_hybrid_format_comment_lines_stripped(self):
        """Files with Anki CSV comment headers at the top should be parsed correctly."""
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = write_entry(
            tmp,
            """\
            #notetype:TestType
            #deck:TestDeck
            #separator:Comma
            #html:true
            #tags column:6
            #columns:ID,Word,Reading,Meaning,Notes,Tags
            notetype: TestType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
        """,
        )
        data = m.load_entry_yaml(p)
        self.assertEqual(data["notetype"], "TestType")
        self.assertEqual(len(data["entries"]), 1)

    def test_invalid_yaml_not_a_mapping(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = write_entry(tmp, "- just\n- a\n- list\n")
        with self.assertRaises(ValueError) as ctx:
            m.load_entry_yaml(p)
        self.assertIn("YAML mapping", str(ctx.exception))


# ---------------------------------------------------------------------------
# Tests: validate_entries
# ---------------------------------------------------------------------------


class TestValidateEntries(unittest.TestCase):
    def _path(self, name="deck.yaml"):
        return Path(name)

    def test_valid_entries(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
            {"name": "Notes", "required": False},
        ]
        entries = [
            {"ID": "001", "Word": "hello", "Notes": "some note"},
            {"ID": "002", "Word": "world"},
        ]
        # Should not raise
        m.validate_entries(entries, fields, self._path())

    def test_empty_entries_list(self):
        fields = [{"name": "ID", "required": True}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries([], fields, self._path())
        self.assertIn("no entries", str(ctx.exception))

    def test_none_entries(self):
        fields = [{"name": "ID", "required": True}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(None, fields, self._path())
        self.assertIn("no entries", str(ctx.exception))

    def test_id_field_empty_string(self):
        fields = [{"name": "ID", "required": True}, {"name": "Word", "required": True}]
        entries = [{"ID": "", "Word": "hello"}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("ID field", str(ctx.exception))
        self.assertIn("must not be empty", str(ctx.exception))

    def test_id_field_missing(self):
        fields = [{"name": "ID", "required": True}, {"name": "Word", "required": True}]
        entries = [{"Word": "hello"}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("ID field", str(ctx.exception))

    def test_id_field_non_string_aborts(self):
        """Unquoted IDs like 001_0001 become integers via YAML; the tool must reject them."""
        fields = [{"name": "ID", "required": True}, {"name": "Word", "required": True}]
        entries = [{"ID": 4097, "Word": "hello"}]  # 4097 == octal 001_0001 parsed value
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("not a string", str(ctx.exception))
        self.assertIn("quotes", str(ctx.exception))

    def test_required_field_missing(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [{"ID": "001"}]  # Word is missing
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("Word", str(ctx.exception))
        self.assertIn("missing or empty", str(ctx.exception))

    def test_required_field_present_but_empty_string(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [{"ID": "001", "Word": ""}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("Word", str(ctx.exception))
        self.assertIn("missing or empty", str(ctx.exception))

    def test_required_field_whitespace_only(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [{"ID": "001", "Word": "   "}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("Word", str(ctx.exception))

    def test_optional_field_may_be_absent(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
            {"name": "Notes", "required": False},
        ]
        entries = [{"ID": "001", "Word": "hello"}]
        # Should not raise
        m.validate_entries(entries, fields, self._path())

    def test_optional_field_may_be_null(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
            {"name": "Notes", "required": False},
        ]
        entries = [{"ID": "001", "Word": "hello", "Notes": None}]
        # Should not raise
        m.validate_entries(entries, fields, self._path())

    def test_unknown_field_in_entry(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [{"ID": "001", "Word": "hello", "Ghost": "unknown"}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("Ghost", str(ctx.exception))
        self.assertIn("Unknown field", str(ctx.exception))

    def test_error_identifies_entry_by_id(self):
        """Error messages for entries with a valid ID should include the ID value."""
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [{"ID": "abc-123", "Word": ""}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("abc-123", str(ctx.exception))

    def test_error_identifies_entry_by_index_when_id_missing(self):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [{"Word": "hello"}]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("entry #1", str(ctx.exception))

    def test_multiple_entries_second_fails(self):
        """Validation must check every entry, not just the first."""
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
        ]
        entries = [
            {"ID": "001", "Word": "hello"},
            {"ID": "002", "Word": ""},  # fails
        ]
        with self.assertRaises(ValueError) as ctx:
            m.validate_entries(entries, fields, self._path())
        self.assertIn("002", str(ctx.exception))


# ---------------------------------------------------------------------------
# Tests: compute_tags_column
# ---------------------------------------------------------------------------


class TestComputeTagsColumn(unittest.TestCase):
    def test_tags_field_present(self):
        fields = [
            {"name": "ID"},
            {"name": "Word"},
            {"name": "Tags"},
        ]
        self.assertEqual(m.compute_tags_column(fields), 3)

    def test_tags_field_absent(self):
        fields = [{"name": "ID"}, {"name": "Word"}]
        self.assertIsNone(m.compute_tags_column(fields))

    def test_tags_field_first_column(self):
        fields = [{"name": "Tags"}, {"name": "ID"}]
        self.assertEqual(m.compute_tags_column(fields), 1)


# ---------------------------------------------------------------------------
# Tests: entry_to_row
# ---------------------------------------------------------------------------


class TestEntryToRow(unittest.TestCase):
    def _fields(self):
        return [
            {"name": "ID"},
            {"name": "Word"},
            {"name": "Notes"},
        ]

    def test_all_fields_present(self):
        row = m.entry_to_row(
            {"ID": "001", "Word": "hello", "Notes": "n"}, self._fields()
        )
        self.assertEqual(row, ["001", "hello", "n"])

    def test_absent_optional_field_becomes_empty_string(self):
        row = m.entry_to_row({"ID": "001", "Word": "hello"}, self._fields())
        self.assertEqual(row, ["001", "hello", ""])

    def test_null_field_becomes_empty_string(self):
        row = m.entry_to_row(
            {"ID": "001", "Word": "hello", "Notes": None}, self._fields()
        )
        self.assertEqual(row, ["001", "hello", ""])

    def test_block_scalar_trailing_newline_stripped(self):
        """YAML block scalars (|) produce a trailing newline that must be stripped, not converted to <br>."""
        row = m.entry_to_row(
            {"ID": "001", "Word": "hello\n", "Notes": None}, self._fields()
        )
        self.assertEqual(row[1], "hello")
        self.assertNotIn("<br>", row[1])

    def test_html_tags_preserved(self):
        row = m.entry_to_row(
            {"ID": "001", "Word": "<b>始まる</b>", "Notes": None}, self._fields()
        )
        self.assertEqual(row[1], "<b>始まる</b>")

    def test_non_string_value_coerced_to_string(self):
        """Any non-string YAML value that passes validation is safely stringified."""
        row = m.entry_to_row({"ID": "001", "Word": 42, "Notes": None}, self._fields())
        self.assertEqual(row[1], "42")

    def test_multiline_value_converted_to_br(self):
        """Multi-line field values (from YAML block scalars) should convert \\n to <br>."""
        row = m.entry_to_row(
            {"ID": "001", "Word": "line one\nline two", "Notes": None}, self._fields()
        )
        self.assertEqual(row[1], "line one<br>line two")

    def test_multiline_with_crlf_converted_to_br(self):
        """Line breaks with CRLF (\\r\\n) should also be converted to <br>."""
        row = m.entry_to_row(
            {"ID": "001", "Word": "line one\r\nline two", "Notes": None}, self._fields()
        )
        self.assertEqual(row[1], "line one<br>line two")

    def test_block_scalar_trailing_newline_no_br_appended(self):
        """Trailing newlines (from YAML block scalars) should be stripped, not converted to <br>."""
        row = m.entry_to_row(
            {"ID": "001", "Word": "hello\n", "Notes": None}, self._fields()
        )
        self.assertEqual(row[1], "hello")
        self.assertNotIn("<br>", row[1])


# ---------------------------------------------------------------------------
# Tests: build_csv
# ---------------------------------------------------------------------------


class TestBuildCsv(unittest.TestCase):
    def _fields(self, include_tags=True):
        fields = [
            {"name": "ID", "required": True},
            {"name": "Word", "required": True},
            {"name": "Notes", "required": False},
        ]
        if include_tags:
            fields.append({"name": "Tags", "required": False})
        return fields

    def test_anki_headers_present(self):
        data = {
            "notetype": "MyType",
            "deck": "MyDeck",
            "entries": [{"ID": "001", "Word": "hello"}],
        }
        csv_text = m.build_csv(data, self._fields())
        self.assertIn("#notetype:MyType", csv_text)
        self.assertIn("#deck:MyDeck", csv_text)
        self.assertIn("#separator:Comma", csv_text)
        self.assertIn("#html:true", csv_text)
        self.assertIn("#tags column:4", csv_text)
        self.assertIn("#columns:ID,Word,Notes,Tags", csv_text)

    def test_tags_column_directive_omitted_when_no_tags_field(self):
        data = {
            "notetype": "MyType",
            "deck": "MyDeck",
            "entries": [{"ID": "001", "Word": "hello"}],
        }
        csv_text = m.build_csv(data, self._fields(include_tags=False))
        self.assertNotIn("#tags column:", csv_text)

    def test_data_rows_follow_headers(self):
        data = {
            "notetype": "MyType",
            "deck": "MyDeck",
            "entries": [
                {"ID": "001", "Word": "hello", "Notes": "n1", "Tags": "t1"},
                {"ID": "002", "Word": "world", "Notes": None, "Tags": None},
            ],
        }
        csv_text = m.build_csv(data, self._fields())
        lines = csv_text.splitlines()
        # Headers are lines 1-6 (0-indexed 0-5); data starts at line 6.
        self.assertEqual(lines[6], "001,hello,n1,t1")
        self.assertEqual(lines[7], "002,world,,")

    def test_csv_quoting_for_commas_in_values(self):
        """Field values containing commas must be quoted in the CSV output."""
        data = {
            "notetype": "MyType",
            "deck": "MyDeck",
            "entries": [
                {"ID": "001", "Word": "to begin, to start", "Notes": None, "Tags": None}
            ],
        }
        csv_text = m.build_csv(data, self._fields())
        self.assertIn('"to begin, to start"', csv_text)

    def test_utf8_japanese_characters_preserved(self):
        data = {
            "notetype": "MyType",
            "deck": "MyDeck",
            "entries": [{"ID": "001", "Word": "始まる", "Notes": None, "Tags": None}],
        }
        csv_text = m.build_csv(data, self._fields())
        self.assertIn("始まる", csv_text)

    def test_html_bold_tags_preserved(self):
        data = {
            "notetype": "MyType",
            "deck": "MyDeck",
            "entries": [
                {
                    "ID": "001",
                    "Word": "<b>始まっています</b>",
                    "Notes": None,
                    "Tags": None,
                }
            ],
        }
        csv_text = m.build_csv(data, self._fields())
        self.assertIn("<b>始まっています</b>", csv_text)


# ---------------------------------------------------------------------------
# Tests: convert_file (integration)
# ---------------------------------------------------------------------------


class TestConvertFile(unittest.TestCase):
    def _setup(self, tmp_path: Path, entry_content: str, fields=None):
        """Write config + entry YAML, return the entry path."""
        if fields is None:
            fields = DEFAULT_FIELDS
        write_config(tmp_path, fields)
        return write_entry(tmp_path, entry_content)

    def test_happy_path_produces_correct_csv(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = self._setup(
            tmp,
            """\
            notetype: TestType
            deck: TestDeck::Sub
            entries:
              - ID: "001_0001"
                Word: 始まる
                Reading: はじまる
                Meaning: to begin; to start
                Notes: Some note.
                Tags: grammar
        """,
        )
        m.convert_file(p)
        csv_path = p.with_suffix(".csv")
        self.assertTrue(csv_path.exists())
        content = csv_path.read_text(encoding="utf-8")
        self.assertIn("#notetype:TestType", content)
        self.assertIn("#deck:TestDeck::Sub", content)
        self.assertIn(
            "001_0001,始まる,はじまる,to begin; to start,Some note.,grammar", content
        )

    def test_csv_written_next_to_yaml(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = self._setup(
            tmp,
            """\
            notetype: TestType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
                Reading: hello
                Meaning: hello
        """,
        )
        m.convert_file(p)
        self.assertTrue(p.with_suffix(".csv").exists())
        # No stray files created elsewhere
        self.assertEqual(
            sorted(f.name for f in tmp.iterdir()),
            sorted(["entries-config.yaml", "deck.yaml", "deck.csv"]),
        )

    def test_notetype_mismatch_aborts(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = self._setup(
            tmp,
            """\
            notetype: WrongType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
                Reading: hello
                Meaning: hello
        """,
        )
        with self.assertRaises(ValueError) as ctx:
            m.convert_file(p)
        self.assertIn("WrongType", str(ctx.exception))
        self.assertIn("TestType", str(ctx.exception))

    def test_missing_deck_key_aborts(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        p = self._setup(
            tmp,
            """\
            notetype: TestType
            entries:
              - ID: "001"
                Word: hello
                Reading: hello
                Meaning: hello
        """,
        )
        with self.assertRaises(ValueError) as ctx:
            m.convert_file(p)
        self.assertIn("deck", str(ctx.exception))

    def test_legacy_hybrid_yaml_converts_correctly(self):
        """The existing 001_明日は遠足.yaml format (comment headers + YAML) must work."""
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        write_config(tmp, DEFAULT_FIELDS)
        p = write_entry(
            tmp,
            """\
            #notetype:TestType
            #deck:TestDeck
            #separator:Comma
            #html:true
            #tags column:6
            #columns:ID,Word,Reading,Meaning,Notes,Tags
            notetype: TestType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
                Reading: hello
                Meaning: hello
        """,
        )
        m.convert_file(p)
        content = p.with_suffix(".csv").read_text(encoding="utf-8")
        self.assertIn("#notetype:TestType", content)
        self.assertIn("001,hello,hello,hello,,", content)

    def test_single_entry_produces_singular_output_message(self, capsys=None):
        import tempfile, io
        from contextlib import redirect_stdout

        tmp = Path(tempfile.mkdtemp())
        p = self._setup(
            tmp,
            """\
            notetype: TestType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
                Reading: hello
                Meaning: hello
        """,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            m.convert_file(p)
        self.assertIn("1 entry", buf.getvalue())

    def test_multiple_entries_produce_plural_output_message(self):
        import tempfile, io
        from contextlib import redirect_stdout

        tmp = Path(tempfile.mkdtemp())
        p = self._setup(
            tmp,
            """\
            notetype: TestType
            deck: TestDeck
            entries:
              - ID: "001"
                Word: hello
                Reading: hello
                Meaning: hello
              - ID: "002"
                Word: world
                Reading: world
                Meaning: world
        """,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            m.convert_file(p)
        self.assertIn("2 entries", buf.getvalue())


# ---------------------------------------------------------------------------
# Tests: find_entry_yaml_files
# ---------------------------------------------------------------------------


class TestFindEntryYamlFiles(unittest.TestCase):
    def test_finds_yaml_files_in_entries_dirs(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        entries = tmp / "note-types" / "MyType" / "entries"
        entries.mkdir(parents=True)
        (entries / "deck1.yaml").touch()
        (entries / "deck2.yaml").touch()
        (entries / m.CONFIG_FILENAME).touch()  # must be excluded

        found = m.find_entry_yaml_files(tmp)
        names = {p.name for p in found}
        self.assertIn("deck1.yaml", names)
        self.assertIn("deck2.yaml", names)
        self.assertNotIn(m.CONFIG_FILENAME, names)

    def test_ignores_yaml_files_outside_entries_dir(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        (tmp / "config.yaml").touch()  # root level — not in entries/
        entries = tmp / "entries"
        entries.mkdir()
        (entries / "deck.yaml").touch()

        found = m.find_entry_yaml_files(tmp)
        names = {p.name for p in found}
        self.assertIn("deck.yaml", names)
        self.assertNotIn("config.yaml", names)

    def test_returns_empty_list_when_no_files(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        self.assertEqual(m.find_entry_yaml_files(tmp), [])

    def test_discovers_multiple_note_types(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        for nt in ("TypeA", "TypeB"):
            e = tmp / "note-types" / nt / "entries"
            e.mkdir(parents=True)
            (e / "deck.yaml").touch()
            (e / m.CONFIG_FILENAME).touch()
        found = m.find_entry_yaml_files(tmp)
        self.assertEqual(len(found), 2)


# ---------------------------------------------------------------------------
# End-to-end: real repository files
# ---------------------------------------------------------------------------


class TestRealRepositoryFiles(unittest.TestCase):
    """Smoke test against the actual files in the repository."""

    REPO_ROOT = Path(__file__).resolve().parent.parent

    def test_japanese_mined_vocab_converts_without_error(self):
        yaml_path = (
            self.REPO_ROOT
            / "note-types"
            / "Japanese_Mined_Vocab"
            / "entries"
            / "001_明日は遠足.yaml"
        )
        if not yaml_path.exists():
            self.skipTest("Real entry file not found; skipping.")
        # Should not raise
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            m.convert_file(yaml_path)
        self.assertIn("entries", buf.getvalue())

    def test_generated_csv_matches_expected_content(self):
        repo = self.REPO_ROOT
        yaml_path = (
            repo
            / "note-types"
            / "Japanese_Mined_Vocab"
            / "entries"
            / "001_明日は遠足.yaml"
        )
        if not yaml_path.exists():
            self.skipTest("Real entry file not found; skipping.")

        import io
        from contextlib import redirect_stdout

        with redirect_stdout(io.StringIO()):
            m.convert_file(yaml_path)

        csv_path = yaml_path.with_suffix(".csv")
        content = csv_path.read_text(encoding="utf-8")

        # Anki directive headers
        self.assertIn("#notetype:Japanese_Mined_Vocab", content)
        self.assertIn("#deck:Japanese::Todoku::明日は遠足", content)
        self.assertIn("#separator:Comma", content)
        self.assertIn("#html:true", content)
        self.assertIn("#tags column:8", content)
        self.assertIn(
            "#columns:VocabID,TargetWord,Reading,Meaning,Sentence,"
            "SentenceTranslation,Notes,Tags",
            content,
        )

        # Entry 001_0001
        self.assertIn("001_0001", content)
        self.assertIn("始まる", content)
        self.assertIn("<b>始まっています</b>", content)
        self.assertIn("Intransitive verb", content)

        # Entry 001_0002
        self.assertIn("001_0002", content)
        self.assertIn("起こす", content)
        self.assertIn("<b>起こしてくれなかった</b>", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
