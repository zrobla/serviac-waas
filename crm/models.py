"""
SERVIAC GROUP - CRM Models
Modèles de données pour la gestion commerciale
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class CustomerType(models.TextChoices):
    B2B = 'B2B', 'Professionnel (B2B)'
    B2C = 'B2C', 'Particulier (B2C)'


class Category(models.Model):
    """Catégorie de produits"""
    name = models.CharField('Nom', max_length=100)
    description = models.TextField('Description', blank=True)
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:category_detail', kwargs={'pk': self.pk})


class ProductUnit(models.TextChoices):
    KG = 'kg', 'Kilogramme'
    SAC_50 = 'sac_50kg', 'Sac de 50 kg'
    TONNE = 'tonne', 'Tonne'
    UNITE = 'unite', 'Unité'


class Product(models.Model):
    """Produit SERVIAC"""
    name = models.CharField('Nom', max_length=200)
    code = models.CharField('Code produit', max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Catégorie')
    description = models.TextField('Description', blank=True)
    unit = models.CharField('Unité', max_length=20, choices=ProductUnit.choices, default=ProductUnit.SAC_50)
    
    price_b2b = models.DecimalField('Prix B2B', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    price_b2c = models.DecimalField('Prix B2C', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    
    stock_quantity = models.DecimalField('Quantité en stock', max_digits=12, decimal_places=2, default=0)
    alert_threshold = models.DecimalField('Seuil d\'alerte', max_digits=12, decimal_places=2, default=10)
    
    is_active = models.BooleanField('Actif', default=True)
    image = models.ImageField('Image', upload_to='products/', blank=True, null=True)
    
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:product_detail', kwargs={'pk': self.pk})
    
    def get_price_for_customer(self, customer):
        """Retourne le prix selon le type de client"""
        if customer and customer.customer_type == CustomerType.B2B:
            return self.price_b2b
        return self.price_b2c
    
    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.alert_threshold


class Customer(models.Model):
    """Client SERVIAC - B2B ou B2C"""
    # Informations de base
    name = models.CharField('Nom / Raison sociale', max_length=200)
    customer_type = models.CharField('Type', max_length=3, choices=CustomerType.choices, default=CustomerType.B2C)
    
    # Contact
    phone = models.CharField('Téléphone', max_length=20)
    phone_secondary = models.CharField('Téléphone secondaire', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    address = models.TextField('Adresse', blank=True)
    city = models.CharField('Ville', max_length=100, default='Abidjan')
    
    # Informations B2B
    company_registration = models.CharField('N° RCCM', max_length=50, blank=True)
    tax_id = models.CharField('N° Contribuable', max_length=50, blank=True)
    
    # Gestion financière
    credit_limit = models.DecimalField('Plafond de crédit (FCFA)', max_digits=14, decimal_places=2, default=0,
                                       help_text='Montant maximum autorisé en crédit')
    payment_terms = models.PositiveIntegerField('Délai de paiement (jours)', default=0,
                                                help_text='0 = paiement comptant')
    balance = models.DecimalField('Solde actuel (FCFA)', max_digits=14, decimal_places=2, default=0,
                                  help_text='Positif = dette du client, Négatif = avoir')
    is_blocked = models.BooleanField('Compte bloqué', default=False,
                                     help_text='Si coché, aucune nouvelle commande acceptée')
    
    # Scoring
    manual_score = models.PositiveIntegerField('Note manuelle (1-10)', default=5,
                                               help_text='Note attribuée par le gestionnaire')
    
    # Métadonnées
    notes = models.TextField('Notes internes', blank=True)
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers_created')
    
    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_customer_type_display()})"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:customer_detail', kwargs={'pk': self.pk})
    
    @property
    def can_order(self):
        """Vérifie si le client peut passer commande"""
        if self.is_blocked:
            return False
        if self.credit_limit > 0 and self.balance >= self.credit_limit:
            return False
        return True
    
    @property
    def available_credit(self):
        """Crédit disponible"""
        if self.credit_limit <= 0:
            return Decimal('0')
        return max(Decimal('0'), self.credit_limit - self.balance)


class OrderInboxStatus(models.TextChoices):
    NEW = 'new', 'Nouvelle'
    PROCESSING = 'processing', 'En traitement'
    VALIDATED = 'validated', 'Validée'
    REJECTED = 'rejected', 'Rejetée'
    CONVERTED = 'converted', 'Convertie en commande'


class OrderInboxSource(models.TextChoices):
    WEB_FORM = 'web_form', 'Formulaire web'
    PHONE = 'phone', 'Téléphone'
    WHATSAPP = 'whatsapp', 'WhatsApp'
    DIRECT = 'direct', 'Direct (magasin)'


class OrderInbox(models.Model):
    """Inbox des commandes entrantes"""
    # Source
    source = models.CharField('Source', max_length=20, choices=OrderInboxSource.choices, default=OrderInboxSource.WEB_FORM)
    
    # Client existant ou prospect
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='order_requests', verbose_name='Client existant')
    
    # Informations prospect (si nouveau client)
    prospect_name = models.CharField('Nom prospect', max_length=200, blank=True)
    prospect_phone = models.CharField('Téléphone prospect', max_length=20, blank=True)
    prospect_email = models.EmailField('Email prospect', blank=True)
    prospect_address = models.TextField('Adresse prospect', blank=True)
    prospect_type = models.CharField('Type prospect', max_length=3, choices=CustomerType.choices, default=CustomerType.B2C)
    
    # Commande
    items = models.JSONField('Articles commandés', default=list,
                             help_text='[{"product_id": 1, "quantity": 10, "unit_price": 5000}]')
    total_requested = models.DecimalField('Total demandé (FCFA)', max_digits=14, decimal_places=2, default=0)
    
    # Préférences
    payment_preference = models.CharField('Préférence paiement', max_length=50, blank=True)
    delivery_address = models.TextField('Adresse de livraison', blank=True)
    notes = models.TextField('Notes / Message', blank=True)
    
    # Workflow
    status = models.CharField('Statut', max_length=20, choices=OrderInboxStatus.choices, default=OrderInboxStatus.NEW)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_order_requests', verbose_name='Assigné à')
    rejection_reason = models.TextField('Motif de rejet', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Reçu le', auto_now_add=True)
    processed_at = models.DateTimeField('Traité le', null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='processed_order_requests')
    
    class Meta:
        verbose_name = 'Demande de commande'
        verbose_name_plural = 'Inbox commandes'
        ordering = ['-created_at']
    
    def __str__(self):
        client = self.customer.name if self.customer else self.prospect_name
        return f"#{self.pk} - {client} - {self.get_status_display()}"
    
    @property
    def client_name(self):
        return self.customer.name if self.customer else self.prospect_name
    
    @property
    def client_phone(self):
        return self.customer.phone if self.customer else self.prospect_phone


class NotificationType(models.TextChoices):
    ORDER = 'order', 'Commande'
    PAYMENT = 'payment', 'Paiement'
    STOCK = 'stock', 'Stock'
    ALERT = 'alert', 'Alerte'
    INFO = 'info', 'Information'


class Notification(models.Model):
    """Notifications internes CRM"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='Destinataire')
    type = models.CharField('Type', max_length=20, choices=NotificationType.choices, default=NotificationType.INFO)
    title = models.CharField('Titre', max_length=200)
    message = models.TextField('Message')
    link = models.CharField('Lien', max_length=500, blank=True, help_text='URL vers l\'objet concerné')
    is_read = models.BooleanField('Lu', default=False)
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


