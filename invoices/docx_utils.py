from django.http import HttpResponse
from django.template.loader import get_template
import os
from django.conf import settings
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from io import BytesIO

def add_watermark(document, image_path):
    """Add a watermark to all pages of the document"""
    # This is a simplified watermark implementation
    # For a true watermark across all pages, a more complex approach with
    # document sections would be needed
    for section in document.sections:
        header = section.header
        paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        # Medium-sized logo for watermark
        picture = run.add_picture(image_path, width=Inches(5))
        # Make the image semi-transparent (this is approximate, not true watermark)
        for child in paragraph._element:
            if child.tag.endswith('drawing'):
                opacity = 0.3  # 30% opacity
                # This is a simplified approach and may not work in all Word versions
                try:
                    pic = child.xpath('.//pic:pic', namespaces={'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture'})[0]
                    blip = pic.xpath('.//a:blip', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})[0]
                    effect = OxmlElement('a:alphaModFix')
                    effect.set('amt', str(int(opacity * 100000)))
                    blip.append(effect)
                except:
                    # If we can't set opacity, just leave it as is
                    pass
        
        # Add demarcation line
        line_paragraph = header.add_paragraph()
        line_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        line_run = line_paragraph.add_run('_' * 100)
        line_run.font.color.rgb = RGBColor(200, 200, 200)  # Light gray color

