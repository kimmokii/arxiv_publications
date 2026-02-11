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
