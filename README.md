# arXiv Publications PDF Generator

Fetches an author's publications from **arXiv** using multiple name variations,  
sorts them by year, and creates a clean **numbered PDF bibliography**.

---

## Usage

```bash
python make_arxiv_pdf.py --author "Kimmo Kiiveri"
python make_arxiv_pdf.py --author "Kimmo Kiiveri" --from 2013 --to 2025 --out kiiveri_publications.pdf

