"""SERVIAC CRM - Forms"""
from django import forms
from django.forms import inlineformset_factory
from .models import Customer, Product, Category, Order, OrderItem


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'customer_type', 'phone', 'phone_secondary', 'email',
            'address', 'city', 'company_registration', 'tax_id',
            'credit_limit', 'payment_terms', 'manual_score', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_type': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+225'}),
            'phone_secondary': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'company_registration': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.NumberInput(attrs={'class': 'form-control'}),
            'manual_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'code', 'category', 'description', 'unit',
            'price_b2b', 'price_b2c', 'stock_quantity', 'alert_threshold',
            'image', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'price_b2b': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_b2c': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'alert_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'delivery_address', 'delivery_date', 'customer_notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


OrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=OrderItemForm,
    extra=1, can_delete=True
)
