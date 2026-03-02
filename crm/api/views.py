"""SERVIAC CRM - API Views"""
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User

from ..models import Customer, Product, Category, OrderInbox, Notification, OrderInboxStatus, NotificationType
from .serializers import CustomerSerializer, ProductSerializer, CategorySerializer, OrderInboxSerializer, NotificationSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """Customer API"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['customer_type', 'is_active', 'is_blocked', 'city']
    search_fields = ['name', 'phone', 'email']
    ordering_fields = ['name', 'created_at', 'balance']


class ProductViewSet(viewsets.ModelViewSet):
    """Product API"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'is_active', 'unit']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'price_b2c', 'stock_quantity']


class CategoryViewSet(viewsets.ModelViewSet):
    """Category API"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class OrderInboxViewSet(viewsets.ModelViewSet):
    """OrderInbox API"""
    queryset = OrderInbox.objects.select_related('customer', 'assigned_to')
    serializer_class = OrderInboxSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'source']
    ordering_fields = ['created_at', 'total_requested']


class NotificationViewSet(viewsets.ModelViewSet):
    """Notification API"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class PublicOrderSubmitView(APIView):
    """Public endpoint pour soumission commande depuis formulaire public"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        data = request.data
        
        # Créer la commande dans l'inbox
        order = OrderInbox.objects.create(
            source='web_form',
            prospect_name=data.get('prospect_name', ''),
            prospect_phone=data.get('prospect_phone', ''),
            prospect_email=data.get('prospect_email', ''),
            prospect_address=data.get('prospect_address', ''),
            prospect_type=data.get('prospect_type', 'B2C'),
            items=data.get('items', []),
            total_requested=data.get('total_requested', 0),
            payment_preference=data.get('payment_preference', ''),
            delivery_address=data.get('delivery_address', ''),
            notes=data.get('notes', ''),
            status=OrderInboxStatus.NEW
        )
        
        # Créer notification pour les admins
        for admin in User.objects.filter(is_staff=True):
            Notification.objects.create(
                user=admin,
                type=NotificationType.ORDER,
                title=f'Nouvelle commande #{order.pk}',
                message=f'{order.prospect_name} - {order.total_requested} FCFA',
                link=f'/crm/inbox/{order.pk}/'
            )
        
        return Response(
            {
                'message': 'Commande reçue avec succès',
                'order_id': order.pk,
                'status': 'new'
            },
            status=status.HTTP_201_CREATED
        )
