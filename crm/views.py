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
        return response


class InvoicePaymentView(LoginRequiredMixin, View):
    """Enregistre un paiement sur une facture"""
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        amount = request.POST.get('amount')
        method = request.POST.get('method', 'cash')
        transaction_ref = request.POST.get('transaction_ref', '')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Montant invalide")
                
            # Trouver la caisse ouverte
            cash_register = CashRegister.objects.filter(status=CashRegisterStatus.OPEN).first()
            
            Payment.objects.create(
                customer=invoice.customer,
                invoice=invoice,
                amount=amount,
                payment_method=method,
                transaction_ref=transaction_ref,
                cash_register=cash_register,
                created_by=request.user
            )
            
            if cash_register:
                cash_register.recalculate_totals()
            
            messages.success(request, f'Paiement de {amount} FCFA enregistré')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f'Erreur: {str(e)}')
        
        return redirect('crm:invoice_detail', pk=pk)


# ============================================================
# PHASE 3: GESTION FINANCIÈRE
# ============================================================

from .models import (Payment, PaymentMethod, PaymentType, CustomerLedger, 
                     CustomerCredit, PaymentSchedule, CashRegister, CashRegisterStatus, CashMovement)
from decimal import Decimal, InvalidOperation


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'crm/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 30
    
    def get_queryset(self):
        qs = Payment.objects.select_related('customer', 'invoice')
        method = self.request.GET.get('method')
        if method:
            qs = qs.filter(payment_method=method)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_methods'] = PaymentMethod.choices
        return context


