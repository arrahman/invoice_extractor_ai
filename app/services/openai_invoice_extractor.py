from __future__ import annotations

from pathlib import Path

from openai import OpenAI

from app.config import settings
from app.schemas import ExtractedInvoice


class OpenAIInvoiceExtractor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def extract(self, file_path: Path) -> ExtractedInvoice:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        with file_path.open("rb") as handle:
            uploaded = self.client.files.create(file=handle, purpose="user_data")

        response = self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured invoice data from PDFs and images. "
                        "Return only the requested schema fields. "
                        "If a field is missing, leave it null. "
                        "Choose the closest business spending category."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Extract the invoice fields, estimate confidence, and "
                                "infer a category from the vendor, line items, and notes."
                            ),
                        },
                        {
                            "type": "input_file",
                            "file_id": uploaded.id,
                        },
                    ],
                },
            ],
            text_format=ExtractedInvoice,
        )

        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("OpenAI returned no structured invoice data.")
        return parsed
