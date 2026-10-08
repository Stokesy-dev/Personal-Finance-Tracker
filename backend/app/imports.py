import csv
import io
from datetime import date
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, UploadFile


@dataclass
class CsvPreview:
    columns: list[str]
    rows: list[dict[str, str]]


@dataclass
class NormalizedTransaction:
    date: str
    description: str
    amount: str
    type: str


async def preview_csv(upload: UploadFile) -> CsvPreview:
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    data = await upload.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file must be smaller than 5 MB")
    try:
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        columns = reader.fieldnames or []
        if not columns:
            raise ValueError("missing header")
        rows = [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Could not parse this CSV file") from exc
    if not rows:
        raise HTTPException(status_code=400, detail="CSV file contains no transactions")
    return CsvPreview(columns=columns, rows=rows)


def validate_mapping(columns: list[str], mapping: dict[str, str]) -> dict[str, str]:
    required = {"date", "description"}
    amount_modes = [{"amount"}, {"debit", "credit"}]
    # Accept both CSV-column -> app-field and app-field -> CSV-column.
    # The latter keeps requests from already-open older frontend bundles working.
    if not required.issubset(mapping.values()) and required.issubset(mapping.keys()):
        mapping = {source: field for field, source in mapping.items() if source}
    mapped = set(mapping.values())
    if not required.issubset(mapped):
        raise HTTPException(status_code=400, detail="Mapping must include date and description")
    if not any(mode.issubset(mapped) for mode in amount_modes):
        raise HTTPException(status_code=400, detail="Mapping must include amount or both debit and credit")
    if any(source not in columns for source in mapping):
        raise HTTPException(status_code=400, detail="Mapping contains a column not present in the CSV")
    return mapping


def parse_amount(value: str) -> Decimal:
    cleaned = value.replace(",", "").replace("$", "").strip()
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise HTTPException(status_code=400, detail=f"Invalid transaction amount: {value}") from exc


def normalize_rows(rows: list[dict[str, str]], mapping: dict[str, str]) -> list[NormalizedTransaction]:
    """Convert mapped bank rows into a consistent signed-amount representation."""
    normalized: list[NormalizedTransaction] = []
    source_for = {target: source for source, target in mapping.items()}
    for row_number, row in enumerate(rows, start=2):
        try:
            transaction_date = date.fromisoformat(row[source_for["date"]]).isoformat()
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid date on row {row_number}; use YYYY-MM-DD") from exc
        description = row.get(source_for["description"], "").strip()
        if not description:
            raise HTTPException(status_code=400, detail=f"Missing description on row {row_number}")
        if "amount" in mapping.values():
            amount = parse_amount(row.get(source_for["amount"], ""))
        else:
            amount = parse_amount(row.get(source_for["credit"], "")) - parse_amount(row.get(source_for["debit"], ""))
        normalized.append(NormalizedTransaction(date=transaction_date, description=description, amount=f"{amount:.2f}", type="income" if amount >= 0 else "expense"))
    return normalized
