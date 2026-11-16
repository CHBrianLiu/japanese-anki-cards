# Shared styling checks

Each Note Type has one `style.css` alongside `note-type.md`; its Card Types keep
their own Front and Back Templates.

## Setup

This tool uses only the Python standard library. Prepare its virtual environment
from the repository root:

```bash
python3 -m venv tools/shared_styling/.venv
```

## Usage

Run the Template and rendering checks from the repository root:

```bash
tools/shared_styling/.venv/bin/python tools/shared_styling/test_shared_styling.py
```

The rendering checks use headless Chrome or Chromium with a temporary browser
profile. Set `CHROME` to its executable if it is not on `PATH`. They are skipped
when no browser is available; the Template Field checks still run. The browser test uses synthetic
Field values, not an Anki Collection, and does not emulate Anki's audio controls,
mobile clients, or all Template features.

Before adopting a styling change, use a **disposable** test Collection on each
intended Anki client. Install the shared stylesheet once on each Note Type and
the separate Front/Back Templates in the documented Card Type order. Check:

1. Both sides of Comprehension and Production for mined vocabulary and grammar:
   blue answer spans, Production blanking and hints, and their distinct sentence
   spacing. Verify the Comprehension presentation has no Production styling.
2. Both sides of Familiarity, Listening, and Sentence Production, including
   optional content and their intended prompt/answer visibility.
3. Narrow screens and night mode where supported, audio replay for Listening,
   and typing/response preservation for Sentence Production.

These client checks supplement, rather than replace, the automated rendering test.
