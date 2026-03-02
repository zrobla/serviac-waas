"""SERVIAC CRM - Views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum, F
from datetime import timedelta

from .models import Customer, Product, Category, OrderInbox, Notification, OrderInboxStatus
from .forms import CustomerForm, ProductForm


class DashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord CRM principal"""
    template_name = 'crm/dashboard.html'
    
    def get_context_data(self, **kwargs):
        from .models import Order, Invoice, OrderStatus, InvoiceStatus
        
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tableau de bord'
        
        # Stats de base
        context['new_orders_count'] = OrderInbox.objects.filter(status=OrderInboxStatus.NEW).count()
        context['customers_count'] = Customer.objects.filter(is_active=True).count()
        
        # Commandes en cours (non facturées, non annulées)
        context['orders_in_progress'] = Order.objects.filter(
            status__in=[OrderStatus.DRAFT, OrderStatus.CONFIRMED, OrderStatus.PROCESSING, 
                       OrderStatus.READY, OrderStatus.DELIVERED]
        ).count()
        
        # Factures impayées
        context['unpaid_invoices'] = Invoice.objects.filter(
            status__in=[InvoiceStatus.DRAFT, InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]
        ).count()
        
        # Dernières commandes
        context['recent_orders'] = Order.objects.select_related('customer').order_by('-created_at')[:5]
        
        # Notifications
        context['recent_notifications'] = Notification.objects.filter(
            user=self.request.user, is_read=False
        )[:5]
        
        # Stats mensuelles
        today = timezone.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0)
        
        monthly_invoices = Invoice.objects.filter(
            created_at__gte=month_start,
            status__in=[InvoiceStatus.SENT, InvoiceStatus.PAID, InvoiceStatus.PARTIAL]
        )
        context['monthly_revenue'] = monthly_invoices.aggregate(total=Sum('total'))['total'] or 0
        context['monthly_orders'] = Order.objects.filter(created_at__gte=month_start).count()
        
        # Total créances clients
        context['total_receivables'] = Customer.objects.filter(
            is_active=True, balance__gt=0
        ).aggregate(total=Sum('balance'))['total'] or 0
        
        return context


# --- Customers ---
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'crm/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Customer.objects.all()
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(phone__icontains=search))
        return qs


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/customer_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Client créé avec succès')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'crm/customer_detail.html'
    context_object_name = 'customer'


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/customer_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Client modifié avec succès')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


# --- Products ---
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'crm/product_list.html'
    context_object_name = 'products'
    paginate_by = 20


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'crm/product_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Produit créé avec succès')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'crm/product_detail.html'
    context_object_name = 'product'


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'crm/product_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Produit modifié avec succès')
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


# --- Order Inbox ---
class OrderInboxListView(LoginRequiredMixin, ListView):
    model = OrderInbox
    template_name = 'crm/inbox_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        qs = OrderInbox.objects.select_related('customer', 'assigned_to')
        status = self.request.GET.get('status', 'all')
        if status != 'all':
            qs = qs.filter(status=status)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status', 'all')
        context['new_count'] = OrderInbox.objects.filter(status=OrderInboxStatus.NEW).count()
        return context


class OrderInboxDetailView(LoginRequiredMixin, DetailView):
    model = OrderInbox
    template_name = 'crm/inbox_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupérer les produits pour afficher les détails
        if self.object.items:
            product_ids = [item.get('product_id') for item in self.object.items if item.get('product_id')]
            context['products'] = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        return context


class OrderInboxValidateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(OrderInbox, pk=pk)
        order.status = OrderInboxStatus.VALIDATED
        order.processed_at = timezone.now()
        order.processed_by = request.user
        order.save()
        messages.success(request, f'Commande #{pk} validée avec succès')
        return redirect('crm:inbox_list')


class OrderInboxRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(OrderInbox, pk=pk)
        order.status = OrderInboxStatus.REJECTED
        order.rejection_reason = request.POST.get('reason', '')
        order.processed_at = timezone.now()
        order.processed_by = request.user
        order.save()
        messages.warning(request, f'Commande #{pk} rejetée')
        return redirect('crm:inbox_list')


# --- Notifications ---
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'crm/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)


# ============================================================
# PHASE 2: GESTION COMMERCIALE (Orders & Invoices)
# ============================================================

from .models import Order, OrderItem, Invoice, InvoiceItem, OrderStatus, PaymentStatus, InvoiceStatus
from .forms import OrderForm, OrderItemFormSet


