"""SERVIAC CRM - API URL Configuration"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'order-inbox', views.OrderInboxViewSet, basename='order-inbox')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/public/order/', views.PublicOrderSubmitView.as_view(), name='public_order_submit'),
]
