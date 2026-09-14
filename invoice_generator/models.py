from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceItem(BaseModel):
    item_no: str = Field(..., example="01")
    description: str = Field(..., example="AWS Charges on Actuals for June")
    qty: float = Field(1.0, example=1)
    rate: float = Field(..., example=32971.00)
    amount: Optional[float] = Field(None, example=32971.00)

    def calculate_amount(self) -> float:
        if self.amount is None or self.amount == 0:
            return round(self.qty * self.rate, 2)
        return round(self.amount, 2)

class BillFrom(BaseModel):
    name_and_code: str = Field("Sarbotrik Basu(Code : 3012885)", description="Sender Name & Code")
    address: str = Field("E/11, Lake View Park, Kolkata-700108", description="Sender Address")
    contact: str = Field("unosoftwaresolutions@gmail.com · 9163578991", description="Sender Email & Phone")

class BillTo(BaseModel):
    client_name: str = Field("SHYAM SEL AND POWER LIMITED (CRM UNIT)", description="Client Name")
    address_line1: str = Field("Village: Dhasal Paschim", description="Address Line 1")
    address_line2: str = Field("Burdwan 713336", description="Address Line 2")

class BankDetails(BaseModel):
    bank_name: str = Field("Punjab National Bank", description="Bank Name")
    account_number: str = Field("1575000101087506", description="Account Number")
    ifsc_code: str = Field("PUNB0157500", description="IFSC Code")
    pan: str = Field("ELLPB9722E", description="PAN Number")

class InvoiceData(BaseModel):
    document_title: str = Field("Proforma Invoice", description="TAX INVOICE or PROFORMA INVOICE")
    bill_from: BillFrom = Field(default_factory=BillFrom)
    bill_to: BillTo = Field(default_factory=BillTo)
    issue_date: str = Field("2026-08-12", description="Issue Date (YYYY-MM-DD)")
    due_date: str = Field("2026-08-26", description="Due Date (YYYY-MM-DD)")
    items: List[InvoiceItem] = Field(default_factory=list)
    payment_terms: str = Field("Payment due within 14 days.", description="Payment terms text")
    bank_details: BankDetails = Field(default_factory=BankDetails)

    @property
    def subtotal(self) -> float:
        return sum(item.calculate_amount() for item in self.items)

    @property
    def total_due(self) -> float:
        return self.subtotal