def generate_invoice_docx(invoice):
    """Generate a Word document for an invoice"""
    document = Document()
    
    # Document properties
    document.core_properties.title = f"Invoice Number {invoice.invoice_number}"
    document.core_properties.author = "Skids LOGISTICS LTD"
    
    # Add logo
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/skids_logo.png')
        if not os.path.exists(logo_path):
            # Fallback to old path if new path doesn't exist
            logo_path = os.path.join(settings.STATIC_ROOT, 'img/logo.png')
        if os.path.exists(logo_path):
            # Medium-sized logo to match PDF
            document.add_picture(logo_path, width=Inches(3))
    except Exception as e:
        print(f"Error adding logo: {e}")
    
    # Add demarcation line
    document.add_paragraph().add_run('_' * 80)
    
    # Company information in a box
    company_info = document.add_table(rows=1, cols=1)
    company_info.style = 'Table Grid'
    cell = company_info.cell(0, 0)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    company_paragraph = cell.paragraphs[0]
    company_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    company_run = company_paragraph.add_run('Skids LOGISTICS LTD\n')
    company_run.bold = True
    company_run.font.size = Pt(14)
    company_paragraph.add_run('NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt\n')
    company_paragraph.add_run('Phone: 07035495280 | Email: info@skidslogistics.com\n')
    company_paragraph.add_run('Website: www.skidslogistics.com')
    
    # Add watermark if logo exists
    try:
        if os.path.exists(logo_path):
            add_watermark(document, logo_path)
    except Exception as e:
        print(f"Error adding watermark: {e}")
    
    # Invoice title
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(f"INVOICE NUMBER Invoice {invoice.invoice_number}")
    title_run.bold = True
    title_run.font.size = Pt(16)
    
    # Client information
    document.add_paragraph(f"Client: {invoice.client_name}")
    document.add_paragraph(f"Date: {invoice.date_created.strftime('%d-%m-%Y')}")
    document.add_paragraph(f"Due Date: {invoice.due_date.strftime('%d-%m-%Y')}")
    
    # Items table
    document.add_paragraph()
    items_table = document.add_table(rows=1, cols=5)
    items_table.style = 'Table Grid'
    
    # Header row
    header_cells = items_table.rows[0].cells
    header_cells[0].text = "Description"
    header_cells[1].text = "Quantity"
    header_cells[2].text = f"Unit Price ({invoice.currency})"
    header_cells[3].text = f"Total ({invoice.currency})"
    header_cells[4].text = "Lead Time"
    
    # Make header bold
    for cell in header_cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    # Add items
    for item in invoice.items.all():
        row_cells = items_table.add_row().cells
        row_cells[0].text = item.name
        # Extract numeric part from quantity and keep any unit text
        quantity_text = str(item.quantity)
        row_cells[1].text = quantity_text
        # Format numbers with comma delimiter
        price = '{:,.0f}'.format(item.price)
        total = '{:,.0f}'.format(item.total)
        row_cells[2].text = price
        row_cells[3].text = total
        row_cells[4].text = item.lead_time if item.lead_time else "1-7 DAYS"
    
    # Totals
    document.add_paragraph()
    totals_table = document.add_table(rows=3, cols=2)
    totals_table.autofit = False
    totals_table.columns[0].width = Inches(4)
    totals_table.columns[1].width = Inches(1.5)
    
    # Right-align the amount column
    for row in totals_table.rows:
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # Add totals
    subtotal_cells = totals_table.rows[0].cells
    subtotal_cells[0].text = "Subtotal:"
    subtotal_cells[1].text = f"{invoice.currency} {'{:,.0f}'.format(invoice.subtotal)}"
    
    vat_cells = totals_table.rows[1].cells
    vat_cells[0].text = "VAT (7.5%):"
    vat_cells[1].text = f"{invoice.currency} {'{:,.0f}'.format(invoice.vat_amount)}"
    
    total_cells = totals_table.rows[2].cells
    total_cells[0].text = "Total:"
    total_cells[1].text = f"{invoice.currency} {'{:,.0f}'.format(invoice.total)}"
    
    # Make the total row bold
    for cell in totals_table.rows[2].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    # Notes if present
    if invoice.notes:
        document.add_paragraph()
        notes_para = document.add_paragraph()
        notes_run = notes_para.add_run("Notes:")
        notes_run.bold = True
        document.add_paragraph(invoice.notes)
    
    # Save to memory
    docx_buffer = BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)
    
    # Create response
    response = HttpResponse(docx_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.docx"'
    
    return response

def generate_quotation_docx(quotation):
    """Generate a Word document for a quotation"""
    document = Document()
    
    # Document properties
    document.core_properties.title = f"Quotation Number {quotation.quotation_number}"
    document.core_properties.author = "Skids LOGISTICS LTD"
    
    # Add logo
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/skids_logo.png')
        if not os.path.exists(logo_path):
            # Fallback to old path if new path doesn't exist
            logo_path = os.path.join(settings.STATIC_ROOT, 'img/logo.png')
        if os.path.exists(logo_path):
            # Increased logo size by 5x (from 2 inches to 10 inches)
            document.add_picture(logo_path, width=Inches(10))
    except Exception as e:
        print(f"Error adding logo: {e}")
    
    # Add demarcation line
    document.add_paragraph().add_run('_' * 80)
    
    # Company information in a box
    company_info = document.add_table(rows=1, cols=1)
    company_info.style = 'Table Grid'
    cell = company_info.cell(0, 0)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    company_paragraph = cell.paragraphs[0]
    company_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    company_run = company_paragraph.add_run('Skids LOGISTICS LTD\n')
    company_run.bold = True
    company_run.font.size = Pt(14)
    company_paragraph.add_run('NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt\n')
    company_paragraph.add_run('Phone: 07035495280 | Email: info@skidslogistics.com\n')
    company_paragraph.add_run('Website: www.skidslogistics.com')
    
    # Add watermark if logo exists
    try:
        if os.path.exists(logo_path):
            add_watermark(document, logo_path)
    except Exception as e:
        print(f"Error adding watermark: {e}")
    
    # Quotation title
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(f"QUOTATION NUMBER Quotation {quotation.quotation_number}")
    title_run.bold = True
    title_run.font.size = Pt(16)
    
    # Client information
    document.add_paragraph(f"Client: {quotation.client_name}")
    document.add_paragraph(f"Date: {quotation.date_created.strftime('%d-%m-%Y')}")
    
    # Items table
    document.add_paragraph()
    items_table = document.add_table(rows=1, cols=5)
    items_table.style = 'Table Grid'
    
    # Header row
    header_cells = items_table.rows[0].cells
    header_cells[0].text = "Description"
    header_cells[1].text = "Quantity"
    header_cells[2].text = f"Unit Price ({quotation.currency})"
    header_cells[3].text = f"Total ({quotation.currency})"
    header_cells[4].text = "Lead Time"
    
    # Make header bold
    for cell in header_cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    # Add items
    for item in quotation.items.all():
        row_cells = items_table.add_row().cells
        row_cells[0].text = item.name
        # Extract numeric part from quantity and keep any unit text
        quantity_text = str(item.quantity)
        row_cells[1].text = quantity_text
        # Format numbers with comma delimiter
        price = '{:,.0f}'.format(item.price)
        total = '{:,.0f}'.format(item.total)
        row_cells[2].text = price
        row_cells[3].text = total
        row_cells[4].text = item.lead_time if item.lead_time else "1-7 DAYS"
    
    # Totals
    document.add_paragraph()
    totals_table = document.add_table(rows=3, cols=2)
    totals_table.autofit = False
    totals_table.columns[0].width = Inches(4)
    totals_table.columns[1].width = Inches(1.5)
    
    # Right-align the amount column
    for row in totals_table.rows:
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    # Add totals
    subtotal_cells = totals_table.rows[0].cells
    subtotal_cells[0].text = "Subtotal:"
    subtotal_cells[1].text = f"{quotation.currency} {'{:,.0f}'.format(quotation.subtotal)}"
    
    vat_cells = totals_table.rows[1].cells
    vat_cells[0].text = "VAT (7.5%):"
    vat_cells[1].text = f"{quotation.currency} {'{:,.0f}'.format(quotation.vat_amount)}"
    
    total_cells = totals_table.rows[2].cells
    total_cells[0].text = "Total:"
    total_cells[1].text = f"{quotation.currency} {'{:,.0f}'.format(quotation.total)}"
    
    # Make the total row bold
    for cell in totals_table.rows[2].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    # Notes if present
    if quotation.notes:
        document.add_paragraph()
        notes_para = document.add_paragraph()
        notes_run = notes_para.add_run("Notes:")
        notes_run.bold = True
        document.add_paragraph(quotation.notes)
    
    # Save to memory
    docx_buffer = BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)
    
    # Create response
    response = HttpResponse(docx_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="Quotation_{quotation.quotation_number}.docx"'
    
    return response