class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Payment
    template_name = 'crm/payment_form.html'
    fields = ['customer', 'invoice', 'amount', 'payment_method', 'transaction_ref', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(is_active=True, balance__gt=0)
        context['invoices'] = Invoice.objects.filter(status__in=[InvoiceStatus.SENT, InvoiceStatus.PARTIAL])
        context['payment_methods'] = PaymentMethod.choices
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Associer à la caisse ouverte
        cash_register = CashRegister.objects.filter(status=CashRegisterStatus.OPEN).first()
        if cash_register:
            form.instance.cash_register = cash_register
        
        response = super().form_valid(form)
        
        if cash_register:
            cash_register.recalculate_totals()
        
        messages.success(self.request, f'Paiement {self.object.reference} enregistré')
        return response
    
    def get_success_url(self):
        return reverse('crm:payment_detail', kwargs={'pk': self.object.pk})


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'crm/payment_detail.html'
    context_object_name = 'payment'


class CustomerLedgerView(LoginRequiredMixin, ListView):
    """Grand livre d'un client"""
    model = CustomerLedger
    template_name = 'crm/customer_ledger.html'
    context_object_name = 'entries'
    paginate_by = 50
    
    def get_queryset(self):
        self.customer = get_object_or_404(Customer, pk=self.kwargs['pk'])
        return CustomerLedger.objects.filter(customer=self.customer)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.customer
        return context


class CashRegisterView(LoginRequiredMixin, TemplateView):
    """Vue principale de la caisse"""
    template_name = 'crm/cash_register.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Caisse ouverte ?
        context['current_register'] = CashRegister.objects.filter(status=CashRegisterStatus.OPEN).first()
        
        if context['current_register']:
            # Récupérer les paiements du jour
            context['today_payments'] = Payment.objects.filter(
                cash_register=context['current_register']
            ).select_related('customer', 'invoice')
            
            # Mouvements de caisse
            context['movements'] = context['current_register'].movements.all()
        
        # Clients avec solde pour encaissement rapide
        context['customers_with_balance'] = Customer.objects.filter(
            is_active=True, balance__gt=0
        ).order_by('-balance')[:10]
        
        context['payment_methods'] = PaymentMethod.choices
        
        return context


class CashRegisterOpenView(LoginRequiredMixin, View):
    """Ouvrir une nouvelle session de caisse"""
    def post(self, request):
        # Vérifier qu'aucune caisse n'est ouverte
        if CashRegister.objects.filter(status=CashRegisterStatus.OPEN).exists():
            messages.error(request, 'Une caisse est déjà ouverte')
            return redirect('crm:cash_register')
        
        opening_balance = request.POST.get('opening_balance', 0)
        try:
            opening_balance = Decimal(opening_balance)
        except:
            opening_balance = Decimal('0')
        
        CashRegister.objects.create(
            opening_balance=opening_balance,
            expected_balance=opening_balance,
            opened_by=request.user
        )
        
        messages.success(request, 'Caisse ouverte avec succès')
        return redirect('crm:cash_register')


class CashRegisterCloseView(LoginRequiredMixin, View):
    """Clôturer la session de caisse"""
    def post(self, request):
        register = CashRegister.objects.filter(status=CashRegisterStatus.OPEN).first()
        if not register:
            messages.error(request, 'Aucune caisse ouverte')
            return redirect('crm:cash_register')
        
        closing_balance = request.POST.get('closing_balance', 0)
        try:
            closing_balance = Decimal(closing_balance)
        except:
            closing_balance = register.expected_balance
        
        register.close(closing_balance, request.user)
        
        diff = register.difference
        if diff and diff != 0:
            if diff > 0:
                messages.warning(request, f'Caisse clôturée avec un excédent de {diff} FCFA')
            else:
                messages.warning(request, f'Caisse clôturée avec un déficit de {abs(diff)} FCFA')
        else:
            messages.success(request, 'Caisse clôturée avec succès')
        
        return redirect('crm:cash_register')


class CashRegisterPaymentView(LoginRequiredMixin, View):
    """Encaisser rapidement depuis la caisse"""
    def post(self, request):
        register = CashRegister.objects.filter(status=CashRegisterStatus.OPEN).first()
        if not register:
            messages.error(request, 'Ouvrez d\'abord la caisse')
            return redirect('crm:cash_register')
        
        customer_id = request.POST.get('customer')
        amount = request.POST.get('amount')
        method = request.POST.get('method', 'cash')
        invoice_id = request.POST.get('invoice')
        transaction_ref = request.POST.get('transaction_ref', '')
        
        try:
            customer = Customer.objects.get(pk=customer_id)
            amount = Decimal(amount)
            invoice = Invoice.objects.get(pk=invoice_id) if invoice_id else None
            
            Payment.objects.create(
                customer=customer,
                invoice=invoice,
                amount=amount,
                payment_method=method,
                transaction_ref=transaction_ref,
                cash_register=register,
                created_by=request.user
            )
            
            register.recalculate_totals()
            messages.success(request, f'Encaissement de {amount} FCFA effectué')
            
        except (Customer.DoesNotExist, ValueError, InvalidOperation) as e:
            messages.error(request, f'Erreur: {str(e)}')
        
        return redirect('crm:cash_register')


class CashMovementView(LoginRequiredMixin, View):
    """Enregistrer un mouvement de caisse (entrée/sortie hors vente)"""
    def post(self, request):
        register = CashRegister.objects.filter(status=CashRegisterStatus.OPEN).first()
        if not register:
            messages.error(request, 'Ouvrez d\'abord la caisse')
            return redirect('crm:cash_register')
        
        movement_type = request.POST.get('movement_type')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason', '')
        
        try:
            amount = Decimal(amount)
            CashMovement.objects.create(
                cash_register=register,
                movement_type=movement_type,
                amount=amount,
                reason=reason,
                created_by=request.user
            )
            
            # Mettre à jour le solde théorique
            if movement_type == 'in':
                register.expected_balance += amount
            else:
                register.expected_balance -= amount
            register.save()
            
            messages.success(request, f'Mouvement enregistré: {amount} FCFA')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f'Erreur: {str(e)}')
        
        return redirect('crm:cash_register')


class CashRegisterHistoryView(LoginRequiredMixin, ListView):
    """Historique des sessions de caisse"""
    model = CashRegister
    template_name = 'crm/cash_register_history.html'
    context_object_name = 'registers'
    paginate_by = 20


