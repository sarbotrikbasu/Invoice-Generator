# 📄 Invoice Generator Workflow (FastAPI + Streamlit + ReportLab)

An automated corporate invoice generator workflow built with **FastAPI** (Backend) and **Streamlit** (Frontend). It produces clean PDF invoices matching exact corporate layout standards (such as the standard *AWS Charges for June* invoice format for **SHYAM SEL AND POWER LIMITED**).

---

## 🌟 Features

- **Exact PDF Template Matching**: Pristine layout with custom section dividers, right-aligned monetary tables, Indian Rupee (`₹`) symbol support, subtotal/total calculation, bank details, and footer page numbering (`Page 1 of 1`).
- **Configurable Header Titles**: Toggle between **PROFORMA INVOICE**, **TAX INVOICE**, or enter any custom document header title.
- **Dynamic Line Item Editor**: Add, modify, or remove line items dynamically on the Streamlit interface with automatic real-time total computation.
- **FastAPI REST Service**: Validated JSON request handling via Pydantic models with binary PDF stream response.
- **100% Serverless & Cloud Ready**: Uses pure-Python `ReportLab` engine compatible with **Vercel Serverless Functions** (no OS binary dependencies like Cairo/Pango).
- **Embedded Live PDF Preview & Download**: Instant inline PDF viewer and 1-click download button in Streamlit.

---

## 📁 Repository Structure

```text
.
├── api/
│   └── index.py            # Vercel serverless entrypoint for FastAPI backend
├── invoice_generator/
│   ├── __init__.py
│   ├── models.py           # Pydantic data schemas (BillFrom, BillTo, Items, BankDetails)
│   └── pdf_engine.py       # ReportLab canvas & Platypus PDF generator engine
├── app.py                  # Streamlit frontend application
├── main.py                 # FastAPI backend application entrypoint
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment routes & configuration
└── README.md               # Documentation & deployment guide
```

---

## 🚀 Local Development Setup

### 1. Install Dependencies

Ensure Python 3.9+ is installed, then run:

```bash
pip install -r requirements.txt
```

### 2. Start FastAPI Backend

Launch the FastAPI backend server on `http://localhost:8000`:

```bash
uvicorn main:app --reload --port 8000
```

You can view interactive API docs at `http://localhost:8000/docs`.

### 3. Start Streamlit Frontend

In a separate terminal window, launch the Streamlit frontend:

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🌐 Cloud Deployment Guide

### A. Step 1: Create GitHub Repository & Push Code

1. Initialize Git in project directory (if not already initialized):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Invoice Generator with FastAPI and Streamlit"
   ```
2. Create a new repository on GitHub (e.g. `invoice-generator-workflow`).
3. Link local git to GitHub and push:
   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/invoice-generator-workflow.git
   git branch -M main
   git push -u origin main
   ```

---

### B. Step 2: Deploy Backend to Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **"Add New Project"** -> **"Import"** and select your GitHub repository (`invoice-generator-workflow`).
3. Framework Preset: Choose **Other** (Vercel automatically detects `vercel.json` and `@vercel/python`).
4. Click **Deploy**.
5. Once deployed, Vercel will provide your live backend URL, for example:
   `https://invoice-generator-backend.vercel.app`
6. Test your live endpoint at `https://invoice-generator-backend.vercel.app/api/health`.

---

### C. Step 3: Deploy Frontend to Streamlit Community Cloud

1. Log into [Streamlit Community Cloud](https://share.streamlit.io).
2. Click **"New app"**.
3. Select your repository: `YOUR_GITHUB_USERNAME/invoice-generator-workflow`.
4. Main file path: `app.py`.
5. Click **Deploy!**
6. On your deployed Streamlit app, open the **Settings** sidebar and set the **FastAPI Backend URL** to your deployed Vercel endpoint:
   `https://invoice-generator-backend.vercel.app/api/generate-invoice`

> **Note**: Streamlit frontend also includes a built-in local PDF engine fallback, ensuring PDF generation continues to work seamlessly even if backend connectivity is offline!

---

## 📝 Usage Instructions

1. **Configure Document Header**: Select **PROFORMA INVOICE** or **TAX INVOICE** (or type a custom title).
2. **Bill From / Bill To**: Adjust sender or client details (pre-filled with default client *SHYAM SEL AND POWER LIMITED (CRM UNIT)*).
3. **Dates & Bank Details**: Set Issue Date, Due Date, Payment Terms, and Bank details.
4. **Line Items**: Add or edit rows in the interactive table (`Item No`, `Description`, `Qty`, `Rate`). Amounts and Total Due calculate automatically.
5. **Generate PDF**: Click **Generate PDF Invoice**. The live PDF will appear in the preview panel on the right with a **Download Invoice PDF** button.
