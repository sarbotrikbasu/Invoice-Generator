import streamlit as st
import pandas as pd
import datetime
import requests
import base64
import os
import sys

# Add local path for direct PDF engine fallback if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from invoice_generator.models import InvoiceData, BillFrom, BillTo, BankDetails, InvoiceItem
from invoice_generator.pdf_engine import generate_invoice_pdf

st.set_page_config(
    page_title="Invoice PDF Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #334155 0%, #1E293B 100%);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.15);
        color: white;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #0F172A;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📄 Invoice Generator Workflow")
st.caption("Generate professional invoices matching exact corporate specifications with FastAPI backend support.")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings & Backend")
    api_url = st.text_input(
        "FastAPI Backend URL",
        value="http://localhost:8000/api/generate-invoice",
        help="URL of deployed FastAPI backend on Vercel or local uvicorn server."
    )
    use_api = st.checkbox("Use FastAPI Backend Endpoint", value=True, help="If unchecked, frontend will use built-in local PDF engine.")
    
    st.markdown("---")
    st.subheader("📌 Quick Defaults")
    if st.button("Reset to AWS June Sample Data"):
        st.session_state.reset_trigger = True
        st.rerun()

# Pre-populate default sample state matching AWS June invoice
if "items" not in st.session_state or getattr(st.session_state, "reset_trigger", False):
    st.session_state.reset_trigger = False
    st.session_state.items = [
        {"item_no": "01", "description": "AWS Charges on Actuals for June", "qty": 1.0, "rate": 32971.00},
        {"item_no": "02", "description": "Additional management charges for AWS (7%)", "qty": 1.0, "rate": 2300.00}
    ]

# Layout Columns
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.markdown("### 1. Document Configuration")
    with st.container():
        doc_header_type = st.radio(
            "Document Header Title",
            ["PROFORMA INVOICE", "TAX INVOICE", "Custom"],
            horizontal=True
        )
        if doc_header_type == "Custom":
            doc_title = st.text_input("Custom Header Title", value="INVOICE")
        else:
            doc_title = doc_header_type

    st.markdown("### 2. BILL FROM (Sender Details)")
    col_from1, col_from2 = st.columns(2)
    with col_from1:
        from_name = st.text_input("Name & Code", value="Sarbotrik Basu(Code : 3012885)")
        from_contact = st.text_input("Email & Phone", value="unosoftwaresolutions@gmail.com · 9163578991")
    with col_from2:
        from_address = st.text_area("Address", value="E/11, Lake View Park, Kolkata-700108", height=100)

    st.markdown("### 3. BILL TO (Client Details)")
    col_to1, col_to2 = st.columns(2)
    with col_to1:
        client_name = st.text_input("Client Name", value="SHYAM SEL AND POWER LIMITED (CRM UNIT)")
        addr_line1 = st.text_input("Address Line 1", value="Village: Dhasal Paschim")
    with col_to2:
        addr_line2 = st.text_input("Address Line 2", value="Burdwan 713336")

    st.markdown("### 4. Dates & Payment Terms")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        issue_date = st.date_input("Issue Date", value=datetime.date(2026, 8, 12))
        due_date = st.date_input("Due Date", value=datetime.date(2026, 8, 26))
    with col_d2:
        payment_terms = st.text_input("Payment Terms", value="Payment due within 14 days.")

    st.markdown("### 5. Bank / Payment Details")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bank_name = st.text_input("Bank Name", value="Punjab National Bank")
        account_no = st.text_input("Account Number", value="1575000101087506")
    with col_b2:
        ifsc_code = st.text_input("IFSC Code", value="PUNB0157500")
        pan_no = st.text_input("PAN Number", value="ELLPB9722E")

    st.markdown("### 6. Line Items & Amounts")
    
    # Data editor for line items
    df_items = pd.DataFrame(st.session_state.items)
    edited_df = st.data_editor(
        df_items,
        num_rows="dynamic",
        column_config={
            "item_no": st.column_config.TextColumn("# Item No", width="small", required=True),
            "description": st.column_config.TextColumn("Description", width="large", required=True),
            "qty": st.column_config.NumberColumn("Qty", min_value=1.0, step=1.0, format="%.2f", required=True),
            "rate": st.column_config.NumberColumn("Rate (₹)", min_value=0.0, format="₹%.2f", required=True)
        },
        use_container_width=True,
        key="items_editor"
    )

    # Calculate subtotal
    subtotal = 0.0
    parsed_items = []
    if not edited_df.empty:
        for _, row in edited_df.iterrows():
            if pd.notna(row["item_no"]) and pd.notna(row["description"]):
                qty = float(row.get("qty", 1.0))
                rate = float(row.get("rate", 0.0))
                amt = qty * rate
                subtotal += amt
                parsed_items.append(InvoiceItem(
                    item_no=str(row["item_no"]),
                    description=str(row["description"]),
                    qty=qty,
                    rate=rate,
                    amount=amt
                ))

    st.markdown(f"""
        <div class="metric-card">
            <span style="font-size: 0.9rem; color: #64748B;">TOTAL CALCULATED DUE</span>
            <div style="font-size: 1.8rem; font-weight: 700; color: #0F172A;">₹{subtotal:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 Generate PDF Invoice", use_container_width=True)

# Generate PDF logic
pdf_bytes = None
if generate_btn:
    # Construct Pydantic model
    invoice_payload = InvoiceData(
        document_title=doc_title,
        bill_from=BillFrom(
            name_and_code=from_name,
            address=from_address,
            contact=from_contact
        ),
        bill_to=BillTo(
            client_name=client_name,
            address_line1=addr_line1,
            address_line2=addr_line2
        ),
        issue_date=issue_date.strftime("%Y-%m-%d"),
        due_date=due_date.strftime("%Y-%m-%d"),
        items=parsed_items,
        payment_terms=payment_terms,
        bank_details=BankDetails(
            bank_name=bank_name,
            account_number=account_no,
            ifsc_code=ifsc_code,
            pan=pan_no
        )
    )

    if use_api:
        try:
            with st.spinner("Connecting to FastAPI backend..."):
                resp = requests.post(
                    api_url,
                    json=invoice_payload.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                if resp.status_code == 200:
                    pdf_bytes = resp.content
                    st.success("PDF generated successfully via FastAPI backend!")
                else:
                    st.warning(f"Backend returned status {resp.status_code}. Using local fallback engine...")
                    pdf_bytes = generate_invoice_pdf(invoice_payload)
        except Exception as e:
            st.info(f"Could not reach FastAPI backend at `{api_url}` ({e}). Using local engine fallback.")
            pdf_bytes = generate_invoice_pdf(invoice_payload)
    else:
        with st.spinner("Generating PDF locally..."):
            pdf_bytes = generate_invoice_pdf(invoice_payload)

    if pdf_bytes:
        st.session_state.generated_pdf = pdf_bytes
        st.session_state.generated_filename = f"{doc_title.replace(' ', '_')}_{issue_date.strftime('%Y-%m-%d')}.pdf"

with col_right:
    st.markdown("### 📄 PDF Preview & Download")
    
    if "generated_pdf" in st.session_state:
        pdf_data = st.session_state.generated_pdf
        filename = st.session_state.generated_filename
        
        st.download_button(
            label="⬇️ Download Invoice PDF",
            data=pdf_data,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )
        
        # Embedded PDF preview via iframe
        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="750" type="application/pdf" style="border: 1px solid #E2E8F0; border-radius: 8px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("👈 Enter your invoice parameters on the left and click **Generate PDF Invoice** to view and download.")
