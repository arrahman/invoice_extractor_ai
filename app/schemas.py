from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class InvoiceCategory(str, Enum):
    office_supplies = "office_supplies"
    software = "software"
    utilities = "utilities"
    rent = "rent"
    travel = "travel"
    logistics = "logistics"
    professional_services = "professional_services"
    marketing = "marketing"
    hardware = "hardware"
    uncategorized = "uncategorized"


class LineItem(BaseModel):
    description: str = Field(default="")
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class ExtractedInvoice(BaseModel):
    document_type: str = "invoice"
    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    purchase_order: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    category: InvoiceCategory = InvoiceCategory.uncategorized
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    line_items: list[LineItem] = Field(default_factory=list)
    notes: str | None = None


class ProcessedInvoiceResponse(ExtractedInvoice):
    filename: str
    requires_human_review: bool
    validation_issues: list[str] = Field(default_factory=list)
