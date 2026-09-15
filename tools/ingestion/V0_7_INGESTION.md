# V0.7 — Real Problem & Attachment Ingestion

## Goal

Turn a CUMCM problem statement plus an attachment directory into a deterministic input envelope that an LLM can safely consume.

```text
题目文件/文本 + 附件目录
        ↓
 deterministic ingestion
        ↓
 file inventory + SHA256 + extraction status
        ↓
 problem text + attachment text
        ↓
 tabular structure profile
        ↓
 ingestion_manifest.json + DataProfile
        ↓
 Stage 00 / Stage 02 / LLM
```

## Supported in V0.7

- TXT / MD / Markdown / RST / LOG
- DOCX text extraction through OOXML
- PDF text extraction when optional `pypdf` is installed
- CSV / TSV raw text plus basic row/column/empty/duplicate checks
- JSON basic list-of-records profiling
- XLSX OOXML sheet/cell inventory
- attachment directory recursion
- SHA-256 provenance

Unsupported or unavailable extractors are **warnings**, not silent success.

## Semantic boundary

V0.7 does not decide what the mathematical meaning of a column, figure, formula or question is. It only reports extractable facts. Semantic interpretation belongs to Stage 00/02 and the model.

## Output

```text
<output>/
├── input/problem_text.txt
├── manifest/ingestion_manifest.json
└── data/data_profile.json
```

These files become upstream evidence for later artifacts and must not be replaced by model-generated guesses.

## Known limitation

PDFs that are scans/images may produce little or no text even when the file is readable. OCR/vision ingestion is a subsequent capability and must be represented explicitly when added.
