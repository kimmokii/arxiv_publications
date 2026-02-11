#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch arXiv publications for a given author using multiple name variations,
deduplicate, optionally filter by year range, sort newest → oldest, and
generate a numbered PDF bibliography with year section headers.

Usage examples:
  python make_arxiv_pdf.py --author "Kimmo Kiiveri" --out kiiveri_arxiv_bibliography.pdf
  python make_arxiv_pdf.py --author "Kimmo Kiiveri" --from 2013 --to 2025
"""

import argparse
import time
from datetime import datetime
from urllib.parse import urlencode
from html import escape

import feedparser
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm
from reportlab.lib import colors

ARXIV_API = "https://export.arxiv.org/api/query"
BATCH = 300          # arXiv allows up to 300 per request
MAX_TOTAL = 5000     # safety cap
DEFAULT_OUTPUT = "arxiv_bibliography.pdf"
AUTHOR_MATCH_SUBSTR_FALLBACK = None  # set dynamically from last name


def build_author_queries(author_fullname: str):
    """
    Build a robust set of arXiv queries for an author:
    - "First Last"
    - "Last, First"
    - "Last" and "Last_F" variants
    - 'all:' variants as a fallback
    """
    author_fullname = author_fullname.strip()
    parts = author_fullname.split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) >= 2 else (parts[0] if parts else "")

    queries = [
        f'au:"{author_fullname}"',
        f'au:"{last}, {first}"',
        f"au:{last}",
        f"all:\"{author_fullname}\"",
        f"all:{last}",
    ]
    # Add Last_F (e.g., Kiiveri_K)
    if first:
        first_initial = first[0]
        queries.append(f"au:{last}_{first_initial}")
    # Deduplicate while preserving order
    seen, out = set(), []
    for query in queries:
        if query not in seen:
            seen.add(query)
            out.append(query)
    return out, last


def fetch_entries_for_query(query):
    """Fetch all results for one arXiv search query, handling pagination."""
    entries = []
    start = 0
    while True:
        params = {
            "search_query": query,
            "start": start,
            "max_results": BATCH,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API}?{urlencode(params)}"
        feed = feedparser.parse(url)
        if feed.bozo:
            time.sleep(1.0)
            feed = feedparser.parse(url)
        batch = getattr(feed, "entries", [])
        if not batch:
            break
        entries.extend(batch)
        start += len(batch)
        if start >= MAX_TOTAL or len(batch) < BATCH:
            break
        time.sleep(0.2)  # polite delay
    return entries


def fetch_all_entries(queries):
    """Fetch and merge results from multiple queries, deduplicated by entry ID."""
    seen = set()
    merged = []
    for query in queries:
        batch = fetch_entries_for_query(query)
        for entry in batch:
            arxiv_id = getattr(entry, "id", None) or ""
            if arxiv_id and arxiv_id not in seen:
                seen.add(arxiv_id)
                merged.append(entry)
    return merged


def normalize_entry(entry):
    """Extract standard fields from an arXiv Atom entry."""
    title = entry.title.strip()

    authors_list = []
    if "authors" in entry:
        for a in entry.authors:
            name = a.get("name", "").strip()
            if name:
                authors_list.append(name)
    authors_str = ", ".join(authors_list)

    pub_dt, pub_year = None, None
    if hasattr(entry, "published"):
        try:
            pub_dt = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%SZ")
            pub_year = pub_dt.year
        except Exception:
            pub_year = None

    link = getattr(entry, "id", None)
    arxiv_id = link.split("/")[-1] if link else None

    abstract = getattr(entry, "summary", "").strip()

    return {
        "title": title,
        "authors": authors_str,
        "authors_list": authors_list,
        "year": pub_year,
        "published": pub_dt,
        "arxiv_id": arxiv_id,
        "link": link,
        "abstract": abstract,
        "raw": entry,
    }


def sort_entries(entries):
    """Sort newest → oldest by publication date; tie-breaker: title."""
    def keyfn(d):
        dt = d["published"] or datetime(1900, 1, 1)
        return (dt, d["title"].lower())
    return sorted(entries, key=keyfn, reverse=True)


def format_authors(authors, max_names=3):
    """Return 'A, B, C et al.' if more than max_names authors."""
    if not authors:
        return ""
    names = list(authors)
    if len(names) > max_names:
        return ", ".join(names[:max_names]) + " et al."
    return ", ".join(names)


def filter_by_author_substring(entries, author_substr: str):
    """Keep entries where any author contains the given substring (case-insensitive)."""
    if not author_substr:
        return entries
    needle = author_substr.lower()
    out = []
    for entry in entries:
        authors = [author.lower() for author in entry.get("authors_list", [])]
        if any(needle in author for author in authors):
            out.append(entry)
    return out


def filter_by_year_range(entries, year_from: int | None, year_to: int | None):
    """Filter entries by inclusive year range; entries with unknown year are dropped if a range is specified."""
    if year_from is None and year_to is None:
        return entries
    out = []
    for entry in entries:
        year = entry.get("year", None)
        if year is None:
            continue
        if (year_from is None or year >= year_from) and (year_to is None or year <= year_to):
            out.append(entry)
    return out


def make_pdf(entries, outfile: str, author_fullname: str):
    """Create a numbered bibliography PDF with year section headers (newest → oldest)."""
    doc = SimpleDocTemplate(
        outfile,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=18*mm,
        bottomMargin=18*mm,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = 1
    normal = styles["Normal"]
    normal.leading = 14

    # Year section style
    year_style = ParagraphStyle(
        "YearHeader",
        parent=styles["Heading2"],
        fontSize=14,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#333333"),
    )

    small = ParagraphStyle("small", parent=normal, fontSize=9, leading=12, textColor=colors.HexColor("#333333"))

    story = []
    # Dynamic title
    story.append(Paragraph(f"{escape(author_fullname)} — Publications", title_style))
    story.append(Spacer(1, 8))

    if not entries:
        story.append(Paragraph("No publications found for the given parameters.", normal))
        doc.build(story)
        return

    current_year = None
    counter = 1
    for entry in entries:
        year = entry["year"] if entry["year"] is not None else "—"
        if year != current_year:
            story.append(Spacer(1, 6))
            story.append(Paragraph(str(year), year_style))
            story.append(Spacer(1, 2))
            current_year = year

        shown_authors = format_authors(entry.get("authors_list", []), max_names=3)

        parts = []
        parts.append(f"<b>{counter}.</b> {escape(entry['title'])}. ")
        if shown_authors:
            parts.append(f"{escape(shown_authors)}. ")
        if entry["arxiv_id"]:
            parts.append(f"arXiv:{escape(entry['arxiv_id'])}")
        line = "".join(parts)

        story.append(Paragraph(line, normal))
        if entry["link"]:
            story.append(Paragraph(f'<a href="{escape(entry["link"])}">{escape(entry["link"])} </a>', small))
        story.append(Spacer(1, 6))
        counter += 1

    doc.build(story)


def main():
    parser = argparse.ArgumentParser(description="Generate a numbered arXiv bibliography PDF for an author.")
    parser.add_argument("--author", required=True, help='Author full name, e.g., "Kimmo Kiiveri"')
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output PDF filename (default: arxiv_bibliography.pdf)")
    parser.add_argument("--from", dest="year_from", type=int, default=None, help="Inclusive start year filter")
    parser.add_argument("--to", dest="year_to", type=int, default=None, help="Inclusive end year filter")
    args = parser.parse_args()

    queries, last_name = build_author_queries(args.author)
    global AUTHOR_MATCH_SUBSTR_FALLBACK
    AUTHOR_MATCH_SUBSTR_FALLBACK = last_name or None

    print("Queries:")
    for query in queries:
        print("  ", query)

    raw_entries = fetch_all_entries(queries)
    print(f"Combined results before normalization: {len(raw_entries)}")

    parsed = [normalize_entry(entry) for entry in raw_entries]

    filtered = filter_by_author_substring(parsed, AUTHOR_MATCH_SUBSTR_FALLBACK)
    print(f"After author-filter: {len(filtered)}")

    filtered = filter_by_year_range(filtered, args.year_from, args.year_to)
    if args.year_from or args.year_to:
        print(f"After year-range filter [{args.year_from}..{args.year_to}]: {len(filtered)}")

    sorted_entries = sort_entries(filtered)
    make_pdf(sorted_entries, args.out, args.author)
    print(f"Done: {args.out}")


if __name__ == "__main__":
    main()