# ============================================================
# PHASE 2: GESTION COMMERCIALE
# ============================================================

class OrderStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    CONFIRMED = 'confirmed', 'Confirmée'
    PROCESSING = 'processing', 'En préparation'
    READY = 'ready', 'Prête'
    DELIVERED = 'delivered', 'Livrée'
    INVOICED = 'invoiced', 'Facturée'
    CANCELLED = 'cancelled', 'Annulée'


class PaymentStatus(models.TextChoices):
    UNPAID = 'unpaid', 'Non payée'
    PARTIAL = 'partial', 'Partiellement payée'
    PAID = 'paid', 'Payée'


class Order(models.Model):
    """Commande client SERVIAC"""
    # Numérotation
    number = models.CharField('N° Commande', max_length=20, unique=True, editable=False)
    
    # Client
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders', verbose_name='Client')
    
    # Dates
    order_date = models.DateField('Date commande', auto_now_add=True)
    delivery_date = models.DateField('Date livraison souhaitée', null=True, blank=True)
    
    # Adresse livraison
    delivery_address = models.TextField('Adresse de livraison', blank=True)
    
    # Montants
    subtotal = models.DecimalField('Sous-total HT', max_digits=14, decimal_places=2, default=0)
    discount_percent = models.DecimalField('Remise (%)', max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField('Remise (FCFA)', max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField('TVA', max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField('Total TTC', max_digits=14, decimal_places=2, default=0)
    
    # Paiement
    amount_paid = models.DecimalField('Montant payé', max_digits=14, decimal_places=2, default=0)
    payment_status = models.CharField('Statut paiement', max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    
    # Workflow
    status = models.CharField('Statut', max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    
    # Origine
    source_inbox = models.ForeignKey(OrderInbox, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='converted_orders', verbose_name='Demande origine')
    
    # Notes
    notes = models.TextField('Notes internes', blank=True)
    customer_notes = models.TextField('Notes client', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders_created')
    
    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.number} - {self.customer.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:order_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_number(cls):
        from django.utils import timezone
        today = timezone.now()
        prefix = f"CMD-{today.strftime('%Y%m')}"
        last = cls.objects.filter(number__startswith=prefix).order_by('-number').first()
        if last:
            last_num = int(last.number.split('-')[-1])
            return f"{prefix}-{last_num + 1:04d}"
        return f"{prefix}-0001"
    
    def calculate_totals(self):
        """Recalcule les totaux depuis les lignes"""
        self.subtotal = sum(item.line_total for item in self.items.all())
        if self.discount_percent > 0:
            self.discount_amount = self.subtotal * self.discount_percent / 100
        self.total = self.subtotal - self.discount_amount + self.tax_amount
        self.update_payment_status()
    
    def update_payment_status(self):
        """Met à jour le statut de paiement"""
        if self.amount_paid >= self.total:
            self.payment_status = PaymentStatus.PAID
        elif self.amount_paid > 0:
            self.payment_status = PaymentStatus.PARTIAL
        else:
            self.payment_status = PaymentStatus.UNPAID
    
    @property
    def balance_due(self):
        """Reste à payer"""
        return max(Decimal('0'), self.total - self.amount_paid)


class OrderItem(models.Model):
    """Ligne de commande"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Commande')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Produit')
    
    quantity = models.DecimalField('Quantité', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField('Prix unitaire', max_digits=12, decimal_places=2)
    discount_percent = models.DecimalField('Remise ligne (%)', max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField('Total ligne', max_digits=14, decimal_places=2, default=0)
    
    notes = models.CharField('Notes', max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calcul automatique du total ligne
        subtotal = self.quantity * self.unit_price
        if self.discount_percent > 0:
            subtotal = subtotal * (1 - self.discount_percent / 100)
        self.line_total = subtotal
        super().save(*args, **kwargs)


class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    SENT = 'sent', 'Envoyée'
    PAID = 'paid', 'Payée'
    PARTIAL = 'partial', 'Partiellement payée'
    OVERDUE = 'overdue', 'En retard'
    CANCELLED = 'cancelled', 'Annulée'


class Invoice(models.Model):
    """Facture SERVIAC"""
    # Numérotation
    number = models.CharField('N° Facture', max_length=20, unique=True, editable=False)
    
    # Liens
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices', verbose_name='Client')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='invoices', verbose_name='Commande')
    
    # Dates
    invoice_date = models.DateField('Date facture', auto_now_add=True)
    due_date = models.DateField('Date échéance')
    
    # Montants
    subtotal = models.DecimalField('Sous-total HT', max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField('Remise', max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField('TVA', max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField('Total TTC', max_digits=14, decimal_places=2, default=0)
    
    # Paiement
    amount_paid = models.DecimalField('Montant payé', max_digits=14, decimal_places=2, default=0)
    
    # Statut
    status = models.CharField('Statut', max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    
    # Notes
    notes = models.TextField('Notes', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    
    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.number} - {self.customer.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crm:invoice_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        if not self.due_date:
            from django.utils import timezone
            from datetime import timedelta
            days = self.customer.payment_terms if self.customer.payment_terms > 0 else 30
            self.due_date = timezone.now().date() + timedelta(days=days)
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_number(cls):
        from django.utils import timezone
        today = timezone.now()
        prefix = f"FAC-{today.strftime('%Y%m')}"
        last = cls.objects.filter(number__startswith=prefix).order_by('-number').first()
        if last:
            last_num = int(last.number.split('-')[-1])
            return f"{prefix}-{last_num + 1:04d}"
        return f"{prefix}-0001"
    
    @property
    def balance_due(self):
        return max(Decimal('0'), self.total - self.amount_paid)
    
    @property
    def amount_due(self):
        """Alias pour balance_due, utilisé dans les templates"""
        return self.balance_due
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
    
    @classmethod
    def create_from_order(cls, order, user=None):
        """Crée une facture depuis une commande"""
        invoice = cls.objects.create(
            customer=order.customer,
            order=order,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            total=order.total,
            notes=order.notes,
            created_by=user
        )
        # Copier les lignes
        for item in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=item.product,
                description=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total
            )
        return invoice


class InvoiceItem(models.Model):
    """Ligne de facture"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='Facture')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Produit')
    
    description = models.CharField('Description', max_length=255)
    quantity = models.DecimalField('Quantité', max_digits=12, decimal_places=2)
    unit_price = models.DecimalField('Prix unitaire', max_digits=12, decimal_places=2)
    line_total = models.DecimalField('Total ligne', max_digits=14, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de facture'
    
    def __str__(self):
        return f"{self.quantity} x {self.description}"


# ============================================================
# PHASE 3: GESTION FINANCIÈRE
# ============================================================

class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Espèces'
    ORANGE_MONEY = 'orange_money', 'Orange Money'
    MTN_MONEY = 'mtn_money', 'MTN Money'
    MOOV_MONEY = 'moov_money', 'Moov Money'
    WAVE = 'wave', 'Wave'
    BANK_TRANSFER = 'bank_transfer', 'Virement bancaire'
    CHECK = 'check', 'Chèque'
    CREDIT = 'credit', 'Crédit client'


class PaymentType(models.TextChoices):
    PAYMENT = 'payment', 'Encaissement'
    REFUND = 'refund', 'Remboursement'
    CREDIT_NOTE = 'credit_note', 'Avoir'
    ADJUSTMENT = 'adjustment', 'Ajustement'


class Payment(models.Model):
    """Paiement/Encaissement SERVIAC"""
    # Référence
    reference = models.CharField('Référence', max_length=30, unique=True, editable=False)
    
    # Liens
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='payments', verbose_name='Client')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='payments', verbose_name='Facture')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='payments', verbose_name='Commande')
    
    # Type et méthode
    payment_type = models.CharField('Type', max_length=20, choices=PaymentType.choices, default=PaymentType.PAYMENT)
    payment_method = models.CharField('Méthode', max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    
    # Montants
    amount = models.DecimalField('Montant', max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Infos complémentaires
    payment_date = models.DateField('Date paiement')
    transaction_ref = models.CharField('Réf. transaction', max_length=100, blank=True, 
                                       help_text='Numéro de transaction mobile money, chèque, etc.')
    notes = models.TextField('Notes', blank=True)
    
    # Caisse
    cash_register = models.ForeignKey('CashRegister', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='payments', verbose_name='Caisse')
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payments_created')
    
    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"{self.reference} - {self.customer.name} - {self.amount} FCFA"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        if not self.payment_date:
            self.payment_date = timezone.now().date()
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Mettre à jour le solde client et la facture
        if is_new:
            self.apply_to_balance()
            if self.invoice:
                self.apply_to_invoice()
    
    @classmethod
    def generate_reference(cls):
        today = timezone.now()
        prefix = f"PAY-{today.strftime('%Y%m%d')}"
        last = cls.objects.filter(reference__startswith=prefix).order_by('-reference').first()
        if last:
            last_num = int(last.reference.split('-')[-1])
            return f"{prefix}-{last_num + 1:04d}"
        return f"{prefix}-0001"
    
    def apply_to_balance(self):
        """Applique le paiement au solde client"""
        if self.payment_type == PaymentType.PAYMENT:
            self.customer.balance -= self.amount
        elif self.payment_type in [PaymentType.REFUND, PaymentType.CREDIT_NOTE]:
            self.customer.balance += self.amount
        self.customer.save()
        
        # Créer l'écriture dans le grand livre
        CustomerLedger.objects.create(
            customer=self.customer,
            payment=self,
            transaction_type='credit' if self.payment_type == PaymentType.PAYMENT else 'debit',
            amount=self.amount,
            balance_after=self.customer.balance,
            description=f"Paiement {self.reference}"
        )
    
    def apply_to_invoice(self):
        """Applique le paiement à la facture"""
        if self.payment_type == PaymentType.PAYMENT:
            self.invoice.amount_paid += self.amount
            if self.invoice.amount_paid >= self.invoice.total:
                self.invoice.status = InvoiceStatus.PAID
            elif self.invoice.amount_paid > 0:
                self.invoice.status = InvoiceStatus.PARTIAL
            self.invoice.save()


class CustomerLedger(models.Model):
    """Grand livre client - historique des mouvements"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='ledger_entries', verbose_name='Client')
    
    # Liens optionnels
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    
    # Transaction
    transaction_type = models.CharField('Type', max_length=10, choices=[
        ('debit', 'Débit (dette)'),
        ('credit', 'Crédit (paiement)')
    ])
    amount = models.DecimalField('Montant', max_digits=14, decimal_places=2)
    balance_after = models.DecimalField('Solde après', max_digits=14, decimal_places=2)
    
    description = models.CharField('Description', max_length=255)
    created_at = models.DateTimeField('Date', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Écriture client'
        verbose_name_plural = 'Grand livre client'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.transaction_type} - {self.amount}"


class CustomerCredit(models.Model):
    """Avoirs clients - crédits à utiliser"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='credits', verbose_name='Client')
    
    # Montants
    original_amount = models.DecimalField('Montant initial', max_digits=14, decimal_places=2)
    remaining_amount = models.DecimalField('Montant restant', max_digits=14, decimal_places=2)
    
    # Origine
    reason = models.CharField('Motif', max_length=255)
    source_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='credit_notes', verbose_name='Facture origine')
    
    # Validité
    expiry_date = models.DateField('Date expiration', null=True, blank=True)
    is_active = models.BooleanField('Actif', default=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Avoir client'
        verbose_name_plural = 'Avoirs clients'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Avoir {self.customer.name} - {self.remaining_amount} FCFA"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    @property
    def is_usable(self):
        return self.is_active and self.remaining_amount > 0 and not self.is_expired


class PaymentSchedule(models.Model):
    """Échéancier de paiement"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payment_schedules')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payment_schedules')
    
    # Échéance
    due_date = models.DateField('Date échéance')
    amount = models.DecimalField('Montant', max_digits=14, decimal_places=2)
    
    # Statut
    is_paid = models.BooleanField('Payé', default=False)
    paid_date = models.DateField('Date paiement', null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Rappels
    reminder_sent = models.BooleanField('Rappel envoyé', default=False)
    reminder_date = models.DateField('Date rappel', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Échéance'
        verbose_name_plural = 'Échéancier'
        ordering = ['due_date']
    
    def __str__(self):
        status = "✓" if self.is_paid else "○"
        return f"{status} {self.due_date} - {self.amount} FCFA"
    
    @property
    def is_overdue(self):
        return not self.is_paid and self.due_date < timezone.now().date()
    
    @property
    def days_until_due(self):
        if self.is_paid:
            return None
        return (self.due_date - timezone.now().date()).days


class CashRegisterStatus(models.TextChoices):
    OPEN = 'open', 'Ouverte'
    CLOSED = 'closed', 'Clôturée'


class CashRegister(models.Model):
    """Session de caisse"""
    # Identification
    name = models.CharField('Nom caisse', max_length=50, default='Caisse principale')
    session_date = models.DateField('Date session')
    
    # Soldes
    opening_balance = models.DecimalField('Solde ouverture', max_digits=14, decimal_places=2, default=0)
    closing_balance = models.DecimalField('Solde clôture', max_digits=14, decimal_places=2, null=True, blank=True)
    expected_balance = models.DecimalField('Solde théorique', max_digits=14, decimal_places=2, default=0)
    
    # Totaux par méthode
    total_cash = models.DecimalField('Total espèces', max_digits=14, decimal_places=2, default=0)
    total_mobile_money = models.DecimalField('Total Mobile Money', max_digits=14, decimal_places=2, default=0)
    total_bank = models.DecimalField('Total virement/chèque', max_digits=14, decimal_places=2, default=0)
    
    # Statut
    status = models.CharField('Statut', max_length=10, choices=CashRegisterStatus.choices, default=CashRegisterStatus.OPEN)
    
    # Gestion
    opened_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cash_registers_opened')
    opened_at = models.DateTimeField('Ouvert le', auto_now_add=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cash_registers_closed')
    closed_at = models.DateTimeField('Clôturé le', null=True, blank=True)
    
    notes = models.TextField('Notes', blank=True)
    
    class Meta:
        verbose_name = 'Session de caisse'
        verbose_name_plural = 'Sessions de caisse'
        ordering = ['-session_date', '-opened_at']
    
    def __str__(self):
        return f"{self.name} - {self.session_date} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.session_date:
            self.session_date = timezone.now().date()
        super().save(*args, **kwargs)
    
    @property
    def difference(self):
        """Écart entre solde réel et théorique"""
        if self.closing_balance is not None:
            return self.closing_balance - self.expected_balance
        return None
    
    @property
    def total_receipts(self):
        """Total des encaissements de la session"""
        return self.total_cash + self.total_mobile_money + self.total_bank
    
    def recalculate_totals(self):
        """Recalcule les totaux depuis les paiements"""
        from django.db.models import Sum
        payments = self.payments.filter(payment_type=PaymentType.PAYMENT)
        
        self.total_cash = payments.filter(payment_method=PaymentMethod.CASH).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        mobile_methods = [PaymentMethod.ORANGE_MONEY, PaymentMethod.MTN_MONEY, 
                         PaymentMethod.MOOV_MONEY, PaymentMethod.WAVE]
        self.total_mobile_money = payments.filter(payment_method__in=mobile_methods).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        bank_methods = [PaymentMethod.BANK_TRANSFER, PaymentMethod.CHECK]
        self.total_bank = payments.filter(payment_method__in=bank_methods).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')
        
        self.expected_balance = self.opening_balance + self.total_cash
        self.save()
    
    def close(self, closing_balance, user):
        """Clôture la caisse"""
        self.closing_balance = closing_balance
        self.status = CashRegisterStatus.CLOSED
        self.closed_by = user
        self.closed_at = timezone.now()
        self.save()


class CashMovement(models.Model):
    """Mouvements de caisse hors ventes"""
    cash_register = models.ForeignKey(CashRegister, on_delete=models.CASCADE, related_name='movements')
    
    movement_type = models.CharField('Type', max_length=10, choices=[
        ('in', 'Entrée'),
        ('out', 'Sortie')
    ])
    amount = models.DecimalField('Montant', max_digits=14, decimal_places=2)
    reason = models.CharField('Motif', max_length=255)
    
    created_at = models.DateTimeField('Date', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Mouvement de caisse'
        verbose_name_plural = 'Mouvements de caisse'
        ordering = ['-created_at']
    
    def __str__(self):
        sign = '+' if self.movement_type == 'in' else '-'
        return f"{sign}{self.amount} FCFA - {self.reason}"


# ============================================================
# PHASE 4: GESTION STOCK INTELLIGENTE
# ============================================================

class ShipmentStatus(models.TextChoices):
    PREPARING = 'preparing', 'En préparation'
    SHIPPED = 'shipped', 'Expédié'
    IN_TRANSIT = 'in_transit', 'En transit'
    ARRIVED = 'arrived', 'Arrivé'
    RECEIVED = 'received', 'Réceptionné'
    CANCELLED = 'cancelled', 'Annulé'


class Shipment(models.Model):
    """Expédition de marchandises (Sénégal → Côte d'Ivoire)"""
    # Identification
    reference = models.CharField('Référence', max_length=30, unique=True, editable=False)
    
    # Dates
    departure_date = models.DateField('Date départ', null=True, blank=True)
    estimated_arrival = models.DateField('Arrivée estimée', null=True, blank=True)
    actual_arrival = models.DateField('Arrivée réelle', null=True, blank=True)
    
    # Statut
    status = models.CharField('Statut', max_length=20, choices=ShipmentStatus.choices, 
                             default=ShipmentStatus.PREPARING)
    
    # Infos transport
    transporter = models.CharField('Transporteur', max_length=100, blank=True)
    vehicle_info = models.CharField('Véhicule/Conteneur', max_length=100, blank=True)
    tracking_number = models.CharField('N° suivi', max_length=100, blank=True)
    
    # Origine/Destination
    origin = models.CharField('Origine', max_length=100, default='Dakar, Sénégal')
    destination = models.CharField('Destination', max_length=100, default='Abidjan, Côte d\'Ivoire')
    
    # Notes
    notes = models.TextField('Notes', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shipments_created')
    
    class Meta:
        verbose_name = 'Expédition'
        verbose_name_plural = 'Expéditions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reference} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_reference(cls):
        today = timezone.now()
        prefix = f"EXP-{today.strftime('%Y%m')}"
        last = cls.objects.filter(reference__startswith=prefix).order_by('-reference').first()
        if last:
            last_num = int(last.reference.split('-')[-1])
            return f"{prefix}-{last_num + 1:04d}"
        return f"{prefix}-0001"
    
    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def days_in_transit(self):
        if self.departure_date and self.status in [ShipmentStatus.SHIPPED, ShipmentStatus.IN_TRANSIT]:
            return (timezone.now().date() - self.departure_date).days
        return None
    
    def receive(self, user):
        """Réceptionne l'expédition et met à jour le stock"""
        self.status = ShipmentStatus.RECEIVED
        self.actual_arrival = timezone.now().date()
        self.save()
        
        # Mettre à jour le stock pour chaque ligne
        for item in self.items.all():
            item.receive(user)


class ShipmentItem(models.Model):
    """Ligne d'expédition"""
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='shipment_items')
    
    quantity = models.DecimalField('Quantité', max_digits=12, decimal_places=2)
    quantity_received = models.DecimalField('Quantité reçue', max_digits=12, decimal_places=2, default=0)
    
    notes = models.CharField('Notes', max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Ligne expédition'
        verbose_name_plural = 'Lignes expédition'
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def receive(self, user):
        """Réceptionne cette ligne"""
        self.quantity_received = self.quantity
        self.save()
        
        # Créer le mouvement de stock
        StockMovement.objects.create(
            product=self.product,
            movement_type='in',
            quantity=self.quantity,
            reason=f"Réception {self.shipment.reference}",
            shipment=self.shipment,
            created_by=user
        )
        
        # Mettre à jour le stock produit
        self.product.stock_quantity += self.quantity
        self.product.save()


class StockMovementType(models.TextChoices):
    IN = 'in', 'Entrée'
    OUT = 'out', 'Sortie'
    ADJUSTMENT = 'adjustment', 'Ajustement'
    TRANSFER = 'transfer', 'Transfert'
    RETURN = 'return', 'Retour'


class StockMovement(models.Model):
    """Mouvement de stock"""
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements')
    
    movement_type = models.CharField('Type', max_length=20, choices=StockMovementType.choices)
    quantity = models.DecimalField('Quantité', max_digits=12, decimal_places=2)
    
    # Stock après mouvement
    stock_after = models.DecimalField('Stock après', max_digits=12, decimal_places=2, null=True)
    
    # Raison/origine
    reason = models.CharField('Motif', max_length=255)
    
    # Liens optionnels
    shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    inventory_control = models.ForeignKey('InventoryControl', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Date', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'
        ordering = ['-created_at']
    
    def __str__(self):
        sign = '+' if self.movement_type == 'in' else '-'
        return f"{sign}{self.quantity} {self.product.code}"
    
    def save(self, *args, **kwargs):
        if self.stock_after is None:
            self.stock_after = self.product.stock_quantity
        super().save(*args, **kwargs)


class CustomerScore(models.Model):
    """Score client pour priorisation"""
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='score_detail')
    
    # Scores composants (0-100)
    payment_score = models.IntegerField('Score paiement', default=50, 
                                        help_text='Régularité des paiements')
    volume_score = models.IntegerField('Score volume', default=50,
                                       help_text='Volume d\'achat')
    frequency_score = models.IntegerField('Score fréquence', default=50,
                                          help_text='Fréquence des commandes')
    loyalty_score = models.IntegerField('Score fidélité', default=50,
                                        help_text='Ancienneté et régularité')
    
    # Score global calculé
    auto_score = models.IntegerField('Score automatique', default=50)
    
    # Métriques
    total_orders = models.IntegerField('Nb commandes', default=0)
    total_amount = models.DecimalField('CA total', max_digits=14, decimal_places=2, default=0)
    avg_payment_delay = models.IntegerField('Délai paiement moyen (j)', default=0)
    last_order_date = models.DateField('Dernière commande', null=True, blank=True)
    
    # Mise à jour
    last_calculated = models.DateTimeField('Dernier calcul', auto_now=True)
    
    class Meta:
        verbose_name = 'Score client'
        verbose_name_plural = 'Scores clients'
    
    def __str__(self):
        return f"{self.customer.name} - Score: {self.final_score}/100"
    
    @property
    def final_score(self):
        """Score final combinant auto et manuel"""
        manual = self.customer.manual_score * 10 if self.customer.manual_score else 50
        return int((self.auto_score + manual) / 2)
    
    def calculate(self):
        """Recalcule le score automatique"""
        from django.db.models import Avg, Count, Sum
        
        # Récupérer les stats
        orders = self.customer.orders.filter(status__in=[OrderStatus.DELIVERED, OrderStatus.INVOICED])
        invoices = self.customer.invoices.all()
        
        # Volume
        self.total_orders = orders.count()
        self.total_amount = orders.aggregate(total=Sum('total'))['total'] or 0
        
        if self.total_orders > 0:
            # Score volume (basé sur CA)
            if self.total_amount >= 10000000:  # 10M+
                self.volume_score = 100
            elif self.total_amount >= 5000000:
                self.volume_score = 80
            elif self.total_amount >= 1000000:
                self.volume_score = 60
            else:
                self.volume_score = 40
            
            # Score fréquence
            last_order = orders.order_by('-created_at').first()
            if last_order:
                self.last_order_date = last_order.created_at.date()
                days_since = (timezone.now().date() - self.last_order_date).days
                if days_since <= 30:
                    self.frequency_score = 100
                elif days_since <= 60:
                    self.frequency_score = 80
                elif days_since <= 90:
                    self.frequency_score = 60
                else:
                    self.frequency_score = 30
            
            # Score paiement
            paid_invoices = invoices.filter(status=InvoiceStatus.PAID)
            if paid_invoices.exists():
                # Délai moyen de paiement (simplifié)
                self.payment_score = 70  # À affiner avec les dates réelles
            else:
                self.payment_score = 50
            
            # Score fidélité (ancienneté)
            first_order = orders.order_by('created_at').first()
            if first_order:
                months_active = (timezone.now().date() - first_order.created_at.date()).days / 30
                if months_active >= 24:
                    self.loyalty_score = 100
                elif months_active >= 12:
                    self.loyalty_score = 80
                elif months_active >= 6:
                    self.loyalty_score = 60
                else:
                    self.loyalty_score = 40
        
        # Calcul score global
        self.auto_score = int(
            (self.payment_score * 0.35) +
            (self.volume_score * 0.25) +
            (self.frequency_score * 0.25) +
            (self.loyalty_score * 0.15)
        )
        
        self.save()


class PreOrderStatus(models.TextChoices):
    PENDING = 'pending', 'En attente'
    ALLOCATED = 'allocated', 'Alloué'
    FULFILLED = 'fulfilled', 'Satisfait'
    CANCELLED = 'cancelled', 'Annulé'


class PreOrder(models.Model):
    """Pré-commande sur arrivage futur"""
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='preorders')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='preorders')
    
    # Quantité demandée
    quantity = models.DecimalField('Quantité', max_digits=12, decimal_places=2)
    quantity_allocated = models.DecimalField('Quantité allouée', max_digits=12, decimal_places=2, default=0)
    
    # Expédition ciblée (optionnel)
    target_shipment = models.ForeignKey(Shipment, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='preorders', verbose_name='Expédition ciblée')
    
    # Priorité (basée sur score client)
    priority = models.IntegerField('Priorité', default=50, 
                                   help_text='Plus élevé = plus prioritaire')
    
    # Statut
    status = models.CharField('Statut', max_length=20, choices=PreOrderStatus.choices,
                             default=PreOrderStatus.PENDING)
    
    # Notes
    notes = models.TextField('Notes', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Pré-commande'
        verbose_name_plural = 'Pré-commandes'
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"PRE-{self.pk} - {self.customer.name} - {self.quantity} x {self.product.code}"
    
    def save(self, *args, **kwargs):
        # Auto-calculer la priorité selon le score client
        if hasattr(self.customer, 'score_detail'):
            self.priority = self.customer.score_detail.final_score
        elif self.customer.manual_score:
            self.priority = self.customer.manual_score * 10
        super().save(*args, **kwargs)
    
    @property
    def remaining_quantity(self):
        return self.quantity - self.quantity_allocated


class StockReservationType(models.TextChoices):
    ORDER = 'order', 'Commande'
    PREORDER = 'preorder', 'Pré-commande'
    HOLD = 'hold', 'Blocage'
    CREDIT = 'credit', 'Avoir client (stock)'


class StockReservation(models.Model):
    """Réservation de stock"""
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='reservations')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='stock_reservations')
    
    quantity = models.DecimalField('Quantité réservée', max_digits=12, decimal_places=2)
    
    reservation_type = models.CharField('Type', max_length=20, choices=StockReservationType.choices)
    
    # Liens optionnels
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_reservations')
    preorder = models.ForeignKey(PreOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    
    # Validité
    expiry_date = models.DateField('Date expiration', null=True, blank=True)
    is_active = models.BooleanField('Active', default=True)
    
    # Notes
    reason = models.CharField('Motif', max_length=255, blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Réservation stock'
        verbose_name_plural = 'Réservations stock'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.quantity} x {self.product.code} pour {self.customer.name}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False


class InventoryControlStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    IN_PROGRESS = 'in_progress', 'En cours'
    VALIDATED = 'validated', 'Validé'
    CANCELLED = 'cancelled', 'Annulé'


class InventoryControl(models.Model):
    """Contrôle d'inventaire (virtuel vs physique)"""
    # Identification
    reference = models.CharField('Référence', max_length=30, unique=True, editable=False)
    name = models.CharField('Nom', max_length=100, default='Inventaire')
    
    # Date
    control_date = models.DateField('Date contrôle')
    
    # Statut
    status = models.CharField('Statut', max_length=20, choices=InventoryControlStatus.choices,
                             default=InventoryControlStatus.DRAFT)
    
    # Notes
    notes = models.TextField('Notes', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inventories_created')
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventories_validated')
    validated_at = models.DateTimeField('Validé le', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Contrôle inventaire'
        verbose_name_plural = 'Contrôles inventaire'
        ordering = ['-control_date']
    
    def __str__(self):
        return f"{self.reference} - {self.control_date}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_reference(cls):
        today = timezone.now()
        prefix = f"INV-{today.strftime('%Y%m%d')}"
        last = cls.objects.filter(reference__startswith=prefix).order_by('-reference').first()
        if last:
            last_num = int(last.reference.split('-')[-1])
            return f"{prefix}-{last_num + 1:02d}"
        return f"{prefix}-01"
    
    @property
    def total_difference(self):
        """Écart total (+ ou -)"""
        return sum(line.difference for line in self.lines.all())
    
    @property
    def has_differences(self):
        return any(line.difference != 0 for line in self.lines.all())
    
    @property
    def total_discrepancies(self):
        """Nombre de lignes avec écart"""
        return sum(1 for line in self.lines.all() if line.physical_quantity is not None and line.difference != 0)
    
    def validate(self, user):
        """Valide l'inventaire et applique les ajustements"""
        for line in self.lines.all():
            if line.difference != 0:
                # Créer mouvement d'ajustement
                StockMovement.objects.create(
                    product=line.product,
                    movement_type='adjustment',
                    quantity=line.difference,
                    stock_after=line.physical_quantity,
                    reason=f"Ajustement inventaire {self.reference}",
                    inventory_control=self,
                    created_by=user
                )
                
                # Mettre à jour le stock
                line.product.stock_quantity = line.physical_quantity
                line.product.save()
        
        self.status = InventoryControlStatus.VALIDATED
        self.validated_by = user
        self.validated_at = timezone.now()
        self.save()


class InventoryLine(models.Model):
    """Ligne de contrôle d'inventaire"""
    inventory = models.ForeignKey(InventoryControl, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    
    # Quantités
    theoretical_quantity = models.DecimalField('Quantité théorique', max_digits=12, decimal_places=2)
    physical_quantity = models.DecimalField('Quantité physique', max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Notes
    notes = models.CharField('Notes', max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Ligne inventaire'
        verbose_name_plural = 'Lignes inventaire'
        unique_together = ['inventory', 'product']
    
    def __str__(self):
        return f"{self.product.code}: {self.theoretical_quantity} → {self.physical_quantity or '?'}"
    
    @property
    def difference(self):
        if self.physical_quantity is not None:
            return self.physical_quantity - self.theoretical_quantity
        return Decimal('0')
    
    @property
    def discrepancy(self):
        """Alias pour difference"""
        return self.difference
    
    @property
    def has_difference(self):
        return self.difference != 0


# ============================================================
# PHASE 5: LOGISTIQUE - BONS DE LIVRAISON
# ============================================================

class DeliveryNoteStatus(models.TextChoices):
    DRAFT = 'draft', 'Brouillon'
    READY = 'ready', 'Prêt pour livraison'
    IN_DELIVERY = 'in_delivery', 'En cours de livraison'
    DELIVERED = 'delivered', 'Livré'
    CANCELLED = 'cancelled', 'Annulé'


class DeliveryNote(models.Model):
    """Bon de livraison"""
    # Identification
    number = models.CharField('Numéro BL', max_length=30, unique=True, editable=False)
    
    # Relations
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='delivery_notes')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='delivery_notes')
    
    # Adresse livraison
    delivery_address = models.TextField('Adresse de livraison', blank=True)
    delivery_contact = models.CharField('Contact livraison', max_length=100, blank=True)
    delivery_phone = models.CharField('Téléphone livraison', max_length=20, blank=True)
    
    # Dates
    planned_date = models.DateField('Date prévue', null=True, blank=True)
    delivery_date = models.DateTimeField('Date livraison effective', null=True, blank=True)
    
    # Transport
    transporter = models.CharField('Transporteur', max_length=100, blank=True)
    vehicle_info = models.CharField('Véhicule', max_length=100, blank=True)
    
    # Statut
    status = models.CharField('Statut', max_length=20, choices=DeliveryNoteStatus.choices,
                             default=DeliveryNoteStatus.DRAFT)
    
    # Signature
    received_by = models.CharField('Réceptionné par', max_length=100, blank=True)
    signature = models.TextField('Signature (base64)', blank=True)  # Pour signature digitale future
    
    # Notes
    notes = models.TextField('Notes', blank=True)
    driver_notes = models.TextField('Notes chauffeur', blank=True)
    
    # Traçabilité
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='delivery_notes_created')
    delivered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='delivery_notes_delivered')
    
    class Meta:
        verbose_name = 'Bon de livraison'
        verbose_name_plural = 'Bons de livraison'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"BL {self.number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self.generate_number()
        # Copier l'adresse du client si pas définie
        if not self.delivery_address and self.customer:
            self.delivery_address = self.customer.address
            self.delivery_phone = self.customer.phone
        super().save(*args, **kwargs)
    
    @classmethod
    def generate_number(cls):
        from django.utils import timezone
        today = timezone.now()
        prefix = f"BL-{today.strftime('%Y%m')}"
        last = cls.objects.filter(number__startswith=prefix).order_by('-number').first()
        if last:
            last_num = int(last.number.split('-')[-1])
            return f"{prefix}-{last_num + 1:04d}"
        return f"{prefix}-0001"
    
    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_weight(self):
        """Poids total en kg"""
        return sum(item.total_weight for item in self.items.all())
    
    @classmethod
    def create_from_order(cls, order, user=None):
        """Créer un BL depuis une commande"""
        delivery = cls.objects.create(
            order=order,
            customer=order.customer,
            delivery_address=order.delivery_address or order.customer.address,
            created_by=user
        )
        
        # Copier les lignes de commande
        for order_item in order.items.all():
            DeliveryNoteItem.objects.create(
                delivery_note=delivery,
                product=order_item.product,
                order_item=order_item,
                quantity=order_item.quantity
            )
        
        return delivery
    
    def mark_delivered(self, user=None, received_by=''):
        """Marquer comme livré"""
        from django.utils import timezone
        self.status = DeliveryNoteStatus.DELIVERED
        self.delivery_date = timezone.now()
        self.delivered_by = user
        if received_by:
            self.received_by = received_by
        self.save()
        
        # Mettre à jour la commande
        self.order.status = OrderStatus.DELIVERED
        self.order.save()
        
        # Créer mouvements de sortie stock
        for item in self.items.all():
            StockMovement.objects.create(
                product=item.product,
                movement_type=StockMovementType.OUT,
                quantity=item.quantity,
                reference=f"BL {self.number}",
                stock_after=item.product.stock_quantity - item.quantity,
                order=self.order,
                created_by=user
            )
            
            # Mettre à jour stock
            item.product.stock_quantity -= item.quantity
            item.product.save()


class DeliveryNoteItem(models.Model):
    """Ligne de bon de livraison"""
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    order_item = models.ForeignKey(OrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    
    quantity = models.DecimalField('Quantité', max_digits=12, decimal_places=2)
    quantity_delivered = models.DecimalField('Quantité livrée', max_digits=12, decimal_places=2, default=0)
    
    # Lot si traçabilité
    lot_number = models.CharField('N° lot', max_length=50, blank=True)
    
    # Notes
    notes = models.CharField('Notes', max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Ligne BL'
        verbose_name_plural = 'Lignes BL'
    
    def __str__(self):
        return f"{self.quantity} x {self.product.code}"
    
    @property
    def total_weight(self):
        """Poids en kg"""
        return self.quantity * self.product.unit_weight if hasattr(self.product, 'unit_weight') else self.quantity


# ============================================================
# PHASE 6: EMAILING & AUTOMATISATIONS
# ============================================================

class EmailCategory(models.TextChoices):
    ORDER = 'order', 'Commandes'
    PAYMENT = 'payment', 'Paiements'
    STOCK = 'stock', 'Stock'
    MARKETING = 'marketing', 'Marketing'
    LOYALTY = 'loyalty', 'Fidélité'


class EmailTemplate(models.Model):
    """Template d'email pré-conçu"""
    # Identification
    code = models.CharField('Code', max_length=50, unique=True)
    name = models.CharField('Nom', max_length=100)
    
    # Catégorie
    category = models.CharField('Catégorie', max_length=20, choices=EmailCategory.choices)
    
    # Contenu
    subject = models.CharField('Sujet', max_length=200, help_text="Utiliser {{client_name}}, {{amount}}, etc.")
    body_html = models.TextField('Corps HTML')
    body_text = models.TextField('Corps texte (fallback)', blank=True)
    
    # Configuration
    is_active = models.BooleanField('Actif', default=True)
    auto_trigger = models.CharField('Déclencheur auto', max_length=100, blank=True,
                                   help_text="Event qui déclenche l'envoi (ex: order_created)")
    
    # Méta
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Modifié le', auto_now=True)
    
    class Meta:
        verbose_name = 'Template email'
        verbose_name_plural = 'Templates email'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def render(self, context):
        """Rendre le template avec le contexte"""
        from django.template import Template, Context
        
        subject = Template(self.subject).render(Context(context))
        body_html = Template(self.body_html).render(Context(context))
        body_text = Template(self.body_text).render(Context(context)) if self.body_text else ''
        
        return subject, body_html, body_text


class EmailStatus(models.TextChoices):
    PENDING = 'pending', 'En attente'
    SENT = 'sent', 'Envoyé'
    FAILED = 'failed', 'Échoué'
    BOUNCED = 'bounced', 'Rejeté'


class EmailLog(models.Model):
    """Historique des emails envoyés"""
    # Template utilisé
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='logs')
    
    # Destinataire
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True,
                                related_name='email_logs')
    recipient_email = models.EmailField('Email destinataire')
    recipient_name = models.CharField('Nom destinataire', max_length=100, blank=True)
    
    # Contenu envoyé
    subject = models.CharField('Sujet', max_length=200)
    body_html = models.TextField('Corps HTML')
    body_text = models.TextField('Corps texte', blank=True)
    
    # Statut
    status = models.CharField('Statut', max_length=20, choices=EmailStatus.choices,
                             default=EmailStatus.PENDING)
    
    # Référence objet lié
    related_type = models.CharField('Type objet', max_length=50, blank=True)  # Order, Invoice, etc.
    related_id = models.PositiveIntegerField('ID objet', null=True, blank=True)
    
    # Méta
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    sent_at = models.DateTimeField('Envoyé le', null=True, blank=True)
    error_message = models.TextField('Message erreur', blank=True)
    
    # Traçabilité
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Log email'
        verbose_name_plural = 'Logs email'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} → {self.recipient_email} ({self.get_status_display()})"
    
    def send(self, fail_silently=True):
        """Envoyer l'email"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        try:
            send_mail(
                subject=self.subject,
                message=self.body_text or self.body_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.recipient_email],
                html_message=self.body_html,
                fail_silently=fail_silently
            )
            self.status = EmailStatus.SENT
            self.sent_at = timezone.now()
        except Exception as e:
            self.status = EmailStatus.FAILED
            self.error_message = str(e)
        
        self.save()
        return self.status == EmailStatus.SENT


class AutomationTrigger(models.TextChoices):
    ORDER_CREATED = 'order_created', 'Nouvelle commande'
    ORDER_CONFIRMED = 'order_confirmed', 'Commande confirmée'
    ORDER_DELIVERED = 'order_delivered', 'Commande livrée'
    INVOICE_CREATED = 'invoice_created', 'Facture créée'
    PAYMENT_RECEIVED = 'payment_received', 'Paiement reçu'
    PAYMENT_DUE_3D = 'payment_due_3d', 'Échéance dans 3 jours'
    PAYMENT_DUE_7D = 'payment_due_7d', 'Retard 7 jours'
    PAYMENT_DUE_30D = 'payment_due_30d', 'Retard 30 jours'
    STOCK_ARRIVED = 'stock_arrived', 'Stock arrivé'
    MANUAL = 'manual', 'Envoi manuel'


class AutomationRule(models.Model):
    """Règle d'automatisation d'envoi d'email"""
    # Identification
    name = models.CharField('Nom', max_length=100)
    
    # Déclencheur
    trigger_event = models.CharField('Événement déclencheur', max_length=50,
                                    choices=AutomationTrigger.choices)
    
    # Template à utiliser
    email_template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE,
                                       related_name='automation_rules')
    
    # Conditions additionnelles (JSON)
    conditions = models.JSONField('Conditions', default=dict, blank=True,
                                  help_text='Ex: {"min_amount": 100000, "customer_type": "B2B"}')
    
    # Configuration
    is_active = models.BooleanField('Actif', default=True)
    priority = models.PositiveIntegerField('Priorité', default=0)
    
    # Méta
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    last_triggered = models.DateTimeField('Dernier déclenchement', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Règle automatisation'
        verbose_name_plural = 'Règles automatisation'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_event_display()})"
    
    def check_conditions(self, context):
        """Vérifier si les conditions sont remplies"""
        if not self.conditions:
            return True
        
        for key, value in self.conditions.items():
            if key == 'min_amount':
                if context.get('amount', 0) < value:
                    return False
            elif key == 'customer_type':
                if context.get('customer_type') != value:
                    return False
            # Ajouter d'autres conditions selon besoins
        
        return True
    
    def execute(self, context, user=None):
        """Exécuter la règle et envoyer l'email"""
        if not self.is_active or not self.email_template.is_active:
            return None
        
        if not self.check_conditions(context):
            return None
        
        # Récupérer le destinataire
        customer = context.get('customer')
        email = context.get('email') or (customer.email if customer else None)
        
        if not email:
            return None
        
        # Rendre le template
        subject, body_html, body_text = self.email_template.render(context)
        
        # Créer le log
        log = EmailLog.objects.create(
            template=self.email_template,
            customer=customer,
            recipient_email=email,
            recipient_name=customer.name if customer else '',
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            related_type=context.get('related_type', ''),
            related_id=context.get('related_id'),
            sent_by=user
        )
        
        # Envoyer
        log.send()
        
        # Mettre à jour la règle
        self.last_triggered = timezone.now()
        self.save()
        
        return log


def trigger_automation(event, context, user=None):
    """Déclencher les automatisations pour un événement"""
    rules = AutomationRule.objects.filter(
        trigger_event=event,
        is_active=True
    ).order_by('-priority')
    
    logs = []
    for rule in rules:
        log = rule.execute(context, user)
        if log:
            logs.append(log)
    
    return logs
