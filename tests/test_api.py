from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ProcessedInvoiceResponse


class StubInvoiceService:
    def __init__(self, response: ProcessedInvoiceResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error

    async def process_invoice(self, _file):
        if self.error:
            raise self.error
        return self.response


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_invoice_endpoint_returns_success(monkeypatch, sample_invoice):
    client = TestClient(app)
    response_model = ProcessedInvoiceResponse(
        filename="invoice.pdf",
        requires_human_review=False,
        validation_issues=[],
        **sample_invoice.model_dump(),
    )
    monkeypatch.setattr("app.main.invoice_service", StubInvoiceService(response=response_model))

    response = client.post(
        "/api/v1/invoices/process",
        files={"file": ("invoice.pdf", BytesIO(b"fake pdf bytes"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "invoice.pdf"
    assert body["vendor_name"] == "Acme Supplies"
    assert body["requires_human_review"] is False


def test_process_invoice_endpoint_returns_bad_request(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(
        "app.main.invoice_service",
        StubInvoiceService(error=ValueError("Unsupported file type.")),
    )

    response = client.post(
        "/api/v1/invoices/process",
        files={"file": ("invoice.txt", BytesIO(b"bad file"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type."
