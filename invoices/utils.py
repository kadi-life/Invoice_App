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
    print(f"\n\n[DEBUG] Processing URI: {uri}\n\n")
    
    # Handle absolute filesystem paths directly
    if os.path.isabs(uri) and os.path.exists(uri):
        print(f"[DEBUG] Absolute path exists: {uri}")
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
        print(f"[DEBUG] Static path: {path} (Exists: {os.path.exists(path)})")
        return path

    # Media files
    media_url = settings.MEDIA_URL
    if uri.startswith(media_url):
        media_rel_path = uri.replace(media_url, '')
        media_path = os.path.join(settings.MEDIA_ROOT, media_rel_path)
        print(f"[DEBUG] Media URL: {uri} -> Path: {media_path} (Exists: {os.path.exists(media_path)})")
        # If the media path doesn't exist, try to find the file in the item_images directory
        if not os.path.exists(media_path):
            item_images_dir = os.path.join(settings.MEDIA_ROOT, 'item_images')
            if os.path.exists(item_images_dir):
                print(f"[DEBUG] Checking item_images directory: {item_images_dir}")
                # Get the filename from the path
                filename = os.path.basename(media_path)
                alternative_path = os.path.join(item_images_dir, filename)
                print(f"[DEBUG] Alternative path: {alternative_path} (Exists: {os.path.exists(alternative_path)})")
                if os.path.exists(alternative_path):
                    return alternative_path
        return media_path
    
    # Handle relative URLs that might be media files
    if uri.startswith('/media/'):
        media_rel_path = uri.replace('/media/', '')
        media_path = os.path.join(settings.MEDIA_ROOT, media_rel_path)
        print(f"[DEBUG] Relative Media URL: {uri} -> Path: {media_path} (Exists: {os.path.exists(media_path)})")
        # If the media path doesn't exist, try to find the file in the item_images directory
        if not os.path.exists(media_path):
            item_images_dir = os.path.join(settings.MEDIA_ROOT, 'item_images')
            if os.path.exists(item_images_dir):
                print(f"[DEBUG] Checking item_images directory: {item_images_dir}")
                # Get the filename from the path
                filename = os.path.basename(media_path)
                alternative_path = os.path.join(item_images_dir, filename)
                print(f"[DEBUG] Alternative path: {alternative_path} (Exists: {os.path.exists(alternative_path)})")
                if os.path.exists(alternative_path):
                    return alternative_path
        return media_path

    # Fallback: try joining BASE_DIR
    fallback_path = os.path.join(settings.BASE_DIR, uri.lstrip('/'))
    print(f"[DEBUG] Fallback path: {fallback_path} (Exists: {os.path.exists(fallback_path)})")
    return fallback_path


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


def generate_invoice_pdf(invoice, request=None):
    context = {
        'invoice': invoice,
        'company_name': 'Skids LOGISTICS LTD',
        'company_address': 'NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt',
        'company_phone': '07035495280',
        'company_email': 'info@skidslogistics.com',
        'company_website': 'www.skidslogistics.com',
    }
    
    # Add request to context if available
    if request:
        context['request'] = request
    
    return render_to_pdf('invoices/invoice_pdf.html', context)