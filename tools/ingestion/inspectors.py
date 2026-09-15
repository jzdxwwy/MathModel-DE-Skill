"""Deterministic file inspection primitives for V0.7.

The inspector never invents semantic meaning. It reports only facts that can
be derived from the file bytes/structure and marks optional extractors when
unavailable.
"""
from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for p in root.findall(".//w:p", ns):
        text = "".join(t.text or "" for t in p.findall(".//w:t", ns))
        if text.strip():
            paragraphs.append(text.strip())
    return "\n".join(paragraphs)


def _csv_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        sample = f.read(64 * 1024)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(f, dialect)
        rows = list(reader)
    header = rows[0] if rows else []
    data = rows[1:] if rows else []
    return {
        "rows": len(data),
        "columns": len(header),
        "columns_profile": [
            {"name": str(name), "dtype": "string"}
            for name in header
        ],
        "delimiter": getattr(dialect, "delimiter", ","),
        "empty_cells": sum(1 for row in data for cell in row if not str(cell).strip()),
        "duplicate_rows": len(data) - len({tuple(r) for r in data}),
    }


def _json_profile(path: Path) -> dict[str, Any]:
    value = json.loads(_text_file(path))
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict):
        rows = value.get("data") if isinstance(value.get("data"), list) else []
    else:
        rows = []
    if rows and all(isinstance(x, dict) for x in rows):
        names = sorted({k for row in rows for k in row})
        profile = [{"name": k, "dtype": "mixed"} for k in names]
    else:
        profile = []
    return {"rows": len(rows), "columns": len(profile), "columns_profile": profile}


def _xlsx_profile(path: Path) -> dict[str, Any]:
    # Lightweight OOXML inspection: enough for inventory and sheet discovery;
    # detailed statistical profiling is delegated to the data Stage/tool layer.
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        sheets = [n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter() if t.tag.endswith("}t")) for si in root]
        sheet_info = []
        for sheet in sheets:
            root = ET.fromstring(z.read(sheet))
            cells = root.findall(".//{*}c")
            rows = root.findall(".//{*}sheetData/{*}row")
            sheet_info.append({"sheet": sheet, "rows": len(rows), "cells": len(cells)})
        return {"sheets": sheet_info, "shared_strings": len(shared)}


def extract_text(path: Path) -> tuple[str, str | None]:
    ext = path.suffix.lower()
    if ext in {".txt", ".md", ".markdown", ".rst", ".log"}:
        return _text_file(path), None
    if ext == ".docx":
        try:
            return _docx_text(path), None
        except Exception as exc:
            return "", f"docx extraction failed: {exc}"
    if ext == ".pdf":
        try:
            from pypdf import PdfReader  # optional dependency
            reader = PdfReader(str(path))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages), None
        except ImportError:
            return "", "PDF text extraction requires optional dependency pypdf"
        except Exception as exc:
            return "", f"pdf extraction failed: {exc}"
    if ext in {".csv", ".tsv"}:
        return _text_file(path), None
    if ext == ".json":
        return _text_file(path), None
    return "", "no text extractor for this format"


def inspect_file(path_like: str) -> dict[str, Any]:
    path = Path(path_like).expanduser().resolve()
    item: dict[str, Any] = {
        "path": str(path),
        "name": path.name,
        "extension": path.suffix.lower(),
        "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "exists": path.exists(),
    }
    if not path.exists() or not path.is_file():
        item["status"] = "MISSING"
        item["error"] = "file does not exist or is not a regular file"
        return item
    item.update({"status": "READABLE", "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    text, extraction_error = extract_text(path)
    item["text"] = text
    item["text_chars"] = len(text)
    if extraction_error:
        item["extraction_warning"] = extraction_error
    try:
        ext = path.suffix.lower()
        if ext in {".csv", ".tsv"}:
            item["data_profile"] = _csv_profile(path)
        elif ext == ".json":
            item["data_profile"] = _json_profile(path)
        elif ext == ".xlsx":
            item["data_profile"] = _xlsx_profile(path)
    except Exception as exc:
        item["data_profile_error"] = str(exc)
    return item
