from django import forms
from .models import Fee, Payment
from students.models import Student

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = ['student', 'amount', 'due_date', 'status']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BulkFeeForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(max_digits=8, decimal_places=2)
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_date', 'payment_method', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
        }