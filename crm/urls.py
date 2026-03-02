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
    path('clients/<int:pk>/grand-livre/', views.CustomerLedgerView.as_view(), name='customer_ledger'),
    
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
    path('factures/<int:pk>/paiement/', views.InvoicePaymentView.as_view(), name='invoice_payment'),
    
    # Payments (Phase 3)
    path('paiements/', views.PaymentListView.as_view(), name='payment_list'),
    path('paiements/nouveau/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('paiements/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    
    # Cash Register (Phase 3)
    path('caisse/', views.CashRegisterView.as_view(), name='cash_register'),
    path('caisse/ouvrir/', views.CashRegisterOpenView.as_view(), name='cash_register_open'),
    path('caisse/cloturer/', views.CashRegisterCloseView.as_view(), name='cash_register_close'),
    path('caisse/encaisser/', views.CashRegisterPaymentView.as_view(), name='cash_register_payment'),
    path('caisse/mouvement/', views.CashMovementView.as_view(), name='cash_movement'),
    path('caisse/historique/', views.CashRegisterHistoryView.as_view(), name='cash_register_history'),
    
    # Balance âgée
    path('balance-agee/', views.AgedBalanceView.as_view(), name='aged_balance'),
    
    # Stock (Phase 4)
    path('stock/', views.StockDashboardView.as_view(), name='stock_dashboard'),
    path('stock/mouvements/', views.StockMovementListView.as_view(), name='stock_movements'),
    
    # Shipments (Phase 4)
    path('expeditions/', views.ShipmentListView.as_view(), name='shipment_list'),
    path('expeditions/nouvelle/', views.ShipmentCreateView.as_view(), name='shipment_create'),
    path('expeditions/<int:pk>/', views.ShipmentDetailView.as_view(), name='shipment_detail'),
    path('expeditions/<int:pk>/expedier/', views.ShipmentShipView.as_view(), name='shipment_ship'),
    path('expeditions/<int:pk>/receptionner/', views.ShipmentReceiveView.as_view(), name='shipment_receive'),
    
    # Pre-orders (Phase 4)
    path('precommandes/', views.PreOrderListView.as_view(), name='preorder_list'),
    path('precommandes/nouvelle/', views.PreOrderCreateView.as_view(), name='preorder_create'),
    path('precommandes/allouer/', views.PreOrderAllocateView.as_view(), name='preorder_allocate'),
    
    # Inventory (Phase 4)
    path('inventaires/', views.InventoryListView.as_view(), name='inventory_list'),
    path('inventaires/nouveau/', views.InventoryCreateView.as_view(), name='inventory_create'),
    path('inventaires/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory_detail'),
    path('inventaires/<int:pk>/valider/', views.InventoryValidateView.as_view(), name='inventory_validate'),
    
    # Bons de livraison (Phase 5)
    path('livraisons/', views.DeliveryNoteListView.as_view(), name='delivery_list'),
    path('livraisons/nouveau/', views.DeliveryNoteCreateView.as_view(), name='delivery_create'),
    path('livraisons/<int:pk>/', views.DeliveryNoteDetailView.as_view(), name='delivery_detail'),
    path('livraisons/<int:pk>/pret/', views.DeliveryNoteReadyView.as_view(), name='delivery_ready'),
    path('livraisons/<int:pk>/partir/', views.DeliveryNoteStartView.as_view(), name='delivery_start'),
    path('livraisons/<int:pk>/livrer/', views.DeliveryNoteDeliverView.as_view(), name='delivery_deliver'),
    path('livraisons/<int:pk>/pdf/', views.DeliveryNotePDFView.as_view(), name='delivery_pdf'),
    
    # Emailing (Phase 6)
    path('emails/templates/', views.EmailTemplateListView.as_view(), name='email_templates'),
    path('emails/templates/<int:pk>/', views.EmailTemplateDetailView.as_view(), name='email_template_detail'),
    path('emails/templates/<int:pk>/preview/', views.EmailPreviewView.as_view(), name='email_preview'),
    path('emails/historique/', views.EmailLogListView.as_view(), name='email_logs'),
    path('emails/composer/', views.EmailComposeView.as_view(), name='email_compose'),
    path('emails/automatisations/', views.AutomationRuleListView.as_view(), name='automation_list'),
    path('emails/automatisations/<int:pk>/toggle/', views.AutomationRuleToggleView.as_view(), name='automation_toggle'),
    
    # Gouvernance (Phase 7)
    path('kpis/', views.KPIDashboardView.as_view(), name='kpi_dashboard'),
    path('rapports/', views.ReportView.as_view(), name='reports'),
    path('audit/', views.AuditLogListView.as_view(), name='audit_log'),
    path('approbations/', views.ApprovalListView.as_view(), name='approval_list'),
    path('approbations/<int:pk>/action/', views.ApprovalActionView.as_view(), name='approval_action'),
    path('utilisateurs/', views.UserProfileListView.as_view(), name='user_list'),
    path('utilisateurs/<int:pk>/role/', views.UserRoleUpdateView.as_view(), name='user_role_update'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/marquer-lues/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Phase 8: Optimisation UX
    path('recherche/', views.GlobalSearchView.as_view(), name='global_search'),
    path('clients/<int:customer_pk>/commande-rapide/', views.QuickOrderCreateView.as_view(), name='quick_order'),
    path('factures/<int:invoice_pk>/encaissement-rapide/', views.QuickPaymentView.as_view(), name='quick_payment'),
    path('clients/<int:pk>/statistiques/', views.CustomerStatsView.as_view(), name='customer_stats'),
]
