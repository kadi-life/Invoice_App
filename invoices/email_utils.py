from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .utils import render_to_pdf
import os

def send_invoice_email(invoice, recipient_email, message=None):
    """
    Send an invoice to a client via email with PDF attachment
    
    Args:
        invoice: The Invoice model instance
        recipient_email: Email address of the recipient
        message: Optional custom message to include in the email
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Prepare context data for the email template
        context = {
            'invoice': invoice,
            'company_name': 'Your Company Name',  # Customize with your company details
            'message': message or f"Please find attached invoice #{invoice.id} for your records.",
        }
        
        # Render email content from template
        email_html = render_to_string('invoices/email/invoice_email.html', context)
        
        # Create email
        subject = f"Invoice #{invoice.id} from {context['company_name']}"
        email = EmailMessage(
            subject=subject,
            body=email_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.content_subtype = "html"  # Set content type to HTML
        
        # Generate PDF attachment
        pdf_context = {
            'invoice': invoice,
            'company_name': context['company_name'],
            'company_address': '123 Business Street, City, Country',
            'company_phone': '+1 234 567 890',
            'company_email': 'contact@yourcompany.com',
            'company_website': 'www.yourcompany.com',
        }
        
        # Temporarily disabled PDF attachment due to dependency issues
        # pdf_content = render_to_pdf('invoices/invoice_pdf.html', pdf_context)
        # 
        # if pdf_content:
        #     # Attach PDF to email
        #     email.attach(f"Invoice_{invoice.id}.pdf", pdf_content.getvalue(), 'application/pdf')
        
        # For now, just send the email without attachment
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending invoice email: {str(e)}")
        return False