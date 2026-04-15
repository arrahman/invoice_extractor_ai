from datetime import date

import pytest

from app.schemas import ExtractedInvoice, InvoiceCategory


@pytest.fixture
def sample_invoice() -> ExtractedInvoice:
    return ExtractedInvoice(
        vendor_name="Acme Supplies",
        invoice_number="INV-1042",
        invoice_date=date(2026, 4, 1),
        due_date=date(2026, 4, 30),
        currency="USD",
        subtotal=1200.0,
        tax=96.0,
        total=1296.0,
        category=InvoiceCategory.office_supplies,
        confidence=0.94,
        notes="Office chairs and printer paper",
    )
