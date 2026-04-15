from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.schemas import ProcessedInvoiceResponse
from app.services.invoice_service import InvoiceService

app = FastAPI(title=settings.app_name)
invoice_service = InvoiceService()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.post("/api/v1/invoices/process", response_model=ProcessedInvoiceResponse)
async def process_invoice(file: UploadFile = File(...)) -> ProcessedInvoiceResponse:
    try:
        return await invoice_service.process_invoice(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invoice processing failed: {exc}") from exc
