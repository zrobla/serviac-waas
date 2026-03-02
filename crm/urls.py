"""SERVIAC CRM - URL Configuration"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'crm'

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='crm/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Customers
    path('clients/', views.CustomerListView.as_view(), name='customer_list'),
    path('clients/nouveau/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('clients/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('clients/<int:pk>/modifier/', views.CustomerUpdateView.as_view(), name='customer_update'),
    
    # Products
    path('produits/', views.ProductListView.as_view(), name='product_list'),
    path('produits/nouveau/', views.ProductCreateView.as_view(), name='product_create'),
    path('produits/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('produits/<int:pk>/modifier/', views.ProductUpdateView.as_view(), name='product_update'),
    
    # Order Inbox
    path('inbox/', views.OrderInboxListView.as_view(), name='inbox_list'),
    path('inbox/<int:pk>/', views.OrderInboxDetailView.as_view(), name='inbox_detail'),
    path('inbox/<int:pk>/valider/', views.OrderInboxValidateView.as_view(), name='inbox_validate'),
    path('inbox/<int:pk>/rejeter/', views.OrderInboxRejectView.as_view(), name='inbox_reject'),
    path('inbox/<int:pk>/convertir/', views.OrderInboxConvertView.as_view(), name='inbox_convert'),
    
    # Orders (Phase 2)
    path('commandes/', views.OrderListView.as_view(), name='order_list'),
    path('commandes/nouvelle/', views.OrderCreateView.as_view(), name='order_create'),
    path('commandes/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('commandes/<int:pk>/modifier/', views.OrderUpdateView.as_view(), name='order_update'),
    path('commandes/<int:pk>/confirmer/', views.OrderConfirmView.as_view(), name='order_confirm'),
    path('commandes/<int:pk>/facturer/', views.OrderInvoiceView.as_view(), name='order_invoice'),
    
    # Invoices (Phase 2)
    path('factures/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('factures/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('factures/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/marquer-lues/', views.mark_notifications_read, name='mark_notifications_read'),
]
