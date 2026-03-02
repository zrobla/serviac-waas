"""SERVIAC CRM - API Serializers"""
from rest_framework import serializers
from ..models import Customer, Product, Category, OrderInbox, Notification


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    can_order = serializers.BooleanField(read_only=True)
    available_credit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    
    class Meta:
        model = Customer
        fields = '__all__'


class OrderInboxSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, allow_null=True)
    client_name = serializers.CharField(read_only=True)
    client_phone = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = OrderInbox
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
