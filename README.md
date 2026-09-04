# Provenance — Document Verification System

Detects whether a document someone submits (e.g. a candidate's "experience
letter") has been edited compared to the original issued by their previous
employer — and shows exactly what changed, sentence by sentence.

Built for the scenario: *Company A employed Yash Gupta as a Software
Engineer. Yash edits his experience letter to say "Senior Software
Engineer" before applying to Company B. Company B looks up the original
record Company A registered, uploads Yash's submitted copy, and the system
flags the exact discrepancy.*

---

## Structure

```
doc-verify/
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py          <- FastAPI app, all routes
│       ├── models.py        <- SQLAlchemy models (SQLite)
│       ├── diff_engine.py   <- sentence-level diff, the core detection logic
│       ├── extract.py       <- .txt/.docx/.pdf text extraction
│       └── hashchain.py     <- makes original records tamper-proof
└── frontend/
    └── index.html           <- single-page UI, no build step
```

---

## Running it in VS Code

**Important:** use Python 3.12 or 3.11 for the venv, not 3.13/3.14 — some
packages don't have pre-built installers for the newest Python yet. Check
your version with `python --version` first. If you already installed
Python 3.12 while setting up the previous project, reuse it.

### 1. Open the folder
`File > Open Folder...` → select `doc-verify`.

### 2. Terminal setup (in `backend/`)
```bash
cd backend
py -3.12 -m venv venv
source venv/Scripts/activate      # Git Bash / Mac / Linux
# or venv\Scripts\activate        # plain Windows CMD
pip install -r requirements.txt
```

### 3. Run the backend
```bash
uvicorn app.main:app --reload
```
Leave this terminal running. A `docverify.db` file will appear automatically.

### 4. Open the frontend
Double-click `frontend/index.html`, or use the VS Code "Live Server"
extension (right-click the file → "Open with Live Server").

---

## How to demo it

1. **Tab 1 — "Company A: Issue record."** Register an original record for
   "Yash Gupta" — upload any .txt/.docx/.pdf describing him as a "Software
   Engineer." This locks in the source-of-truth text.
2. Make a **second file** that's nearly identical but changes his title to
   "Senior Software Engineer" (and maybe adds a fake claim, like "led a
   team of five"). This simulates the doctored document Yash gives Company B.
3. **Tab 2 — "Company B: Verify candidate."** Search for "Yash," note the
   record ID, then upload the doctored file and run verification.
4. You'll see the **verdict, match %, and the exact sentence-level diff** —
   original vs. submitted, side by side, exactly where they differ.
5. **Tab 3 — "Record integrity."** Click "Verify entire chain" (valid).
   Then use the tamper button to simulate Company A itself editing the
   record afterward, and verify again — the chain breaks and names exactly
   which record was altered. This shows the system protects the *original*
   record too, not just candidate submissions.

---

## Where the real work is (for your report / viva)

- **Sentence-level diffing** (`diff_engine.py`) uses Python's `difflib`
  (Myers diff algorithm) rather than a raw text comparison — this is what
  lets it say "this specific sentence changed" instead of just "these
  documents are 80% similar." Explain why sentence granularity matters for
  a system like this (word-level would be noisy; paragraph-level would
  miss small but critical edits like a job title).
- **Design decision to justify:** matching is done by *content*, not by
  file identity. Two files with completely different filenames or
  formatting will still be compared correctly, because both get converted
  to plain text before comparison.
- **Threat model to state explicitly in your report:** this detects
  *edits to a specific known original*. It does not (on its own) verify
  that the *original* record itself was truthful when issued — if Company
  A's HR made an error or was complicit in a lie originally, this system
  won't catch that. It also doesn't verify the *issuer's* identity — a
  production version would need Company A to authenticate before
  registering records. Naming this limitation clearly is a strong thing to
  say in your defense.
- **Extending it:** add authentication so only verified HR accounts can
  register records for their own company; add PDF metadata/font analysis
  as a second signal (crude edits often change font or embedded metadata);
  generate a downloadable PDF verification report.
