from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import csv

from students.models import Student
from .models import Fee, Payment
from .forms import FeeForm, BulkFeeForm, PaymentForm

# Basic CRUD Operations
@login_required
def fee_list(request):
    fees = Fee.objects.all().order_by('-due_date')
    
    # Filtering
    status = request.GET.get('status')
    if status in ['Paid', 'Unpaid']:
        fees = fees.filter(status=status)
    
    student_id = request.GET.get('student')
    if student_id:
        fees = fees.filter(student__id=student_id)
    
    context = {
        'fees': fees,
        'students': Student.objects.all(),
        'total_amount': fees.aggregate(Sum('amount'))['amount__sum'] or 0,
        'paid_amount': fees.filter(status='Paid').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    return render(request, 'fees/fee_list.html', context)

@login_required
def fee_detail(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    payments = fee.payment_set.all()
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.fee = fee
            payment.processed_by = request.user
            payment.save()
            
            # Update fee status if fully paid
            if fee.amount <= payment.amount:
                fee.status = 'Paid'
                fee.save()
            
            messages.success(request, 'Payment recorded successfully!')
            return redirect('fees:fee_detail', pk=fee.pk)
    else:
        form = PaymentForm()
    
    context = {
        'fee': fee,
        'payments': payments,
        'form': form,
        'balance': fee.amount - (payments.aggregate(Sum('amount'))['amount__sum'] or 0),
    }
    return render(request, 'fees/fee_detail.html', context)

@login_required
def create_fee(request):
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save()
            messages.success(request, 'Fee record created successfully!')
            return redirect('fees:fee_detail', pk=fee.pk)
    else:
        form = FeeForm()
    
    return render(request, 'fees/fee_form.html', {'form': form, 'title': 'Create Fee'})

@login_required
def update_fee(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    if request.method == 'POST':
        form = FeeForm(request.POST, instance=fee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee record updated successfully!')
            return redirect('fees:fee_detail', pk=fee.pk)
    else:
        form = FeeForm(instance=fee)
    
    return render(request, 'fees/fee_form.html', {'form': form, 'title': 'Update Fee'})

@login_required
def delete_fee(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    if request.method == 'POST':
        fee.delete()
        messages.success(request, 'Fee record deleted successfully!')
        return redirect('fees:fee_list')
    
    return render(request, 'fees/fee_confirm_delete.html', {'fee': fee})

# Status Management
@login_required
def mark_fee_paid(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    if fee.status != 'Paid':
        fee.status = 'Paid'
        fee.save()
        messages.success(request, f'Fee marked as paid for {fee.student}')
    else:
        messages.warning(request, 'Fee is already marked as paid')
    
    return redirect('fees:fee_detail', pk=fee.pk)

# Student-Specific Views
@login_required
def student_fee_list(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    fees = Fee.objects.filter(student=student).order_by('-due_date')
    
    context = {
        'student': student,
        'fees': fees,
        'total_owed': fees.filter(status='Unpaid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_paid': fees.filter(status='Paid').aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    return render(request, 'fees/student_fee_list.html', context)

@login_required
def create_student_fee(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.student = student
            fee.save()
            messages.success(request, 'Fee created successfully for student!')
            return redirect('fees:student_fee_list', student_id=student.pk)
    else:
        form = FeeForm(initial={'student': student})
    
    return render(request, 'fees/fee_form.html', {
        'form': form,
        'title': f'Create Fee for {student}',
        'student': student,
    })

# Bulk Operations
@login_required
def bulk_create_fees(request):
    if request.method == 'POST':
        form = BulkFeeForm(request.POST)
        if form.is_valid():
            students = form.cleaned_data['students']
            amount = form.cleaned_data['amount']
            due_date = form.cleaned_data['due_date']
            
            created = 0
            for student in students:
                Fee.objects.create(
                    student=student,
                    amount=amount,
                    due_date=due_date,
                    status='Unpaid'
                )
                created += 1
            
            messages.success(request, f'Successfully created {created} fee records!')
            return redirect('fees:fee_list')
    else:
        form = BulkFeeForm()
    
    return render(request, 'fees/bulk_fee_form.html', {'form': form})

# Reports
@login_required
def fee_overview_report(request):
    fees = Fee.objects.all()
    paid = fees.filter(status='Paid').count()
    unpaid = fees.filter(status='Unpaid').count()
    
    context = {
        'total_fees': fees.count(),
        'paid_fees': paid,
        'unpaid_fees': unpaid,
        'total_amount': fees.aggregate(Sum('amount'))['amount__sum'] or 0,
        'paid_amount': fees.filter(status='Paid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'unpaid_amount': fees.filter(status='Unpaid').aggregate(Sum('amount'))['amount__sum'] or 0,
        'students_with_unpaid': Student.objects.annotate(
            unpaid_count=Count('fee', filter=models.Q(fee__status='Unpaid'))
                                .filter(unpaid_count__gt=0).count(),
    }
    return render(request, 'fees/reports/overview.html', context)

@login_required
def unpaid_fees_report(request):
    fees = Fee.objects.filter(status='Unpaid').order_by('due_date')
    return render(request, 'fees/reports/unpaid.html', {'fees': fees})

@login_required
def export_fees(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fees_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student', 'Amount', 'Status', 'Due Date', 'Created At'])
    
    for fee in Fee.objects.all():
        writer.writerow([
            fee.student,
            fee.amount,
            fee.status,
            fee.due_date,
            fee.created_at,
        ])
    
    return response

# Due Date Management
@login_required
def upcoming_due_fees(request):
    date_from = timezone.now().date()
    date_to = date_from + timedelta(days=30)
    fees = Fee.objects.filter(
        due_date__range=[date_from, date_to],
        status='Unpaid'
    ).order_by('due_date')
    
    return render(request, 'fees/due/upcoming.html', {'fees': fees})

@login_required
def overdue_fees(request):
    fees = Fee.objects.filter(
        due_date__lt=timezone.now().date(),
        status='Unpaid'
    ).order_by('due_date')
    
    return render(request, 'fees/due/overdue.html', {'fees': fees})

# Payment Processing
@login_required
def process_payment(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.fee = fee
            payment.processed_by = request.user
            payment.save()
            
            # Check if fee is fully paid
            total_paid = fee.payment_set.aggregate(Sum('amount'))['amount__sum'] or 0
            if total_paid >= fee.amount:
                fee.status = 'Paid'
                fee.save()
            
            messages.success(request, 'Payment processed successfully!')
            return redirect('fees:fee_detail', pk=fee.pk)
    else:
        form = PaymentForm(initial={'amount': fee.amount})
    
    return render(request, 'fees/payment_form.html', {
        'form': form,
        'fee': fee,
        'balance': fee.amount - (fee.payment_set.aggregate(Sum('amount'))['amount__sum'] or 0),
    })

@login_required
def payment_history(request):
    payments = Payment.objects.all().order_by('-payment_date')
    return render(request, 'fees/payment_history.html', {'payments': payments})

# API Views
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .serializers import FeeSerializer

class FeeListAPI(LoginRequiredMixin, ListAPIView):
    queryset = Fee.objects.all()
    serializer_class = FeeSerializer

class FeeDetailAPI(LoginRequiredMixin, RetrieveAPIView):
    queryset = Fee.objects.all()
    serializer_class = FeeSerializer