from django.db import models
from django.conf import settings
from django.utils import timezone

class Item(models.Model):
    UNIT_CHOICES = [
        ('', ''),
        ('EA', 'Each'),
        ('PCS', 'Pieces'),
        ('KG', 'Kilograms'),
        ('LTR', 'Liters'),
        ('M', 'Meters'),
        ('BOX', 'Box'),
        ('SET', 'Set'),
        ('UNIT', 'Unit'),
    ]
    
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='', blank=True, verbose_name="Unit")
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    lead_time = models.CharField(max_length=50, blank=True, null=True, verbose_name="Lead Time")
    
    def __str__(self):
        return self.name
    
    @property
    def total(self):
        return self.price * self.quantity

class Quotation(models.Model):
    CURRENCY_CHOICES = [
        ('NGN', 'Nigerian Naira (₦)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quotation_number = models.CharField(max_length=100, verbose_name="Quotation Number", null=True, blank=True)
    client_name = models.CharField(max_length=255)
    rfq_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Request for Quotation Number")
    vessel_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vessel Name")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN', verbose_name="Currency")
    items = models.ManyToManyField(Item)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=7.5)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True, verbose_name="Additional Notes")
    
    def __str__(self):
        return f"Quotation {(self.quotation_number or self.id).upper()} for {self.client_name}"
    
    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items.all())
        self.vat_amount = self.subtotal * (self.vat_percentage / 100)
        self.total = self.subtotal + self.vat_amount
        return self.total
