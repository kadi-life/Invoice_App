from django.db import models
from django.conf import settings
from django.utils import timezone
from quotations.models import Item

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
    )
    
    CURRENCY_CHOICES = [
        ('NGN', 'Nigerian Naira (₦)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=100, verbose_name="Invoice Number", null=True, blank=True)
    client_name = models.CharField(max_length=255)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN', verbose_name="Currency")
    items = models.ManyToManyField(Item)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=7.5)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number or self.id} for {self.client_name}"
    
    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items.all())
        self.vat_amount = self.subtotal * (self.vat_percentage / 100)
        self.total = self.subtotal + self.vat_amount
        return self.total
    
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status != 'Paid'