class AgedBalanceView(LoginRequiredMixin, TemplateView):
    """Balance âgée des clients"""
    template_name = 'crm/aged_balance.html'
    
    def get_context_data(self, **kwargs):
        from datetime import timedelta
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        
        # Récupérer toutes les factures non payées
        unpaid_invoices = Invoice.objects.filter(
            status__in=[InvoiceStatus.SENT, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]
        ).select_related('customer')
        
        # Calculer les tranches d'âge
        aged_data = []
        totals = {'current': 0, 'days_30': 0, 'days_60': 0, 'days_90': 0, 'over_90': 0, 'total': 0}
        
        customers_balance = {}
        for inv in unpaid_invoices:
            remaining = inv.total - inv.amount_paid
            if remaining <= 0:
                continue
                
            days_old = (today - inv.invoice_date).days
            
            if inv.customer_id not in customers_balance:
                customers_balance[inv.customer_id] = {
                    'customer': inv.customer,
                    'current': Decimal('0'),
                    'days_30': Decimal('0'),
                    'days_60': Decimal('0'),
                    'days_90': Decimal('0'),
                    'over_90': Decimal('0'),
                    'total': Decimal('0')
                }
            
            cb = customers_balance[inv.customer_id]
            cb['total'] += remaining
            totals['total'] += remaining
            
            if days_old <= 30:
                cb['current'] += remaining
                totals['current'] += remaining
            elif days_old <= 60:
                cb['days_30'] += remaining
                totals['days_30'] += remaining
            elif days_old <= 90:
                cb['days_60'] += remaining
                totals['days_60'] += remaining
            elif days_old <= 120:
                cb['days_90'] += remaining
                totals['days_90'] += remaining
            else:
                cb['over_90'] += remaining
                totals['over_90'] += remaining
        
        # Trier par total décroissant
        aged_data = sorted(customers_balance.values(), key=lambda x: x['total'], reverse=True)
        
        context['aged_data'] = aged_data
        context['totals'] = totals
        
        return context


# ============================================================
# PHASE 4: GESTION STOCK INTELLIGENTE
# ============================================================

from .models import (Shipment, ShipmentItem, ShipmentStatus, StockMovement, StockMovementType,
                     CustomerScore, PreOrder, PreOrderStatus, StockReservation,
                     InventoryControl, InventoryLine, InventoryControlStatus)


class StockDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard stock avec vue d'ensemble"""
    template_name = 'crm/stock_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Produits avec stock
        products = Product.objects.filter(is_active=True)
        context['products'] = products
        
        # Alertes stock bas
        context['low_stock'] = products.filter(
            stock_quantity__lte=F('alert_threshold')
        )
        
        # Expéditions en transit
        context['shipments_in_transit'] = Shipment.objects.filter(
            status__in=[ShipmentStatus.SHIPPED, ShipmentStatus.IN_TRANSIT]
        )
        
        # Stock en transit
        transit_items = ShipmentItem.objects.filter(
            shipment__status__in=[ShipmentStatus.SHIPPED, ShipmentStatus.IN_TRANSIT]
        ).values('product__name', 'product__code').annotate(
            total=Sum('quantity')
        )
        context['stock_in_transit'] = transit_items
        
        # Pré-commandes en attente
        context['pending_preorders'] = PreOrder.objects.filter(status=PreOrderStatus.PENDING).count()
        
        # Réservations actives
        context['active_reservations'] = StockReservation.objects.filter(is_active=True).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Totaux
        context['total_stock'] = products.aggregate(total=Sum('stock_quantity'))['total'] or 0
        
        return context


class StockMovementListView(LoginRequiredMixin, ListView):
    """Historique des mouvements de stock"""
    model = StockMovement
    template_name = 'crm/stock_movements.html'
    context_object_name = 'movements'
    paginate_by = 50
    
    def get_queryset(self):
        qs = StockMovement.objects.select_related('product', 'shipment', 'order')
        product = self.request.GET.get('product')
        if product:
            qs = qs.filter(product_id=product)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(is_active=True)
        return context


