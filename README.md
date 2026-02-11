# arXiv Publications PDF Generator

Fetches an author's publications from **arXiv** using multiple name variations,  
sorts them by year, and creates a clean **numbered PDF bibliography**.

<p align="center">
  <img src="example_pdf.png" alt="Example PDF" width="400">
</p>

## Installation

Choose one of the two options below. `uv` and `pip` are alternative installers.

### uv

```bash
uv venv
uv pip install -r requirements.txt
```

### pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python make_arxiv_pdf.py --author "Kimmo Kiiveri"
python make_arxiv_pdf.py --author "Kimmo Kiiveri" --from 2013 --to 2026 --out kiiveri_publications.pdf
```

## Automatic Updates (GitHub Actions)

A workflow **runs every Sunday at 00:00 UTC** to check for new publications, but is **disabled by default**.

**How it works:**

- The workflow fetches the latest publication from arXiv
- Compares it against the cached latest entry (`.arxiv_cache`)
- Only updates and commits the PDF if a new publication is detected
- No unnecessary commits — updates happen only when content changes

**To enable on your fork:**

1. Go to **Settings → Secrets and variables → Actions → Repository variables**
2. Create: `ENABLE_ARXIV_WORKFLOW = true` (enables the workflow)
3. Create: `AUTO_COMMIT_PDF = true` (enables auto-commit when changes are detected)

If you don't set these variables, the workflow won't run. This way, forks can opt-in to automation.
