from django.http import HttpResponse
from django.template.loader import get_template
import os
from django.conf import settings
try:
    from xhtml2pdf import pisa
    from io import BytesIO
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


def _link_callback(uri, rel):
    """Convert HTML URIs to absolute system paths for xhtml2pdf.
    Supports STATIC_URL and MEDIA_URL so images/fonts load inside PDFs."""
    # Handle absolute filesystem paths directly
    if os.path.isabs(uri) and os.path.exists(uri):
        return uri

    # Static files
    static_url = settings.STATIC_URL
    if uri.startswith(static_url):
        # Prefer STATIC_ROOT if collected; otherwise first STATICFILES_DIRS entry
        static_rel_path = uri.replace(static_url, '')
        static_root = getattr(settings, 'STATIC_ROOT', '')
        if static_root and os.path.isdir(static_root):
            path = os.path.join(static_root, static_rel_path)
        else:
            static_dirs = getattr(settings, 'STATICFILES_DIRS', [])
            base_dir = static_dirs[0] if static_dirs else os.path.join(settings.BASE_DIR, 'static')
            path = os.path.join(base_dir, static_rel_path)
        return path

    # Media files
    media_url = settings.MEDIA_URL
    if uri.startswith(media_url):
        media_rel_path = uri.replace(media_url, '')
        return os.path.join(settings.MEDIA_ROOT, media_rel_path)

    # Fallback: try joining BASE_DIR
    return os.path.join(settings.BASE_DIR, uri.lstrip('/'))


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    if not PDF_AVAILABLE:
        return HttpResponse(html, content_type='text/html')
    result = BytesIO()
    # Use CreatePDF with link_callback to resolve static/media URIs
    pdf = pisa.CreatePDF(src=BytesIO(html.encode('utf-8')), dest=result, encoding='utf-8', link_callback=_link_callback)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        return response
    return HttpResponse(html, content_type='text/html')


def generate_invoice_pdf(invoice):
    context = {
        'invoice': invoice,
        'company_name': 'Skids LOGISTICS LTD',
        'company_address': 'NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt',
        'company_phone': '07035495280',
        'company_email': 'info@skidslogistics.com',
        'company_website': 'www.skidslogistics.com',
    }
    return render_to_pdf('invoices/invoice_pdf.html', context)