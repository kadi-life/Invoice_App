from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('new/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/view/', views.view_invoice, name='view_invoice'),
    path('<int:pk>/edit/', views.invoice_detail, name='invoice_edit'),
    path('<int:pk>/update-status/', views.update_invoice_status, name='update_invoice_status'),
    path('<int:pk>/pdf/', views.export_invoice_pdf, name='invoice_pdf'),
    path('<int:pk>/delete/', views.delete_invoice, name='delete_invoice'),
    path('<int:pk>/mark-paid/', views.mark_as_paid, name='mark_as_paid'),
    path('<int:pk>/email/', views.email_invoice, name='invoice_email'),
    path('check-number/', views.check_invoice_number, name='check_invoice_number'),
]