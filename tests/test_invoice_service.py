import asyncio
from datetime import date
from io import BytesIO

import pytest
from fastapi import UploadFile

from app.schemas import ExtractedInvoice, InvoiceCategory
from app.services.invoice_service import InvoiceService


class StubExtractor:
    def __init__(self, invoice: ExtractedInvoice) -> None:
        self.invoice = invoice

    def extract(self, _file_path):
        return self.invoice


def test_process_invoice_returns_structured_response(sample_invoice):
    service = InvoiceService(extractor=StubExtractor(sample_invoice))
    upload = UploadFile(filename="invoice.pdf", file=BytesIO(b"fake invoice bytes"))

    result = asyncio.run(service.process_invoice(upload))

    assert result.filename == "invoice.pdf"
    assert result.vendor_name == "Acme Supplies"
    assert result.category == InvoiceCategory.office_supplies
    assert result.requires_human_review is False
    assert result.validation_issues == []


def test_process_invoice_rejects_unsupported_extension(sample_invoice):
    service = InvoiceService(extractor=StubExtractor(sample_invoice))
    upload = UploadFile(filename="invoice.txt", file=BytesIO(b"not supported"))

    with pytest.raises(ValueError, match="Unsupported file type"):
        asyncio.run(service.process_invoice(upload))


def test_validate_flags_missing_fields_and_business_rule_issues():
    invoice = ExtractedInvoice(
        vendor_name="",
        invoice_number=None,
        invoice_date=date(2026, 4, 10),
        due_date=date(2026, 4, 1),
        subtotal=100.0,
        tax=5.0,
        total=120.0,
        confidence=0.95,
    )
    service = InvoiceService(extractor=StubExtractor(invoice))

    issues = service._validate(invoice)

    assert "Missing required field: vendor_name." in issues
    assert "Missing required field: invoice_number." in issues
    assert "Total mismatch: expected 105.0 from subtotal and tax, got 120.0." in issues
    assert "Due date is earlier than invoice date." in issues


def test_process_invoice_marks_low_confidence_for_review(sample_invoice):
    low_confidence_invoice = sample_invoice.model_copy(update={"confidence": 0.61})
    service = InvoiceService(extractor=StubExtractor(low_confidence_invoice))
    upload = UploadFile(filename="invoice.png", file=BytesIO(b"fake image bytes"))

    result = asyncio.run(service.process_invoice(upload))

    assert result.requires_human_review is True
    assert "Model confidence below review threshold (0.80)." in result.validation_issues
