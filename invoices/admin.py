from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Invoice, Item

class ItemInline(admin.TabularInline):
    model = Invoice.items.through
    extra = 0
    verbose_name = "Item"
    verbose_name_plural = "Items"
    readonly_fields = ['item_details']
    
    def item_details(self, instance):
        item = instance.item
        return f"{item.name} - {item.quantity} {item.unit} - {item.price}"
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client_name', 'date_created', 'total', 'status', 'export_buttons']
    list_filter = ['status', 'date_created']
    search_fields = ['invoice_number', 'client_name']
    readonly_fields = ['subtotal', 'vat_amount', 'total', 'export_buttons']
    exclude = ['items']
    inlines = [ItemInline]
    
    def export_buttons(self, obj):
        pdf_url = reverse('invoice_pdf', args=[obj.id])
        docx_url = reverse('invoice_docx', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank">PDF</a>&nbsp;'
            '<a class="button" href="{}" target="_blank">Word</a>',
            pdf_url, docx_url
        )
    export_buttons.short_description = "Export"
    export_buttons.allow_tags = True
