from django.urls import path
from . import views

urlpatterns = [
    path('', views.quotation_list, name='quotation_list'),
    path('new/', views.quotation_detail, name='quotation_detail'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('<int:pk>/view/', views.view_quotation, name='view_quotation'),
    path('<int:pk>/edit/', views.quotation_detail, name='quotation_edit'),
    path('<int:pk>/pdf/', views.quotation_pdf, name='quotation_pdf'),
    path('<int:pk>/delete/', views.delete_quotation, name='delete_quotation'),
    path('<int:pk>/convert/', views.convert_to_invoice, name='quotation_convert'),
    path('check-number/', views.check_quotation_number, name='check_quotation_number'),
]