class OrderInboxConvertView(LoginRequiredMixin, View):
    """Convertit une demande inbox en commande"""
    def post(self, request, pk):
        inbox = get_object_or_404(OrderInbox, pk=pk)
        
        # Créer ou récupérer le client
        if inbox.customer:
            customer = inbox.customer
        else:
            # Créer un nouveau client depuis le prospect
            customer = Customer.objects.create(
                name=inbox.prospect_name,
                phone=inbox.prospect_phone,
                email=inbox.prospect_email or '',
                address=inbox.prospect_address,
                customer_type=inbox.prospect_type,
                created_by=request.user
            )
            inbox.customer = customer
        
        # Créer la commande
        order = Order.objects.create(
            customer=customer,
            delivery_address=inbox.delivery_address or customer.address,
            source_inbox=inbox,
            customer_notes=inbox.notes,
            created_by=request.user
        )
        
        # Créer les lignes de commande
        for item in inbox.items:
            try:
                product = Product.objects.get(pk=item.get('product_id'))
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.get('quantity', 1),
                    unit_price=item.get('unit_price', product.get_price_for_customer(customer))
                )
            except Product.DoesNotExist:
                continue
        
        # Recalculer les totaux
        order.calculate_totals()
        order.save()
        
        # Mettre à jour l'inbox
        inbox.status = OrderInboxStatus.CONVERTED
        inbox.processed_at = timezone.now()
        inbox.processed_by = request.user
        inbox.save()
        
        messages.success(request, f'Commande {order.number} créée avec succès')
        return redirect('crm:order_detail', pk=order.pk)


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'crm/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Order.objects.select_related('customer')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = OrderStatus.choices
        context['current_status'] = self.request.GET.get('status', '')
        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'crm/order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(is_active=True)
        context['is_new'] = True
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        
        # Traiter les lignes de commande depuis le formulaire
        items_data = self.request.POST.getlist('item_product')
        quantities = self.request.POST.getlist('item_quantity')
        prices = self.request.POST.getlist('item_price')
        
        for i, product_id in enumerate(items_data):
            if product_id:
                try:
                    product = Product.objects.get(pk=product_id)
                    OrderItem.objects.create(
                        order=self.object,
                        product=product,
                        quantity=quantities[i] if i < len(quantities) else 1,
                        unit_price=prices[i] if i < len(prices) else product.price_b2c
                    )
                except (Product.DoesNotExist, ValueError):
                    continue
        
        self.object.calculate_totals()
        self.object.save()
        
        messages.success(self.request, f'Commande {self.object.number} créée')
        return redirect(self.object.get_absolute_url())


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'crm/order_detail.html'
    context_object_name = 'order'


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'crm/order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(is_active=True)
        context['is_new'] = False
        return context


class OrderConfirmView(LoginRequiredMixin, View):
    """Confirme une commande"""
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status == OrderStatus.DRAFT:
            order.status = OrderStatus.CONFIRMED
            order.save()
            
            # Mettre à jour le solde client
            order.customer.balance += order.total
            order.customer.save()
            
            messages.success(request, f'Commande {order.number} confirmée')
        return redirect('crm:order_detail', pk=pk)


class OrderInvoiceView(LoginRequiredMixin, View):
    """Crée une facture depuis une commande"""
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status in [OrderStatus.CONFIRMED, OrderStatus.DELIVERED]:
            invoice = Invoice.create_from_order(order, user=request.user)
            order.status = OrderStatus.INVOICED
            order.save()
            messages.success(request, f'Facture {invoice.number} créée')
            return redirect('crm:invoice_detail', pk=invoice.pk)
        messages.error(request, 'Impossible de facturer cette commande')
        return redirect('crm:order_detail', pk=pk)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'crm/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Invoice.objects.select_related('customer', 'order')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'crm/invoice_detail.html'
    context_object_name = 'invoice'


class InvoicePDFView(LoginRequiredMixin, View):
    """Génère le PDF d'une facture"""
    def get(self, request, pk):
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        
        invoice = get_object_or_404(Invoice, pk=pk)
        
        # Générer HTML
        html = render_to_string('crm/invoice_pdf.html', {
            'invoice': invoice,
            'company': {
                'name': 'SERVIAC GROUP SUARL',
                'address': 'Abidjan, Côte d\'Ivoire',
                'phone': '+225 XX XX XX XX XX',
                'email': 'contact@serviac-group.com',
            }
        })
        
        # Pour l'instant, retourner HTML (WeasyPrint pour PDF réel)
        response = HttpResponse(html, content_type='text/html')
        # response['Content-Disposition'] = f'attachment; filename="facture_{invoice.number}.pdf"'
        return response


# Import models for F expression
from django.db import models
