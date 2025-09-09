from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Invoice
from quotations.models import Item
from django.http import JsonResponse, HttpResponse
import json
from datetime import datetime, timedelta
from decimal import Decimal
from .utils import generate_invoice_pdf
from .email_utils import send_invoice_email
from django.db.models import Q

@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(user=request.user).order_by('-date_created')
    # Filters
    q = request.GET.get('q')
    status = request.GET.get('status')
    start = request.GET.get('start')
    end = request.GET.get('end')
    min_amt = request.GET.get('min')
    max_amt = request.GET.get('max')
    if q:
        invoices = invoices.filter(Q(client_name__icontains=q))
    if status:
        invoices = invoices.filter(status=status)
    if start:
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d').date()
            invoices = invoices.filter(date_created__date__gte=start_date)
        except Exception:
            pass
    if end:
        try:
            end_date = datetime.strptime(end, '%Y-%m-%d').date()
            invoices = invoices.filter(date_created__date__lte=end_date)
        except Exception:
            pass
    if min_amt:
        try:
            invoices = invoices.filter(total__gte=Decimal(min_amt))
        except Exception:
            pass
    if max_amt:
        try:
            invoices = invoices.filter(total__lte=Decimal(max_amt))
        except Exception:
            pass
    
    # Calculate summary statistics
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(status='Paid').count()
    overdue_invoices = sum(1 for invoice in invoices if invoice.is_overdue())
    
    context = {
        'invoices': invoices,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'overdue_invoices': overdue_invoices
    }
    
    return render(request, 'invoices/invoice_list.html', context)

@login_required
def invoice_detail(request, pk=None):
    if pk:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    else:
        invoice = None
    
    if request.method == 'POST':
        # Prevent editing once created
        if pk:
            messages.error(request, 'Editing invoices is disabled for integrity. Create a new invoice instead.')
            return redirect('invoice_detail', pk=pk)
        
        data = request.POST
        
        # Set due date (default to 30 days from today if not provided)
        due_date_str = data.get('due_date')
        if not due_date_str:
            due_date = (datetime.now() + timedelta(days=30)).date()
        else:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except Exception:
                due_date = (datetime.now() + timedelta(days=30)).date()
        
        vat_pct = data.get('vat_percentage') or '7.5'
        try:
            vat_pct_val = Decimal(vat_pct)
        except Exception:
            vat_pct_val = Decimal('7.5')
        
        status_val = data.get('status', 'Pending') or 'Pending'
        notes_val = data.get('notes', '') or ''
        client_name_val = data.get('client_name') or ''
        
        # Check if invoice number already exists
        invoice_number = data.get('invoice_number') or ''
        if invoice_number:
            existing_invoice = Invoice.objects.filter(invoice_number=invoice_number).first()
            if existing_invoice:
                messages.error(request, f'Invoice number "{invoice_number}" has already been used. Please choose a different number.')
                return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})
        
        # Create new invoice with safe defaults
        invoice = Invoice(
            user=request.user,
            invoice_number=invoice_number,
            client_name=client_name_val,
            currency=(data.get('currency') or 'NGN'),
            vat_percentage=vat_pct_val,
            due_date=due_date,
            status=status_val,
            notes=notes_val,
            subtotal=Decimal('0.00'),
            vat_amount=Decimal('0.00'),
            total=Decimal('0.00'),
            date_created=datetime.now()
        )
        invoice.save()
        
        # Process items
        item_names = request.POST.getlist('item_name[]')
        item_prices = request.POST.getlist('item_price[]')
        item_quantities = request.POST.getlist('item_quantity[]')
        item_images = request.FILES.getlist('item_image[]')
        for i in range(len(item_names)):
            name = item_names[i]
            price_str = item_prices[i] if i < len(item_prices) else ''
            qty_str = item_quantities[i] if i < len(item_quantities) else ''
            if name and price_str and qty_str:
                try:
                    price_val = Decimal(price_str)
                    qty_val = int(qty_str)
                except Exception:
                    continue
                image_file = item_images[i] if i < len(item_images) else None
                item = Item.objects.create(
                    name=name,
                    price=price_val,
                    quantity=qty_val,
                    image=image_file
                )
                invoice.items.add(item)
        
        # Calculate totals
        invoice.calculate_totals()
        invoice.save()
        
        messages.success(request, 'Invoice saved successfully!')
        return redirect('invoice_list')
    
    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})

@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete associated items
        for item in invoice.items.all():
            item.delete()
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')
        return redirect('invoice_list')
    
    return render(request, 'invoices/delete_confirm.html', {'invoice': invoice})

@login_required
def mark_as_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    invoice.status = 'Paid'
    invoice.save()
    messages.success(request, 'Invoice marked as paid!')
    return redirect('invoice_detail', pk=pk)

@login_required
def update_invoice_status(request, pk):
    """Update only the status of an invoice"""
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, pk=pk)
    else:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Invoice.STATUS_CHOICES):
            invoice.status = new_status
            invoice.save()
            messages.success(request, f'Invoice status updated to {invoice.get_status_display()}')
        else:
            messages.error(request, 'Invalid status value')
        return redirect('view_invoice', pk=pk)
    
    context = {
        'invoice': invoice,
        'status_choices': Invoice.STATUS_CHOICES,
    }
    return render(request, 'invoices/update_status.html', context)

@login_required
def export_invoice_pdf(request, pk):
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, pk=pk)
    else:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    return generate_invoice_pdf(invoice)

@login_required
def email_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email')
        message = request.POST.get('message')
        
        if recipient_email:
            # Send email with invoice
            success = send_invoice_email(invoice, recipient_email, message)
            
            if success:
                messages.success(request, f'Invoice #{invoice.id} has been emailed to {recipient_email}')
                return redirect('invoice_detail', pk=pk)
            else:
                messages.error(request, 'Failed to send email. Please try again.')
        else:
            messages.error(request, 'Recipient email is required')
    
    return render(request, 'invoices/email_invoice.html', {'invoice': invoice})

@login_required
def view_invoice(request, pk):
    """View an invoice in detail"""
    if request.user.is_staff:
        invoice = get_object_or_404(Invoice, pk=pk)
    else:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    context = {
        'invoice': invoice,
    }
    return render(request, 'invoices/invoice_view.html', context)

@login_required
def check_invoice_number(request):
    """Check if an invoice number already exists"""
    number = request.GET.get('number', '').strip()
    if not number:
        return JsonResponse({'exists': False})
    
    exists = Invoice.objects.filter(invoice_number=number).exists()
    return JsonResponse({'exists': exists})
