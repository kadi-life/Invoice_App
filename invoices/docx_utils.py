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
    # This function is now disabled to remove the watermark/logo from the header
    # as requested by the user
    pass

def generate_invoice_docx(invoice):
    """Generate a Word document for an invoice"""
    document = Document()
    
    # Document properties
    document.core_properties.title = f"INVOICE {invoice.invoice_number.upper() if invoice.invoice_number else invoice.id}"
    document.core_properties.author = "Skids LOGISTICS LTD"
    
    # Company information in a single line
    company_info = document.add_paragraph()
    company_run = company_info.add_run('Skids LOGISTICS LTD | ')
    company_run.bold = True
    company_info.add_run('NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt | ')
    company_info.add_run('Phone: 07035495280 | Email: info@skidslogistics.com | ')
    company_info.add_run('Website: www.skidslogistics.com')
    
    # Add logo after the company information
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/skids_logo.png')
        if not os.path.exists(logo_path):
            # Fallback to old path if new path doesn't exist
            logo_path = os.path.join(settings.STATIC_ROOT, 'img/logo.png')
        if os.path.exists(logo_path):
            # Center align the logo
            logo_paragraph = document.add_paragraph()
            logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_run = logo_paragraph.add_run()
            logo_run.add_picture(logo_path, width=Inches(3))
    except Exception as e:
        print(f"Error adding logo: {e}")
    
    # Add demarcation line
    document.add_paragraph().add_run('_' * 80)
    
    # Add watermark if logo exists
    try:
        if os.path.exists(logo_path):
            add_watermark(document, logo_path)
    except Exception as e:
        print(f"Error adding watermark: {e}")
    
    # Invoice title
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(f"INVOICE {invoice.invoice_number.upper() if invoice.invoice_number else invoice.id}")
    title_run.bold = True
    title_run.font.size = Pt(16)
    
    # Client information
    document.add_paragraph(f"Client: {invoice.client_name}")
    document.add_paragraph(f"Date: {invoice.date_created.strftime('%d-%m-%Y')}")
    document.add_paragraph(f"Due Date: {invoice.due_date.strftime('%d-%m-%Y')}")
    document.add_paragraph(f"Status: {invoice.status}")
    
    # Items table
    document.add_paragraph()
    items_table = document.add_table(rows=1, cols=5)
    items_table.style = 'Table Grid'
    
    # Header row
    header_cells = items_table.rows[0].cells
    header_cells[0].text = "DESCRIPTION"
    header_cells[1].text = "QUANTITY"
    header_cells[2].text = f"UNIT PRICE ({invoice.currency})"
    header_cells[3].text = f"TOTAL ({invoice.currency})"
    
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
    
    # Create a left-aligned paragraph for each total line to match PDF style
    subtotal_para = document.add_paragraph()
    subtotal_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    subtotal_para.add_run(f"Subtotal: {invoice.currency} {'{:,.0f}'.format(invoice.subtotal)}")
    
    vat_para = document.add_paragraph()
    vat_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    vat_para.add_run(f"VAT ({invoice.vat_percentage}%): {invoice.currency} {'{:,.0f}'.format(invoice.vat_amount)}")
    
    # Add a line before the total
    document.add_paragraph().add_run('_' * 30)
    
    # Make the total bold
    total_para = document.add_paragraph()
    total_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    total_run = total_para.add_run(f"Total: {invoice.currency} {'{:,.0f}'.format(invoice.total)}")
    total_run.bold = True
    
    # Notes if present
    if invoice.notes:
        document.add_paragraph()
        notes_para = document.add_paragraph()
        notes_run = notes_para.add_run("Notes:")
        notes_run.bold = True
        document.add_paragraph(invoice.notes)
    
    # Add images on a new page if any items have images
    has_images = False
    for item in invoice.items.all():
        if item.image:
            has_images = True
            break
    
    if has_images:
        # Add page break before images
        document.add_page_break()
        
        # Add images title
        images_title = document.add_paragraph()
        images_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        images_title_run = images_title.add_run("ITEM IMAGES")
        images_title_run.bold = True
        images_title_run.font.size = Pt(14)
        
        # Create a table for images (2 columns x 2 rows = 4 images per page)
        if invoice.items.filter(image__isnull=False).count() > 0:
            # Count items with images
            items_with_images = [item for item in invoice.items.all() if item.image]
            num_items = len(items_with_images)
            
            # Process 4 images per page
            images_per_page = 4
            current_item = 0
            
            while current_item < num_items:
                # For each page (except the first which already has a page break)
                if current_item > 0 and current_item % images_per_page == 0:
                    document.add_page_break()
                    # Add images title on new page
                    new_page_title = document.add_paragraph()
                    new_page_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    new_page_title_run = new_page_title.add_run("ITEM IMAGES (CONTINUED)")
                    new_page_title_run.bold = True
                    new_page_title_run.font.size = Pt(14)
                
                # Calculate how many images to process on this page (max 4)
                images_remaining = num_items - current_item
                images_on_this_page = min(images_per_page, images_remaining)
                
                # Calculate rows needed (2 columns, so divide by 2 and round up)
                rows_needed = (images_on_this_page + 1) // 2
                
                # Create table for this page's images
                img_table = document.add_table(rows=rows_needed, cols=2)
                img_table.style = 'Table Grid'
                
                # Add images to table
                for row in range(rows_needed):
                    for col in range(2):
                        if current_item < num_items:
                            item = items_with_images[current_item]
                            cell = img_table.cell(row, col)
                            
                            try:
                                # Add the image - slightly smaller to fit 4 per page
                                paragraph = cell.paragraphs[0]
                                run = paragraph.add_run()
                                run.add_picture(item.image.path, width=Inches(2.2))
                                
                                # Add item name below image
                                name_paragraph = cell.add_paragraph()
                                name_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                name_run = name_paragraph.add_run(f"{item.name}")
                                name_run.bold = True
                            except Exception as e:
                                print(f"Error adding image for {item.name}: {e}")
                            
                            current_item += 1
    
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
    document.core_properties.title = f"Quotation Number {quotation.quotation_number.upper() if quotation.quotation_number else quotation.id}"
    document.core_properties.author = "Skids LOGISTICS LTD"
    
    # Company information in a single line
    company_info = document.add_paragraph()
    company_run = company_info.add_run('Skids LOGISTICS LTD | ')
    company_run.bold = True
    company_info.add_run('NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt | ')
    company_info.add_run('Phone: 07035495280 | Email: info@skidslogistics.com | ')
    company_info.add_run('Website: www.skidslogistics.com')
    
    # Add logo after the company information
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/skids_logo.png')
        if not os.path.exists(logo_path):
            # Fallback to old path if new path doesn't exist
            logo_path = os.path.join(settings.STATIC_ROOT, 'img/logo.png')
        if os.path.exists(logo_path):
            # Center align the logo
            logo_paragraph = document.add_paragraph()
            logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_run = logo_paragraph.add_run()
            logo_run.add_picture(logo_path, width=Inches(3))
    except Exception as e:
        print(f"Error adding logo: {e}")
    
    # Add demarcation line
    document.add_paragraph().add_run('_' * 80)
    
    # Add watermark if logo exists
    try:
        if os.path.exists(logo_path):
            add_watermark(document, logo_path)
    except Exception as e:
        print(f"Error adding watermark: {e}")
    
    # Quotation title
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(f"QUOTATION {quotation.quotation_number.upper() if quotation.quotation_number else quotation.id}")
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
    header_cells[0].text = "DESCRIPTION"
    header_cells[1].text = "QUANTITY"
    header_cells[2].text = f"UNIT PRICE ({quotation.currency})"
    header_cells[3].text = f"TOTAL ({quotation.currency})"
    header_cells[4].text = "LEAD TIME"
    
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
    
    # Create a left-aligned paragraph for each total line to match PDF style
    subtotal_para = document.add_paragraph()
    subtotal_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    subtotal_para.add_run(f"Subtotal: {quotation.currency} {'{:,.0f}'.format(quotation.subtotal)}")
    
    vat_para = document.add_paragraph()
    vat_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    vat_para.add_run(f"VAT ({quotation.vat_percentage}%): {quotation.currency} {'{:,.0f}'.format(quotation.vat_amount)}")
    
    # Add a line before the total
    document.add_paragraph().add_run('_' * 30)
    
    # Make the total bold
    total_para = document.add_paragraph()
    total_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    total_run = total_para.add_run(f"Total: {quotation.currency} {'{:,.0f}'.format(quotation.total)}")
    total_run.bold = True
    
    # Notes if present
    if quotation.notes:
        document.add_paragraph()
        notes_para = document.add_paragraph()
        notes_run = notes_para.add_run("Notes:")
        notes_run.bold = True
        document.add_paragraph(quotation.notes)
    
    # Add images on a new page if any items have images
    has_images = False
    for item in quotation.items.all():
        if item.image:
            has_images = True
            break
    
    if has_images:
        # Add page break before images
        document.add_page_break()
        
        # Add images title
        images_title = document.add_paragraph()
        images_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        images_title_run = images_title.add_run("ITEM IMAGES")
        images_title_run.bold = True
        images_title_run.font.size = Pt(14)
        
        # Create a table for images (2 columns x 2 rows = 4 images per page)
        if quotation.items.filter(image__isnull=False).count() > 0:
            # Count items with images
            items_with_images = [item for item in quotation.items.all() if item.image]
            num_items = len(items_with_images)
            
            # Process 4 images per page
            images_per_page = 4
            current_item = 0
            
            while current_item < num_items:
                # For each page (except the first which already has a page break)
                if current_item > 0 and current_item % images_per_page == 0:
                    document.add_page_break()
                    # Add images title on new page
                    new_page_title = document.add_paragraph()
                    new_page_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    new_page_title_run = new_page_title.add_run("ITEM IMAGES (CONTINUED)")
                    new_page_title_run.bold = True
                    new_page_title_run.font.size = Pt(14)
                
                # Calculate how many images to process on this page (max 4)
                images_remaining = num_items - current_item
                images_on_this_page = min(images_per_page, images_remaining)
                
                # Calculate rows needed (2 columns, so divide by 2 and round up)
                rows_needed = (images_on_this_page + 1) // 2
                
                # Create table for this page's images
                img_table = document.add_table(rows=rows_needed, cols=2)
                img_table.style = 'Table Grid'
                
                # Add images to table
                for row in range(rows_needed):
                    for col in range(2):
                        if current_item < num_items:
                            item = items_with_images[current_item]
                            cell = img_table.cell(row, col)
                            
                            try:
                                # Add the image - slightly smaller to fit 4 per page
                                paragraph = cell.paragraphs[0]
                                run = paragraph.add_run()
                                run.add_picture(item.image.path, width=Inches(2.2))
                                
                                # Add item name below image
                                name_paragraph = cell.add_paragraph()
                                name_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                name_run = name_paragraph.add_run(f"{item.name}")
                                name_run.bold = True
                            except Exception as e:
                                print(f"Error adding image for {item.name}: {e}")
                            
                            current_item += 1
    
    # Save to memory
    docx_buffer = BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)
    
    # Create response
    response = HttpResponse(docx_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="Quotation_{quotation.quotation_number}.docx"'
    
    return response