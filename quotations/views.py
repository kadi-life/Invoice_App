from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quotation, Item
from django.http import JsonResponse
import json
import re
from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import get_template
from invoices.utils import render_to_pdf
from django.db.models import Q
from datetime import datetime

@login_required
def quotation_list(request):
    quotations = Quotation.objects.filter(user=request.user).order_by('-date_created')
    # Filters
    q = request.GET.get('q')
    start = request.GET.get('start')
    end = request.GET.get('end')
    min_amt = request.GET.get('min')
    max_amt = request.GET.get('max')
    if q:
        quotations = quotations.filter(Q(client_name__icontains=q))
    if start:
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            quotations = quotations.filter(date_created__date__gte=start_date)
        except Exception:
            pass
    if end:
        try:
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
            quotations = quotations.filter(date_created__date__lte=end_date)
        except Exception:
            pass
    if min_amt:
        try:
            quotations = quotations.filter(total__gte=Decimal(min_amt))
        except Exception:
            pass
    if max_amt:
        try:
            quotations = quotations.filter(total__lte=Decimal(max_amt))
        except Exception:
            pass
    return render(request, 'quotations/quotation_list.html', {'quotations': quotations})

@login_required
def quotation_detail(request, pk=None):
    if pk:
        quotation = get_object_or_404(Quotation, pk=pk, user=request.user)
    else:
        quotation = None
    
    if request.method == 'POST':
        # Prevent editing once created
        if pk:
            messages.error(request, 'Editing quotations is disabled for integrity. Create a new quotation instead.')
            return redirect('quotation_detail', pk=pk)
        
        data = request.POST
        
        vat_pct = data.get('vat_percentage') or '7.5'
        try:
            vat_pct_val = Decimal(vat_pct)
        except Exception:
            vat_pct_val = Decimal('7.5')
        
        # Check if quotation number already exists
        quotation_number = data.get('quotation_number') or ''
        if quotation_number:
            existing_quotation = Quotation.objects.filter(quotation_number=quotation_number).first()
            if existing_quotation:
                messages.error(request, f'Quotation number "{quotation_number}" has already been used. Please choose a different number.')
                return render(request, 'quotations/quotation_detail.html', {'quotation': quotation})
        
        # Create new quotation with safe defaults
        quotation = Quotation(
            user=request.user,
            quotation_number=quotation_number,
            client_name=(data.get('client_name') or ''),
            rfq_number=(data.get('rfq_number') or ''),
            vessel_name=(data.get('vessel_name') or ''),
            currency=(data.get('currency') or 'NGN'),
            subtotal=Decimal('0.00'),
            vat_percentage=vat_pct_val,
            vat_amount=Decimal('0.00'),
            total=Decimal('0.00'),
            notes=(data.get('notes') or ''),
            date_created=datetime.now()
        )
        quotation.save()
        
        # Process items
        item_names = request.POST.getlist('item_name[]')
        item_prices = request.POST.getlist('item_price[]')
        item_quantity_displays = request.POST.getlist('item_quantity_display[]')
        item_units = request.POST.getlist('item_unit[]')
        item_lead_times = request.POST.getlist('item_lead_time[]')
        item_images = request.FILES.getlist('item_image[]')
        for i in range(len(item_names)):
            name = item_names[i]
            price_str = item_prices[i] if i < len(item_prices) else ''
            qty_display = item_quantity_displays[i] if i < len(item_quantity_displays) else ''
            unit = item_units[i] if i < len(item_units) else 'EA'
            lead_time_str = item_lead_times[i] if i < len(item_lead_times) else ''
            if name and price_str and qty_display:
                try:
                    price_val = Decimal(price_str)
                    # Extract numeric value from quantity display field
                    qty_match = re.match(r'^(\d+)', qty_display.strip())
                    if qty_match:
                        qty_val = int(qty_match.group(1))
                    else:
                        qty_val = 1
                except Exception:
                    continue
                image_file = item_images[i] if i < len(item_images) else None
                item = Item.objects.create(
                    name=name,
                    price=price_val,
                    quantity=qty_val,
                    unit=unit,
                    image=image_file,
                    lead_time=lead_time_str
                )
                quotation.items.add(item)
        
        # Calculate totals
        quotation.calculate_totals()
        quotation.save()
        
        messages.success(request, 'Quotation saved successfully!')
        return redirect('quotation_list')
    
    return render(request, 'quotations/quotation_detail.html', {'quotation': quotation})

@login_required
def quotation_pdf(request, pk):
    if request.user.is_staff:
        quotation = get_object_or_404(Quotation, pk=pk)
    else:
        quotation = get_object_or_404(Quotation, pk=pk, user=request.user)
    context = {
        'quotation': quotation,
        'company_name': 'Skids LOGISTICS LTD',
        'company_address': 'NO. 17 Eastern Bypass, Buchi Atako Villa, Port Harcourt',
        'company_phone': '07035495280',
        'company_email': 'info@skidslogistics.com',
        'company_website': 'www.skidslogistics.com',
    }
    return render_to_pdf('quotations/quotation_pdf.html', context)

@login_required
def quotation_docx(request, pk):
    if request.user.is_staff:
        quotation = get_object_or_404(Quotation, pk=pk)
    else:
        quotation = get_object_or_404(Quotation, pk=pk, user=request.user)
    from invoices.docx_utils import generate_quotation_docx
    return generate_quotation_docx(quotation)

@login_required
def delete_quotation(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete associated items
        for item in quotation.items.all():
            item.delete()
        quotation.delete()
        messages.success(request, 'Quotation deleted successfully!')
        return redirect('quotation_list')
    
    return render(request, 'quotations/delete_confirm.html', {'quotation': quotation})

@login_required
def convert_to_invoice(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk, user=request.user)
    
    # Import Invoice model here to avoid circular imports
    from invoices.models import Invoice
    
    # Create a new invoice with the same data as the quotation
    invoice = Invoice(
        user=request.user,
        invoice_number=f"INV-{quotation.quotation_number or quotation.id}",
        client_name=quotation.client_name,
        vat_percentage=quotation.vat_percentage,
        subtotal=quotation.subtotal,
        vat_amount=quotation.vat_amount,
        total=quotation.total,
        due_date=quotation.date_created.date(),
        status='Pending',
        notes=quotation.notes
    )
    invoice.save()
    
    # Copy items from quotation to invoice
    for item in quotation.items.all():
        # Create a new item with the same data
        new_item = Item.objects.create(
            name=item.name,
            price=item.price,
            quantity=item.quantity
        )
        invoice.items.add(new_item)
    
    # Calculate totals and save
    invoice.calculate_totals()
    invoice.save()
    
    messages.success(request, f'Quotation #{quotation.quotation_number or quotation.id} successfully converted to Invoice #{invoice.invoice_number}')
    return redirect('invoice_detail', pk=invoice.id)

@login_required
def check_quotation_number(request):
    """Check if a quotation number already exists"""
    number = request.GET.get('number', '').strip()
    if not number:
        return JsonResponse({'exists': False})
    
    exists = Quotation.objects.filter(quotation_number=number).exists()
    return JsonResponse({'exists': exists})

@login_required
def view_quotation(request, pk):
    """View a quotation in detail"""
    if request.user.is_staff:
        quotation = get_object_or_404(Quotation, pk=pk)
    else:
        quotation = get_object_or_404(Quotation, pk=pk, user=request.user)
    
    context = {
        'quotation': quotation,
    }
    return render(request, 'quotations/quotation_view.html', context)
