from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from pydantic import BaseModel
import PyPDF2
import re

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class KeyValues(BaseModel):
    order_number: str
    order_date: str
    invoice_no: str
    invoice_date: str
    product_category: str
    invoice_due_date: str
    currency: str
    invoice_amount: str
    delivery_challan_no: str
    delivery_date: str
    seller_name: str
    buyer_name: str

def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_info_from_text(pdf_text):
    patterns = {
    "Order Number": r"Order\s*Number[:\s]*([\w-]+)",
    "Order Date": r"Order\s*Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})",
    "Invoice No.": r"Invoice\s*No\.[:\s]*([\w-]+)",
    "Invoice Date": r"Invoice\s*Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})",
    "Product category": r"Product\s*Category[:\s]*([^\n\r]+)",
    "Invoice Due Date": r"Invoice\s*Due\s*Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})",
    "Currency": r"(?i)(?:Rs\.|₹|INR|USD|\$)",
    "Invoice Amount": r"Invoice\s*Amount[:\s]*₹?([\d.,]+)",
    "Delivery Challan No.": r"Delivery\s*Challan\s*No\.[:\s]*([\w-]+)",
    "Delivery Date": r"Delivery\s*Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})",
    "Seller Name": r"Seller\s*Name[:\s]*([^\n\r]+)",
    "Buyer Name": r"Buyer\s*Name[:\s]*([^\n\r]+)"
}
    key_value_pairs = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, pdf_text)
        if match:
            if key == "Currency":
                if re.search(r"(?i)(Rs\.|₹|INR)", match.group(0)):
                    key_value_pairs[key] = "INR"
                elif re.search(r"(?i)(USD|\$)", match.group(0)):
                    key_value_pairs[key] = "USD"
            else:
                key_value_pairs[key.lower().replace(" ", "_")] = match.group(1)
    return key_value_pairs

@app.post("/extract-pdf-info/")
async def extract_pdf_info(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with open("./data/uploaded_pdf.pdf", "wb") as f:
            f.write(contents)
        
        pdf_text = extract_text("./data/uploaded_pdf.pdf")
        key_value_pairs = extract_info_from_text(pdf_text)

        return JSONResponse(content={"key_values": key_value_pairs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
