from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm, AdminUserEditForm
from .models import CustomUser
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import json

def is_staff_user(user):
    return user.is_staff

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'users/landing.html')

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('admin_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, 'Only staff members can register new users.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Ensure Admin role sets is_staff
        try:
            user = form.save(commit=False)
            if user.role == 'Admin':
                user.is_staff = True
            user.save()
            messages.success(self.request, f'User {form.cleaned_data.get("email")} has been registered successfully.')
            return redirect(self.success_url)
        except Exception as e:
            import logging
            logger = logging.getLogger('users')
            logger.error(f"Exception during user registration: {str(e)}")
            messages.error(self.request, f"Registration failed due to an error: {str(e)}")
            return self.render_to_response(self.get_context_data(form=form))
        
    def form_invalid(self, form):
        # Log form errors for debugging in production
        import logging
        logger = logging.getLogger('users')
        logger.error(f"User registration form errors: {form.errors}")
        logger.error(f"Request POST data: {self.request.POST}")
        logger.error(f"CSRF token in POST: {'csrfmiddlewaretoken' in self.request.POST}")
        logger.error(f"CSRF cookie present: {'CSRF_COOKIE' in self.request.META}")
        
        # Add error message for user
        from django.contrib import messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        
        return super().form_invalid(form)

def login_view(request):
    if request.method == 'POST':
        # Get email and password directly from POST data
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Add debug message
        messages.info(request, f"Attempting login with email: {email}")
        
        # Try to find the user first
        try:
            user_exists = CustomUser.objects.filter(email=email).exists()
            if not user_exists:
                messages.error(request, f"No user found with email: {email}")
            else:
                user = CustomUser.objects.get(email=email)
                if not user.is_active:
                    messages.error(request, "This account is inactive.")
        except Exception as e:
            messages.error(request, f"Error checking user: {str(e)}")
        
        # Process the form
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Simple authentication approach
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                response = redirect('dashboard')
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                messages.error(request, 'Authentication failed. Please check your credentials.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomAuthenticationForm()
    response = render(request, 'users/login.html', {'form': form})
    # Add cache control headers to prevent browser back button issues
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def logout_view(request):
    response = redirect('login')
    # Add cache control headers to prevent browser back button from showing logged-in pages
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    logout(request)
    return response

@login_required
def dashboard(request):
    # Ensure cache control headers are set for all protected views
    response = render(request, 'users/dashboard.html', get_dashboard_context(request))
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def get_dashboard_context(request):
    # Get counts for dashboard statistics
    from invoices.models import Invoice
    from quotations.models import Quotation
    
    # Invoice counts
    invoices_qs = Invoice.objects.filter(user=request.user)
    invoice_count = invoices_qs.count()
    paid_count = invoices_qs.filter(status='Paid').count()
    pending_count = invoices_qs.filter(status='Pending').count()
    overdue_count = sum(1 for invoice in invoices_qs if invoice.is_overdue())
    
    # Quotation count
    quotation_count = Quotation.objects.filter(user=request.user).count()
    
    # Recent items
    recent_invoices = invoices_qs.order_by('-date_created')[:5]
    recent_quotations = Quotation.objects.filter(user=request.user).order_by('-date_created')[:5]
    
    # Monthly revenue for last 6 months
    monthly_revenue = []
    now = timezone.now()
    for i in range(5, -1, -1):
        month_date = (now - timedelta(days=30*i))
        year = month_date.year
        month = month_date.month
        month_label = month_date.strftime('%b')
        month_total = sum((inv.total for inv in invoices_qs.filter(date_created__year=year, date_created__month=month)), Decimal('0.00'))
        monthly_revenue.append({'month': month_label, 'amount': float(month_total)})
    
    # Status data for chart
    invoice_status = [
        {'status': 'Paid', 'count': paid_count},
        {'status': 'Pending', 'count': pending_count},
        {'status': 'Overdue', 'count': overdue_count},
    ]

    
    context = {
        'invoice_count': invoice_count,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'quotation_count': quotation_count,
        'recent_invoices': recent_invoices,
        'recent_quotations': recent_quotations,
        'monthly_revenue': json.dumps(monthly_revenue),
        'invoice_status': json.dumps(invoice_status),
    }
    
    return context

@login_required
@user_passes_test(is_staff_user)
def admin_dashboard(request):
    # Get the context and render with cache control headers
    context = get_admin_dashboard_context(request)
    response = render(request, 'users/admin_dashboard.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
    
def get_admin_dashboard_context(request):
    from django.core.paginator import Paginator
    from quotations.models import Quotation
    from invoices.models import Invoice

    users = CustomUser.objects.all().order_by('-date_joined')
    total_users = users.count()
    staff_users = users.filter(is_staff=True).count()
    active_users = users.filter(is_active=True).count()

    # Quotations pagination
    quotation_list = Quotation.objects.all().order_by('-date_created')
    quotation_paginator = Paginator(quotation_list, 10)
    quotation_page = request.GET.get('quotation_page')
    quotations = quotation_paginator.get_page(quotation_page)

    # Invoices pagination with status counts
    invoice_list = Invoice.objects.all().order_by('-date_created')
    invoice_paginator = Paginator(invoice_list, 10)
    
    # Real-time status counts
    status_counts = {
        'total': invoice_list.count(),
        'paid': invoice_list.filter(status='Paid').count(),
        'pending': invoice_list.filter(status='Pending').count(),
        'overdue': len([inv for inv in invoice_list if inv.is_overdue()])
    }
    invoice_page = request.GET.get('invoice_page')
    invoices = invoice_paginator.get_page(invoice_page)

    context = {
        'users': users,
        'total_users': total_users,
        'staff_users': staff_users,
        'active_users': active_users,
        'quotations': quotations,
        'invoices': invoices,
        'status_counts': status_counts,
    }
    return context

@login_required
@user_passes_test(is_staff_user)
def admin_user_detail(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    response = render(request, 'users/admin_user_detail.html', {'user_obj': user_obj})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
@user_passes_test(is_staff_user)
def admin_user_edit(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            edited_user = form.save(commit=False)
            if edited_user.role == 'Admin':
                edited_user.is_staff = True
            edited_user.save()
            messages.success(request, 'User updated successfully')
            response = redirect('admin_dashboard')
            # Add cache control headers
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
    else:
        form = AdminUserEditForm(instance=user_obj)
    response = render(request, 'users/admin_user_edit.html', {'form': form, 'user_obj': user_obj})
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
@user_passes_test(is_staff_user)
def admin_user_toggle_active(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    
    # Prevent non-superusers from deactivating admin users
    if user_obj.is_staff and not request.user.is_superuser:
        messages.error(request, "Only superusers can activate/deactivate admin users.")
        response = redirect('admin_dashboard')
        # Add cache control headers
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    messages.success(request, f"User {'activated' if user_obj.is_active else 'deactivated'} successfully")
    response = redirect('admin_dashboard')
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@login_required
def profile(request):
    if request.method == 'POST':
        # Handle profile update
        if 'first_name' in request.POST:
            user = request.user
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                try:
                    # Delete old profile picture if it exists
                    if user.profile_picture:
                        try:
                            user.profile_picture.delete(save=False)
                        except Exception as e:
                            # Log the error but continue
                            print(f"Error deleting old profile picture: {e}")
                    
                    # Save new profile picture
                    user.profile_picture = request.FILES['profile_picture']
                    messages.success(request, 'Profile picture updated successfully')
                except Exception as e:
                    messages.error(request, f'Error updating profile picture: {e}')
            
            try:
                user.save()
                messages.success(request, 'Profile updated successfully')
            except Exception as e:
                messages.error(request, f'Error updating profile: {e}')
                
            response = redirect('profile')
            # Add cache control headers
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
    
    response = render(request, 'users/profile.html')
    # Add cache control headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
