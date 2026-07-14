#!/usr/bin/env python3
"""Generate a Jekyll/al-folio BibTeX entry from a DOI or PubMed PMID.

Examples:
  python scripts/pub_to_bib.py 10.1038/s41596-025-01158-4
  python scripts/pub_to_bib.py 40912345 --selected --cofirst 1,2 --corresponding 3,4
  python scripts/pub_to_bib.py 10.1038/s41596-025-01158-4 --append
  python scripts/pub_to_bib.py 10.1038/s41596-025-01158-4 --append _bibliography/papers.bib
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BIB_FILE = ROOT / "_bibliography" / "works_at_CNCB.bib"
DEFAULT_APPEND_TARGET = "__default_bib_file__"
USER_AGENT = "junchaoshi.github.io bibliography helper (mailto:shijc@cncb.ac.cn)"

MONTHS = {
    "jan": "1",
    "january": "1",
    "feb": "2",
    "february": "2",
    "mar": "3",
    "march": "3",
    "apr": "4",
    "april": "4",
    "may": "5",
    "jun": "6",
    "june": "6",
    "jul": "7",
    "july": "7",
    "aug": "8",
    "august": "8",
    "sep": "9",
    "sept": "9",
    "september": "9",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


class FetchError(RuntimeError):
    pass


def request_text(url: str, accept: str = "application/json") -> str:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise FetchError(f"Failed to fetch {url}: {exc}") from exc


def request_json(url: str) -> dict:
    return json.loads(request_text(url, "application/json"))


def normalize_identifier(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    value = value.strip().strip(".")
    return value


def is_pmid(value: str) -> bool:
    return bool(re.fullmatch(r"\d+", value.strip()))


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def clean_title(value: str | None) -> str:
    value = clean_text(value)
    if value.endswith(".") and not value.endswith("..."):
        return value[:-1]
    return value


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return clean_text("".join(element.itertext()))


def first_text(parent: ET.Element | None, path: str) -> str:
    if parent is None:
        return ""
    return element_text(parent.find(path))


def month_number(value: str | int | None) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    if not value:
        return ""
    if value.isdigit():
        return str(int(value))
    return MONTHS.get(value.lower()[:3], MONTHS.get(value.lower(), value))


def pubmed_search_by_doi(doi: str) -> str:
    term = urllib.parse.quote(f"{doi}[AID]")
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&retmode=json&term={term}"
    )
    data = request_json(url)
    ids = data.get("esearchresult", {}).get("idlist", [])
    return ids[0] if ids else ""


def fetch_pubmed_xml(pmid: str) -> ET.Element:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={urllib.parse.quote(pmid)}&retmode=xml"
    )
    return ET.fromstring(request_text(url, "application/xml"))


def parse_pubmed(pmid: str) -> dict[str, str]:
    root = fetch_pubmed_xml(pmid)
    article = root.find(".//PubmedArticle")
    if article is None:
        raise FetchError(f"PubMed PMID {pmid} was not found.")

    medline = article.find("MedlineCitation")
    pubmed_data = article.find("PubmedData")
    article_node = medline.find("Article") if medline is not None else None
    journal_node = article_node.find("Journal") if article_node is not None else None
    issue_node = journal_node.find("JournalIssue") if journal_node is not None else None
    pub_date = issue_node.find("PubDate") if issue_node is not None else None

    year = first_text(pub_date, "Year")
    medline_date = first_text(pub_date, "MedlineDate")
    if not year and medline_date:
        match = re.search(r"\d{4}", medline_date)
        year = match.group(0) if match else ""

    doi = ""
    if pubmed_data is not None:
        for article_id in pubmed_data.findall(".//ArticleId"):
            if article_id.attrib.get("IdType", "").lower() == "doi":
                doi = element_text(article_id)
                break

    authors = []
    if article_node is not None:
        for author in article_node.findall("AuthorList/Author"):
            collective = first_text(author, "CollectiveName")
            if collective:
                authors.append(collective)
                continue
            last_name = first_text(author, "LastName")
            fore_name = first_text(author, "ForeName") or first_text(author, "Initials")
            if last_name and fore_name:
                authors.append(f"{last_name}, {fore_name}")
            elif last_name:
                authors.append(last_name)

    abstract_parts = []
    if article_node is not None:
        for abstract_text in article_node.findall("Abstract/AbstractText"):
            label = abstract_text.attrib.get("Label")
            text = element_text(abstract_text)
            if label and text:
                abstract_parts.append(f"{label}: {text}")
            elif text:
                abstract_parts.append(text)

    url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return {
        "source": "pubmed",
        "entry_type": "article",
        "title": clean_title(first_text(article_node, "ArticleTitle")),
        "author": " and ".join(authors),
        "journal": first_text(journal_node, "Title"),
        "abbr": first_text(journal_node, "ISOAbbreviation"),
        "volume": first_text(issue_node, "Volume"),
        "number": first_text(issue_node, "Issue"),
        "pages": first_text(article_node, "Pagination/MedlinePgn"),
        "year": year,
        "Month": month_number(first_text(pub_date, "Month")),
        "Abstract": " ".join(abstract_parts),
        "doi": doi,
        "pmid": pmid,
        "url": url,
        "html": url,
    }


def crossref_date(message: dict) -> tuple[str, str]:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = message.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            values = parts[0]
            year = str(values[0]) if len(values) >= 1 else ""
            month = month_number(values[1]) if len(values) >= 2 else ""
            return year, month
    return "", ""


def parse_crossref(doi: str) -> dict[str, str]:
    encoded = urllib.parse.quote(doi, safe="")
    data = request_json(f"https://api.crossref.org/works/{encoded}")
    message = data.get("message", {})
    if not message:
        raise FetchError(f"Crossref DOI {doi} was not found.")

    authors = []
    for author in message.get("author", []):
        family = clean_text(author.get("family"))
        given = clean_text(author.get("given"))
        if family and given:
            authors.append(f"{family}, {given}")
        elif family:
            authors.append(family)
        elif given:
            authors.append(given)

    year, month = crossref_date(message)
    doi_value = clean_text(message.get("DOI")) or doi
    url = clean_text(message.get("URL")) or f"https://doi.org/{doi_value}"
    return {
        "source": "crossref",
        "entry_type": "article",
        "title": clean_title(next(iter(message.get("title", [])), "")),
        "author": " and ".join(authors),
        "journal": clean_text(next(iter(message.get("container-title", [])), "")),
        "volume": clean_text(message.get("volume")),
        "number": clean_text(message.get("issue")),
        "pages": clean_text(message.get("page") or message.get("article-number")),
        "year": year,
        "Month": month,
        "publisher": clean_text(message.get("publisher")),
        "Abstract": clean_text(message.get("abstract")),
        "doi": doi_value,
        "url": url,
        "html": url,
    }


def fetch_metadata(identifier: str) -> dict[str, str]:
    identifier = normalize_identifier(identifier)
    if is_pmid(identifier):
        return parse_pubmed(identifier)

    try:
        pmid = pubmed_search_by_doi(identifier)
    except FetchError:
        pmid = ""
    if pmid:
        return parse_pubmed(pmid)
    return parse_crossref(identifier)


def ascii_slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)
    return value.strip().lower()


def make_key(metadata: dict[str, str], existing_keys: set[str], requested_key: str = "") -> str:
    if requested_key:
        base = requested_key
    else:
        first_author = metadata.get("author", "").split(" and ")[0].split(",", 1)[0]
        first_author = ascii_slug(first_author).replace(" ", "")
        year = metadata.get("year", "unknown")
        title_words = [
            word
            for word in ascii_slug(metadata.get("title", "")).split()
            if word not in STOPWORDS
        ]
        title_word = title_words[0] if title_words else "article"
        base = f"{first_author}{year}{title_word}"

    key = base
    suffix = "b"
    while key in existing_keys:
        key = f"{base}{suffix}"
        suffix = chr(ord(suffix) + 1)
    return key


def bib_escape(value: str, text_field: bool = True) -> str:
    value = clean_text(value)
    value = value.replace("{", "\\{").replace("}", "\\}")
    if text_field:
        value = value.replace("&", r"\&")
        value = value.replace("%", r"\%")
    return value


def bib_field(name: str, value: str, quoted: bool = False, text_field: bool = True) -> str:
    value = bib_escape(value, text_field=text_field)
    if quoted:
        return f'  {name}="{value}",'
    return f"  {name}={{{value}}},"


def render_bibtex(metadata: dict[str, str], args: argparse.Namespace, existing_keys: set[str]) -> str:
    metadata = {key: value for key, value in metadata.items() if value}
    if args.abbr:
        metadata["abbr"] = args.abbr
    if args.pdf:
        metadata["pdf"] = args.pdf
    if args.cofirst:
        metadata["cofirst"] = args.cofirst
    if args.corresponding:
        metadata["corresponding"] = args.corresponding
    if args.selected:
        metadata["selected"] = "true"
    metadata["bibtex_show"] = "true"

    entry_key = make_key(metadata, existing_keys, args.key)
    lines = [f"@{metadata.get('entry_type', 'article')}{{{entry_key},"]
    field_order = [
        "title",
        "author",
        "journal",
        "abbr",
        "volume",
        "number",
        "pages",
        "year",
        "Month",
        "publisher",
        "Abstract",
        "doi",
        "pmid",
        "url",
        "html",
        "pdf",
        "cofirst",
        "corresponding",
        "selected",
        "bibtex_show",
    ]
    raw_fields = {"doi", "pmid", "url", "html", "pdf", "cofirst", "corresponding", "selected", "bibtex_show"}
    quoted_fields = {"abbr", "Month"}

    for field in field_order:
        value = metadata.get(field)
        if not value:
            continue
        lines.append(
            bib_field(
                field,
                value,
                quoted=field in quoted_fields,
                text_field=field not in raw_fields,
            )
        )

    if len(lines) > 1:
        lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def existing_bib_data(path: Path) -> tuple[set[str], set[str], set[str]]:
    if not path.exists():
        return set(), set(), set()
    text = path.read_text(encoding="utf-8", errors="replace")
    keys = set(re.findall(r"@\w+\{([^,\s]+)", text))
    dois = {doi.lower() for doi in re.findall(r"doi\s*=\s*[\{\"]([^}\"]+)", text, flags=re.I)}
    pmids = set(re.findall(r"pmid\s*=\s*[\{\"]([^}\"]+)", text, flags=re.I))
    return keys, dois, pmids


def duplicate_message(metadata: dict[str, str], dois: set[str], pmids: set[str]) -> str:
    doi = metadata.get("doi", "").lower()
    pmid = metadata.get("pmid", "")
    if doi and doi in dois:
        return f"DOI already exists in bibliography: {metadata['doi']}"
    if pmid and pmid in pmids:
        return f"PMID already exists in bibliography: {pmid}"
    return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a works_at_CNCB.bib-style BibTeX entry from DOI or PMID."
    )
    parser.add_argument("identifier", help="DOI, DOI URL, or PubMed PMID")
    parser.add_argument(
        "--bib-file",
        default=str(DEFAULT_BIB_FILE),
        help="Default bibliography file used for duplicate/key checks and --append.",
    )
    parser.add_argument(
        "--append",
        nargs="?",
        const=DEFAULT_APPEND_TARGET,
        default="",
        metavar="BIB_FILE",
        help="Append the generated entry. Optionally pass the target .bib file.",
    )
    parser.add_argument("--allow-duplicate", action="store_true", help="Allow appending duplicate DOI/PMID entries.")
    parser.add_argument("--key", default="", help="Override the generated BibTeX key.")
    parser.add_argument("--abbr", default="", help="Override the journal abbreviation shown on the site.")
    parser.add_argument("--cofirst", default="", help="Set custom cofirst field, e.g. 1,2.")
    parser.add_argument("--corresponding", default="", help="Set custom corresponding field, e.g. 3,4,5.")
    parser.add_argument("--pdf", default="", help="Set custom local PDF path, e.g. /2026/example.pdf.")
    parser.add_argument("--selected", action="store_true", help="Add selected={true}.")
    return parser.parse_args()


def resolve_path(path: str) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = ROOT / resolved
    return resolved


def main() -> int:
    args = parse_args()
    append_requested = bool(args.append)
    bib_file = resolve_path(args.bib_file)
    append_file = bib_file
    if append_requested and args.append != DEFAULT_APPEND_TARGET:
        append_file = resolve_path(args.append)
        bib_file = append_file

    existing_keys, existing_dois, existing_pmids = existing_bib_data(bib_file)
    metadata = fetch_metadata(args.identifier)
    duplicate = duplicate_message(metadata, existing_dois, existing_pmids)
    if duplicate and append_requested and not args.allow_duplicate:
        print(f"Refusing to append duplicate entry. {duplicate}", file=sys.stderr)
        return 2

    entry = render_bibtex(metadata, args, existing_keys)
    if append_requested:
        append_file.parent.mkdir(parents=True, exist_ok=True)
        with append_file.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\n\n")
            handle.write(entry)
            handle.write("\n")
        print(f"Appended entry to {append_file}")
    else:
        print(entry)
        if duplicate:
            print(f"\n# Note: {duplicate}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FetchError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
