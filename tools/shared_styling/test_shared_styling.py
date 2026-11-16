"""Render repository Templates with their Note Type stylesheet in headless Chrome.

Run with tools/shared_styling/.venv/bin/python tools/shared_styling/test_shared_styling.py.
Set CHROME to a Chromium-compatible browser executable when it is not on PATH.
"""

import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CHROME = os.environ.get("CHROME") or shutil.which("chromium") or shutil.which("google-chrome")
if not CHROME and Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome").is_file():
    CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class RepositoryTemplateTests(unittest.TestCase):
    def test_all_template_fields_are_in_parent_schema(self):
        special_fields = {"Tags", "Type", "Deck", "Subdeck", "Card", "CardFlag", "FrontSide"}
        for directory in sorted((ROOT / "note-types").iterdir()):
            if not directory.is_dir():
                continue
            schema = (directory / "note-type.md").read_text()
            fields = set(re.findall(r"^\|\s*\d+\s*\|\s*`([^`]+)`", schema, re.M))
            self.assertTrue(fields, f"No Fields found in {directory}")
            self.assertTrue((directory / "style.css").is_file(), directory.name)
            self.assertEqual(list((directory / "card-types").glob("*/style.css")), [])
            for template in (directory / "card-types").glob("*/*.html"):
                for reference in re.findall(r"{{\s*([#^/]?)([^{}]+?)\s*}}", template.read_text()):
                    field = reference[1].split(":")[-1].strip()
                    with self.subTest(template=template, field=field):
                        self.assertIn(field, fields | special_fields)


def render(note_type, card_type, side, fields, expression):
    directory = ROOT / "note-types" / note_type
    template = (directory / "card-types" / card_type / f"{side}.html").read_text()
    for name, value in fields.items():
        template = re.sub(r"{{#" + re.escape(name) + r"}}(.*?){{/" + re.escape(name) + r"}}", lambda m: m.group(1) if value else "", template, flags=re.S)
        template = template.replace("{{" + name + "}}", value)
    css = (directory / "style.css").read_text()
    page = f"""<!doctype html><html><head><style>{css}</style></head>
    <body class="card"><div id="content">{template}</div><pre id="result"></pre>
    <script>document.getElementById('result').textContent = JSON.stringify({expression});</script>
    </body></html>"""
    with tempfile.TemporaryDirectory() as tmp:
        page_path = Path(tmp) / "card.html"
        page_path.write_text(page)
        result = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", f"--user-data-dir={tmp}/profile", "--dump-dom", page_path.as_uri()],
            capture_output=True, text=True, check=True, timeout=30,
        )
    match = re.search(r'<pre id="result">(.*?)</pre>', result.stdout, flags=re.S)
    if not match:
        raise AssertionError(f"No rendering result: {result.stdout}")
    return json.loads(html.unescape(match.group(1)))


