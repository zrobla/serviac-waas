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
