from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.schemas import ExtractedInvoice, ProcessedInvoiceResponse
from app.services.openai_invoice_extractor import OpenAIInvoiceExtractor

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
REQUIRED_FIELDS = ("vendor_name", "invoice_number", "invoice_date", "total")


class InvoiceService:
    def __init__(self, extractor: OpenAIInvoiceExtractor | None = None) -> None:
        self.extractor = extractor or OpenAIInvoiceExtractor()

    async def process_invoice(self, upload: UploadFile) -> ProcessedInvoiceResponse:
        suffix = Path(upload.filename or "invoice").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file type. Use PDF, PNG, JPG, JPEG, or WEBP.")

        file_path = await self._save_upload(upload, suffix)
        try:
            extracted = self.extractor.extract(file_path)
            issues = self._validate(extracted)
            requires_review = bool(issues) or extracted.confidence < 0.8
            if extracted.confidence < 0.8:
                issues.append("Model confidence below review threshold (0.80).")

            return ProcessedInvoiceResponse(
                filename=upload.filename or file_path.name,
                requires_human_review=requires_review,
                validation_issues=issues,
                **extracted.model_dump(),
            )
        finally:
            file_path.unlink(missing_ok=True)

    async def _save_upload(self, upload: UploadFile, suffix: str) -> Path:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)
            return Path(temp_file.name)

    def _validate(self, invoice: ExtractedInvoice) -> list[str]:
        issues: list[str] = []

        for field_name in REQUIRED_FIELDS:
            if getattr(invoice, field_name) in (None, ""):
                issues.append(f"Missing required field: {field_name}.")

        if (
            invoice.subtotal is not None
            and invoice.tax is not None
            and invoice.total is not None
        ):
            expected_total = round(invoice.subtotal + invoice.tax, 2)
            actual_total = round(invoice.total, 2)
            if expected_total != actual_total:
                issues.append(
                    f"Total mismatch: expected {expected_total} from subtotal and tax, got {actual_total}."
                )

        if invoice.invoice_date and invoice.due_date and invoice.due_date < invoice.invoice_date:
            issues.append("Due date is earlier than invoice date.")

        if invoice.total is not None and invoice.total < 0:
            issues.append("Invoice total cannot be negative.")

        return issues