class ShipmentListView(LoginRequiredMixin, ListView):
    """Liste des expéditions"""
    model = Shipment
    template_name = 'crm/shipment_list.html'
    context_object_name = 'shipments'
    paginate_by = 20
    
    def get_queryset(self):
        qs = Shipment.objects.prefetch_related('items__product')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ShipmentStatus.choices
        return context


class ShipmentCreateView(LoginRequiredMixin, CreateView):
    """Créer une nouvelle expédition"""
    model = Shipment
    template_name = 'crm/shipment_form.html'
    fields = ['departure_date', 'estimated_arrival', 'transporter', 'vehicle_info', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(is_active=True)
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        
        # Traiter les lignes d'expédition
        products = self.request.POST.getlist('item_product')
        quantities = self.request.POST.getlist('item_quantity')
        
        for i, product_id in enumerate(products):
            if product_id and i < len(quantities):
                try:
                    product = Product.objects.get(pk=product_id)
                    qty = Decimal(quantities[i])
                    if qty > 0:
                        ShipmentItem.objects.create(
                            shipment=self.object,
                            product=product,
                            quantity=qty
                        )
                except (Product.DoesNotExist, ValueError):
                    continue
        
        messages.success(self.request, f'Expédition {self.object.reference} créée')
        return redirect('crm:shipment_detail', pk=self.object.pk)


class ShipmentDetailView(LoginRequiredMixin, DetailView):
    model = Shipment
    template_name = 'crm/shipment_detail.html'
    context_object_name = 'shipment'


class ShipmentShipView(LoginRequiredMixin, View):
    """Marquer une expédition comme expédiée"""
    def post(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        if shipment.status == ShipmentStatus.PREPARING:
            shipment.status = ShipmentStatus.SHIPPED
            shipment.departure_date = timezone.now().date()
            shipment.save()
            messages.success(request, f'Expédition {shipment.reference} marquée comme expédiée')
        return redirect('crm:shipment_detail', pk=pk)


class ShipmentReceiveView(LoginRequiredMixin, View):
    """Réceptionner une expédition"""
    def post(self, request, pk):
        shipment = get_object_or_404(Shipment, pk=pk)
        if shipment.status in [ShipmentStatus.SHIPPED, ShipmentStatus.IN_TRANSIT, ShipmentStatus.ARRIVED]:
            shipment.receive(request.user)
            messages.success(request, f'Expédition {shipment.reference} réceptionnée. Stock mis à jour.')
        return redirect('crm:shipment_detail', pk=pk)


class PreOrderListView(LoginRequiredMixin, ListView):
    """Liste des pré-commandes"""
    model = PreOrder
    template_name = 'crm/preorder_list.html'
    context_object_name = 'preorders'
    paginate_by = 20
    
    def get_queryset(self):
        qs = PreOrder.objects.select_related('customer', 'product', 'target_shipment')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(is_active=True)
        return context


class PreOrderCreateView(LoginRequiredMixin, CreateView):
    """Créer une pré-commande"""
    model = PreOrder
    template_name = 'crm/preorder_form.html'
    fields = ['customer', 'product', 'quantity', 'target_shipment', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(is_active=True)
        context['products'] = Product.objects.filter(is_active=True)
        context['shipments'] = Shipment.objects.filter(
            status__in=[ShipmentStatus.PREPARING, ShipmentStatus.SHIPPED, ShipmentStatus.IN_TRANSIT]
        )
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Pré-commande créée')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('crm:preorder_list')


class PreOrderAllocateView(LoginRequiredMixin, View):
    """Allouer du stock aux pré-commandes par priorité"""
    def post(self, request):
        product_id = request.POST.get('product')
        
        if not product_id:
            messages.error(request, 'Sélectionnez un produit')
            return redirect('crm:preorder_list')
        
        product = get_object_or_404(Product, pk=product_id)
        available_stock = product.stock_quantity
        
        # Récupérer les pré-commandes en attente par priorité décroissante
        preorders = PreOrder.objects.filter(
            product=product,
            status=PreOrderStatus.PENDING
        ).order_by('-priority', 'created_at')
        
        allocated_count = 0
        for preorder in preorders:
            remaining = preorder.remaining_quantity
            if remaining > 0 and available_stock >= remaining:
                preorder.quantity_allocated = preorder.quantity
                preorder.status = PreOrderStatus.ALLOCATED
                preorder.save()
                
                # Créer réservation
                StockReservation.objects.create(
                    product=product,
                    customer=preorder.customer,
                    quantity=remaining,
                    reservation_type='preorder',
                    preorder=preorder,
                    created_by=request.user
                )
                
                available_stock -= remaining
                allocated_count += 1
            elif remaining > 0 and available_stock > 0:
                # Allocation partielle
                preorder.quantity_allocated += available_stock
                preorder.save()
                
                StockReservation.objects.create(
                    product=product,
                    customer=preorder.customer,
                    quantity=available_stock,
                    reservation_type='preorder',
                    preorder=preorder,
                    created_by=request.user
                )
                available_stock = 0
                break
        
        messages.success(request, f'{allocated_count} pré-commande(s) allouée(s)')
        return redirect('crm:preorder_list')


class InventoryListView(LoginRequiredMixin, ListView):
    """Liste des contrôles d'inventaire"""
    model = InventoryControl
    template_name = 'crm/inventory_list.html'
    context_object_name = 'inventories'
    paginate_by = 20


class InventoryCreateView(LoginRequiredMixin, View):
    """Créer un nouveau contrôle d'inventaire"""
    def get(self, request):
        return render(request, 'crm/inventory_form.html', {
            'products': Product.objects.filter(is_active=True)
        })
    
    def post(self, request):
        name = request.POST.get('name', 'Inventaire')
        control_date = request.POST.get('control_date', timezone.now().date())
        
        inventory = InventoryControl.objects.create(
            name=name,
            control_date=control_date,
            created_by=request.user
        )
        
        # Créer les lignes pour tous les produits actifs
        for product in Product.objects.filter(is_active=True):
            InventoryLine.objects.create(
                inventory=inventory,
                product=product,
                theoretical_quantity=product.stock_quantity
            )
        
        messages.success(request, f'Inventaire {inventory.reference} créé')
        return redirect('crm:inventory_detail', pk=inventory.pk)


class InventoryDetailView(LoginRequiredMixin, DetailView):
    model = InventoryControl
    template_name = 'crm/inventory_detail.html'
    context_object_name = 'inventory'
    
    def post(self, request, pk):
        """Mettre à jour les quantités physiques"""
        inventory = self.get_object()
        
        if inventory.status != InventoryControlStatus.DRAFT:
            messages.error(request, 'Cet inventaire ne peut plus être modifié')
            return redirect('crm:inventory_detail', pk=pk)
        
        # Mettre à jour les quantités physiques
        for line in inventory.lines.all():
            qty = request.POST.get(f'qty_{line.pk}')
            if qty:
                try:
                    line.physical_quantity = Decimal(qty)
                    line.save()
                except (ValueError, InvalidOperation):
                    pass
        
        inventory.status = InventoryControlStatus.IN_PROGRESS
        inventory.save()
        
        messages.success(request, 'Quantités enregistrées')
        return redirect('crm:inventory_detail', pk=pk)


class InventoryValidateView(LoginRequiredMixin, View):
    """Valider un inventaire et appliquer les ajustements"""
    def post(self, request, pk):
        inventory = get_object_or_404(InventoryControl, pk=pk)
        
        if inventory.status not in [InventoryControlStatus.DRAFT, InventoryControlStatus.IN_PROGRESS]:
            messages.error(request, 'Cet inventaire ne peut pas être validé')
            return redirect('crm:inventory_detail', pk=pk)
        
        inventory.validate(request.user)
        messages.success(request, f'Inventaire {inventory.reference} validé. Stock ajusté.')
        return redirect('crm:inventory_detail', pk=pk)


# Import models for F expression
from django.db import models
from django.urls import reverse
