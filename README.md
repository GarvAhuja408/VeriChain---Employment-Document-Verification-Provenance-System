# Provenance — Document Verification System

A document verification system built wit Python and FastAPI that detects whether a submitted document has been modified from its original registered version.

It can be used for verifying documents such as experience letters, certificates, and employment records.

## Features

* Upload and extract text from `.txt`, `.pdf`, and `.docx` files
* Compare original and submitted documents
* Detect changes at the sentence level
* Calculate document similarity
* Show exact differences
* Store original records securely
* Detect tampering using : SHA-256 hash chaining

## Tech Stack

* Python
* FastAPI
* SQLAlchemy
* SQLite
* SHA-256
* HTML, CSS, JavaScript

## Project Structure

doc-verify/
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── diff_engine.py
│       ├── extract.py
│       └── hashchain.py
│
└── frontend/
    └── index.html


## How It Works

1. Register the original document.
2. Upload the document submitted by the candidate.
3. The system extracts and compares the text.
4. Differences are detected sentence by sentence.
5. The system displays the similarity and exact changes.
6. The hash chain can be verified to detect tampering with stored records.

## Note

This system detects modifications compared to a known original record. It does not independently verify whether the original document was truthful when it was issued.

## Author

Garv Ahuja
