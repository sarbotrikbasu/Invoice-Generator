import os
import io
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from invoice_generator.models import InvoiceData

# -----------------------------------------------------------------------------
# Font Loading Strategy
# Load bundled TTF font from repository so Rupee symbol (₹) works 100% reliably
# on Windows, Mac, Linux, Vercel Serverless, and Streamlit Cloud.
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "CustomFont.ttf")

# Register bundled TTF font
SANS_FONT = "Helvetica"
SERIF_FONT = "Times-Roman"
MONO_FONT = "Courier"
HAS_UNICODE_FONT = False

if os.path.exists(FONT_PATH):
    try:
        pdfmetrics.registerFont(TTFont("InvoiceUnicodeFont", FONT_PATH))
        SANS_FONT = "InvoiceUnicodeFont"
        MONO_FONT = "InvoiceUnicodeFont"
        HAS_UNICODE_FONT = True
    except Exception:
        pass
else:
    # Attempt system font fallbacks
    system_candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]
    for sys_path in system_candidates:
        if os.path.exists(sys_path):
            try:
                pdfmetrics.registerFont(TTFont("InvoiceUnicodeFont", sys_path))
                SANS_FONT = "InvoiceUnicodeFont"
                MONO_FONT = "InvoiceUnicodeFont"
                HAS_UNICODE_FONT = True
                break
            except Exception:
                continue


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count
    and clean document footer matching the reference design.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont(SANS_FONT, 8.5)
        self.setFillColor(colors.HexColor("#777777"))
        
        # Document title on left, Page X of Y on right
        doc_title = getattr(self, "_doc_title", "Proforma Invoice")
        footer_y = 40
        self.drawString(54, footer_y, doc_title)
        self.drawRightString(letter[0] - 54, footer_y, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def format_currency(amount: float) -> str:
    """Format float into standard invoice currency string (e.g. ₹32971.00)."""
    formatted_val = f"{amount:.2f}"
    return f"₹{formatted_val}" if HAS_UNICODE_FONT else f"Rs. {formatted_val}"


def generate_invoice_pdf(invoice_data: InvoiceData) -> bytes:
    """
    Generates a PDF byte stream matching the exact aesthetic of the
    'AWS Charges for June' reference invoice.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=64
    )

    styles = getSampleStyleSheet()

    # Define bespoke color palette matching reference PDF
    PRIMARY_TEXT = colors.HexColor("#111111")
    MUTED_GRAY = colors.HexColor("#666666")
    LINE_COLOR = colors.HexColor("#E2E2E2")
    DARK_LINE_COLOR = colors.HexColor("#999999")

    # Typography Styles matching original PDF
    style_label = ParagraphStyle(
        'SectionLabel',
        parent=styles['Normal'],
        fontName=SANS_FONT,
        fontSize=8.5,
        leading=10,
        textColor=MUTED_GRAY,
        spaceAfter=3
    )

    style_header_title = ParagraphStyle(
        'DocHeaderTitle',
        parent=styles['Normal'],
        fontName=SERIF_FONT,
        fontSize=28,
        leading=32,
        textColor=PRIMARY_TEXT,
        alignment=2 # Right aligned
    )

    style_sender_name = ParagraphStyle(
        'SenderName',
        parent=styles['Normal'],
        fontName=SANS_FONT,
        fontSize=15,
        leading=18,
        textColor=PRIMARY_TEXT,
        spaceAfter=2
    )

    style_body_text = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName=SANS_FONT,
        fontSize=9.5,
        leading=13,
        textColor=PRIMARY_TEXT
    )

    style_mono_text = ParagraphStyle(
        'MonoTextCustom',
        parent=styles['Normal'],
        fontName=MONO_FONT,
        fontSize=9.5,
        leading=13,
        textColor=PRIMARY_TEXT
    )

    style_table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName=SANS_FONT,
        fontSize=8.5,
        leading=10,
        textColor=MUTED_GRAY
    )

    style_table_header_right = ParagraphStyle(
        'TableHeaderRight',
        parent=style_table_header,
        alignment=2
    )

    style_table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=style_mono_text,
        alignment=2
    )

    style_total_due_value = ParagraphStyle(
        'TotalDueValue',
        parent=styles['Normal'],
        fontName=SERIF_FONT if SERIF_FONT != "Times-Roman" else SANS_FONT,
        fontSize=26,
        leading=28,
        textColor=PRIMARY_TEXT,
        alignment=2
    )

    story = []

    # -------------------------------------------------------------------------
    # 1. TOP HEADER SECTION (FROM details & Document Title)
    # -------------------------------------------------------------------------
    from_label_para = Paragraph("F R O M", style_label)
    sender_name_para = Paragraph(invoice_data.bill_from.name_and_code, style_sender_name)
    sender_addr_para = Paragraph(invoice_data.bill_from.address, style_body_text)
    sender_contact_para = Paragraph(invoice_data.bill_from.contact, style_body_text)

    title_para = Paragraph(invoice_data.document_title, style_header_title)

    top_table_data = [
        [from_label_para, title_para],
        [sender_name_para, ''],
        [sender_addr_para, ''],
        [sender_contact_para, '']
    ]

    top_table = Table(top_table_data, colWidths=[270, 234])
    top_table.setStyle(TableStyle([
        ('SPAN', (1, 0), (1, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (0, 0), 0.5, MUTED_GRAY),
    ]))

    story.append(top_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE_COLOR, spaceBefore=0, spaceAfter=20))

    # -------------------------------------------------------------------------
    # 2. BILL TO & DATES SECTION
    # -------------------------------------------------------------------------
    bill_to_label = Paragraph("B I L L &nbsp; T O", style_label)
    issue_date_label = Paragraph("I S S U E &nbsp; D A T E", style_label)
    due_date_label = Paragraph("D U E &nbsp; D A T E", style_label)

    client_name_para = Paragraph(f"<b>{invoice_data.bill_to.client_name}</b>", style_body_text)
    client_addr1_para = Paragraph(invoice_data.bill_to.address_line1, style_body_text)
    client_addr2_para = Paragraph(invoice_data.bill_to.address_line2, style_body_text)

    issue_date_val = Paragraph(invoice_data.issue_date, style_mono_text)
    due_date_val = Paragraph(invoice_data.due_date, style_mono_text)

    mid_table_data = [
        [bill_to_label, issue_date_label, due_date_label],
        [client_name_para, issue_date_val, due_date_val],
        [client_addr1_para, '', ''],
        [client_addr2_para, '', '']
    ]

    mid_table = Table(mid_table_data, colWidths=[240, 132, 132])
    mid_table.setStyle(TableStyle([
        ('SPAN', (1, 1), (1, 3)),
        ('SPAN', (2, 1), (2, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (0, 0), 0.5, MUTED_GRAY),
        ('LINEBELOW', (1, 0), (1, 0), 0.5, MUTED_GRAY),
        ('LINEBELOW', (2, 0), (2, 0), 0.5, MUTED_GRAY),
    ]))

    story.append(mid_table)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE_COLOR, spaceBefore=0, spaceAfter=20))

    # -------------------------------------------------------------------------
    # 3. LINE ITEMS TABLE
    # -------------------------------------------------------------------------
    table_headers = [
        Paragraph("#", style_table_header),
        Paragraph("D E S C R I P T I O N", style_table_header),
        Paragraph("Q T Y", style_table_header_right),
        Paragraph("R A T E", style_table_header_right),
        Paragraph("A M O U N T", style_table_header_right)
    ]

    items_data = [table_headers]

    for item in invoice_data.items:
        amt = item.calculate_amount()
        items_data.append([
            Paragraph(item.item_no, style_mono_text),
            Paragraph(item.description, style_mono_text),
            Paragraph(str(int(item.qty) if item.qty.is_integer() else item.qty), style_table_cell_right),
            Paragraph(format_currency(item.rate), style_table_cell_right),
            Paragraph(format_currency(amt), style_table_cell_right)
        ])

    items_table = Table(items_data, colWidths=[35, 259, 50, 80, 80])
    items_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, DARK_LINE_COLOR),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, DARK_LINE_COLOR),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, LINE_COLOR),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # 4. SUBTOTAL & TOTAL DUE SECTION
    # -------------------------------------------------------------------------
    subtotal_label = Paragraph("Subtotal", style_body_text)
    subtotal_value = Paragraph(f"<b>{format_currency(invoice_data.subtotal)}</b>", style_table_cell_right)

    total_label = Paragraph("T O T A L &nbsp; D U E", style_label)

    # Format total due with custom font for ₹ symbol and bold serif/sans for numbers
    total_val_str = f"{invoice_data.total_due:.2f}"
    if HAS_UNICODE_FONT:
        total_due_html = f"<b><font name='{SANS_FONT}'>₹</font>{total_val_str}</b>"
    else:
        total_due_html = f"<b>Rs. {total_val_str}</b>"

    total_value = Paragraph(total_due_html, style_total_due_value)

    totals_data = [
        ['', subtotal_label, subtotal_value],
        ['', '', ''],
        ['', total_label, total_value]
    ]

    totals_table = Table(totals_data, colWidths=[250, 100, 154])
    totals_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, 0), (2, 0), 0.5, DARK_LINE_COLOR),
        ('LINEABOVE', (1, 2), (1, 2), 0.5, DARK_LINE_COLOR),
    ]))

    story.append(totals_table)
    story.append(Spacer(1, 25))

    # -------------------------------------------------------------------------
    # 5. PAYMENT TERMS & BANK DETAILS (Two Column Layout)
    # -------------------------------------------------------------------------
    terms_hdr = Paragraph("P A Y M E N T &nbsp; T E R M S", style_label)
    terms_content = Paragraph(invoice_data.payment_terms, style_mono_text)

    bank_hdr = Paragraph("B A N K &nbsp; / &nbsp; P A Y M E N T &nbsp; D E T A I L S", style_label)

    bank_info = (
        f"Bank Name : {invoice_data.bank_details.bank_name}<br/>"
        f"Account Number: {invoice_data.bank_details.account_number}<br/>"
        f"IFSC Code : {invoice_data.bank_details.ifsc_code}<br/>"
        f"PAN : {invoice_data.bank_details.pan}"
    )
    bank_content = Paragraph(bank_info, style_mono_text)

    footer_block_data = [
        [terms_hdr, bank_hdr],
        [terms_content, bank_content]
    ]

    footer_table = Table(footer_block_data, colWidths=[240, 264])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, 0), (0, 0), 0.5, MUTED_GRAY),
        ('LINEABOVE', (1, 0), (1, 0), 0.5, MUTED_GRAY),
    ]))

    story.append(KeepTogether([footer_table]))

    # Build PDF with two-pass canvas for footer page numbering
    def canvas_maker(*args, **kwargs):
        c = NumberedCanvas(*args, **kwargs)
        c._doc_title = invoice_data.document_title
        return c

    doc.build(story, canvasmaker=canvas_maker)
    
    buffer.seek(0)
    return buffer.getvalue()