@unittest.skipUnless(CHROME, "headless Chrome/Chromium not available; set CHROME")
class SharedStylingPresentationTests(unittest.TestCase):
    def test_production_hint_rules_do_not_leak_to_other_content(self):
        fields = {"Sentence": "<b>猫</b>", "Meaning": "cat", "TargetWord": "猫", "Reading": "ねこ", "SentenceTranslation": "cat", "Notes": ""}
        expression = """(() => { const probe = document.createElement('span');
          probe.className = 'hint'; probe.textContent = 'probe';
          document.querySelector('.card-front').appendChild(probe);
          return getComputedStyle(probe).fontStyle; })()"""
        for card_type, expected in (("Comprehension", "normal"), ("Production", "italic")):
            for side in ("front", "back"):
                with self.subTest(card_type=card_type, side=side):
                    self.assertEqual(render("Japanese_Mined_Vocab", card_type, side, fields, expression), expected)

    def test_vocab_front_and_back_keep_distinct_presentations(self):
        fields = {"Sentence": "猫が<b>食べる</b>", "Meaning": "eat", "TargetWord": "食べる", "Reading": "たべる", "SentenceTranslation": "The cat eats", "Notes": ""}
        expression = """({margin: getComputedStyle(document.querySelector('.sentence')).marginBottom,
          bold: document.querySelector('.sentence b').textContent,
          color: getComputedStyle(document.querySelector('.sentence b')).color,
          hint: document.querySelector('.hint')?.textContent ?? null,
          meaning: document.querySelector('.meaning')?.textContent ?? null})"""
        for card_type, margin in (("Comprehension", "4px"), ("Production", "8px")):
            for side in ("front", "back"):
                with self.subTest(card_type=card_type, side=side):
                    result = render("Japanese_Mined_Vocab", card_type, side, fields, expression)
                    self.assertEqual(result["margin"], margin)
                    self.assertEqual(result["bold"], "＿＿＿" if card_type == "Production" and side == "front" else "食べる")
                    self.assertEqual(result["color"], "rgb(26, 110, 189)")
                    self.assertEqual(result["hint"], "eat" if card_type == "Production" else None)
                    self.assertEqual(result["meaning"], "eat" if card_type == "Comprehension" and side == "back" else None)

    def test_grammar_front_and_back_keep_distinct_presentations(self):
        fields = {"Sentence": "教室に<b>入ると</b>先生がいた", "Meaning_Hint": "when", "GrammarPoint": "と", "Formation": "Verb + と", "SentenceTranslation": "When I entered", "Notes": ""}
        expression = """({margin: getComputedStyle(document.querySelector('.sentence')).marginBottom,
          bold: document.querySelector('.sentence b').textContent,
          color: getComputedStyle(document.querySelector('.sentence b')).color,
          hint: document.querySelector('.hint')?.textContent ?? null,
          labels: Array.from(document.querySelectorAll('.info-label'), e => e.textContent)})"""
        for card_type, margin in (("Comprehension", "4px"), ("Production", "8px")):
            for side in ("front", "back"):
                with self.subTest(card_type=card_type, side=side):
                    result = render("Japanese_Mined_Grammar", card_type, side, fields, expression)
                    self.assertEqual(result["margin"], margin)
                    self.assertEqual(result["bold"], "＿＿＿" if card_type == "Production" and side == "front" else "入ると")
                    self.assertEqual(result["color"], "rgb(26, 110, 189)")
                    self.assertEqual(result["hint"], "when" if card_type == "Production" else None)
                    self.assertEqual(result["labels"], [] if side == "front" else (["Meaning", "Formation"] if card_type == "Comprehension" else ["Formation"]))

    def test_single_card_types_render_front_and_back(self):
        cases = (
            ("Japanese_Familiarity_Vocab", "Familiarity",
             {"DisplayWord": "猫", "Reading": "ねこ", "Meaning": "cat", "UsageLabel": "", "Source": "", "Example": "", "Notes": ""},
             "({word: document.querySelector('.display-word').textContent, size: getComputedStyle(document.querySelector('.display-word')).fontSize, meaning: document.querySelector('.meaning')?.textContent ?? null})",
             {"word": "猫", "size": "32px", "meaning": None},
             {"word": "猫", "size": "32px", "meaning": "cat"}),
            ("Japanese_Listening", "ListeningComprehension",
             {"Audio": "[sound:example.mp3]", "JapaneseSentence": "猫です", "Reading": "", "Notes": "", "Source": ""},
             "({audio: document.querySelector('.audio').textContent, sentence: document.querySelector('.sentence')?.textContent ?? null, align: getComputedStyle(document.querySelector('.audio')).textAlign})",
             {"audio": "[sound:example.mp3]", "sentence": None, "align": "center"},
             {"audio": "[sound:example.mp3]", "sentence": "猫です", "align": "center"}),
            ("Japanese_Sentence_Production", "Production",
             {"SentenceID": "001_0001", "EnglishSentence": "A cat", "JapaneseSentence": "猫です", "Notes": ""},
             "({prompt: document.querySelector('.prompt').textContent, size: getComputedStyle(document.querySelector('.prompt')).fontSize, input: !!document.querySelector('#japanese-response'), answer: document.querySelector('.japanese:not(.typed-response)')?.textContent ?? null})",
             {"prompt": "A cat", "size": "21.6px", "input": True, "answer": None},
             {"prompt": "A cat", "size": "21.6px", "input": False, "answer": "猫です"}),
        )
        for note_type, card_type, fields, expression, front, back in cases:
            for side, expected in (("front", front), ("back", back)):
                with self.subTest(note_type=note_type, side=side):
                    self.assertEqual(render(note_type, card_type, side, fields, expression), expected)


if __name__ == "__main__":
    unittest.main()
