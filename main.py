from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from invoice_generator.models import InvoiceData
from invoice_generator.pdf_engine import generate_invoice_pdf

app = FastAPI(
    title="Invoice PDF Generator API",
    description="FastAPI service for generating professional PDF invoices matching exact template specifications.",
    version="1.0.0"
)

# Enable CORS for Streamlit Cloud and local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Invoice PDF Generator API is operational"}

@app.post("/api/generate-invoice")
def generate_invoice(invoice: InvoiceData):
    try:
        pdf_bytes = generate_invoice_pdf(invoice)
        filename = f"{invoice.document_title.replace(' ', '_')}_{invoice.issue_date}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
