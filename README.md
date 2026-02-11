# arXiv Publications PDF Generator

Fetches an author's publications from **arXiv** using multiple name variations,  
sorts them by year, and creates a clean **numbered PDF bibliography**.

![Example PDF](example_pdf.png)

---

## Installation

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
