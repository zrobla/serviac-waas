"""
Données initiales pour les templates email SERVIAC
"""
from django.core.management.base import BaseCommand
from crm.models import EmailTemplate, AutomationRule


class Command(BaseCommand):
    help = 'Charge les templates email pré-conçus pour SERVIAC'
    
    def handle(self, *args, **options):
        templates = [
            {
                'code': 'order_confirm',
                'name': 'Confirmation de commande',
                'category': 'order',
                'subject': 'SERVIAC - Confirmation de votre commande {{order_number}}',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1a237e; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #1a237e;">Merci pour votre commande !</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Nous avons bien reçu votre commande <strong>{{order_number}}</strong> du {{order_date}}.</p>
        
        <div style="background: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #1a237e;">Récapitulatif</h3>
            <p><strong>Montant:</strong> {{amount}} FCFA</p>
            <p><strong>Articles:</strong> {{items_count}} article(s)</p>
        </div>
        
        <p>Notre équipe va traiter votre commande dans les plus brefs délais.</p>
        <p>Nous vous contacterons pour la livraison.</p>
        
        <p style="margin-top: 30px;">
            Cordialement,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
    
    <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px;">
        <p>SERVIAC GROUP SUARL - Abidjan, Côte d'Ivoire</p>
    </div>
</div>
''',
                'auto_trigger': 'order_confirmed'
            },
            {
                'code': 'payment_reminder_3d',
                'name': 'Rappel échéance 3 jours',
                'category': 'payment',
                'subject': 'SERVIAC - Rappel: Échéance dans 3 jours',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1a237e; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #ff9800;">⏰ Rappel de paiement</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Nous vous rappelons que le paiement de votre facture <strong>{{invoice_number}}</strong> 
        arrive à échéance dans <strong>3 jours</strong> ({{due_date}}).</p>
        
        <div style="background: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ff9800;">
            <p style="margin: 0;"><strong>Montant à régler:</strong> {{amount}} FCFA</p>
        </div>
        
        <p>Merci de procéder au règlement avant cette date.</p>
        
        <p><strong>Moyens de paiement:</strong></p>
        <ul>
            <li>Espèces à notre magasin</li>
            <li>Orange Money / MTN Money / Wave</li>
            <li>Virement bancaire</li>
        </ul>
        
        <p style="margin-top: 30px;">
            Cordialement,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': 'payment_due_3d'
            },
            {
                'code': 'payment_reminder_7d',
                'name': 'Relance retard 7 jours',
                'category': 'payment',
                'subject': 'SERVIAC - URGENT: Facture en retard de paiement',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #d32f2f; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #d32f2f;">⚠️ Facture en retard</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Sauf erreur de notre part, la facture <strong>{{invoice_number}}</strong> 
        reste impayée depuis <strong>7 jours</strong> après son échéance.</p>
        
        <div style="background: #ffebee; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #d32f2f;">
            <p><strong>Montant impayé:</strong> {{amount}} FCFA</p>
            <p><strong>Échéance dépassée:</strong> {{due_date}}</p>
        </div>
        
        <p>Nous vous prions de régulariser cette situation dans les meilleurs délais.</p>
        
        <p style="margin-top: 30px;">
            Cordialement,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': 'payment_due_7d'
            },
            {
                'code': 'payment_reminder_30d',
                'name': 'Relance retard 30 jours',
                'category': 'payment',
                'subject': 'SERVIAC - DERNIER RAPPEL: Créance impayée',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #b71c1c; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #b71c1c;">🚨 DERNIER RAPPEL</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Malgré nos précédents rappels, la facture <strong>{{invoice_number}}</strong> 
        reste impayée depuis plus de <strong>30 jours</strong>.</p>
        
        <div style="background: #ffcdd2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #b71c1c;">
            <p><strong>Montant impayé:</strong> {{amount}} FCFA</p>
        </div>
        
        <p><strong>Sans règlement sous 48h:</strong></p>
        <ul>
            <li>Suspension des commandes en cours</li>
            <li>Blocage des nouvelles commandes</li>
        </ul>
        
        <p style="margin-top: 30px;">
            Service Recouvrement<br>
            <strong>SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': 'payment_due_30d'
            },
            {
                'code': 'payment_received',
                'name': 'Confirmation paiement',
                'category': 'payment',
                'subject': 'SERVIAC - Paiement reçu - Merci !',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1a237e; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #4caf50;">✅ Paiement reçu</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Nous avons bien reçu votre paiement.</p>
        
        <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4caf50;">
            <p><strong>Montant reçu:</strong> {{amount}} FCFA</p>
            <p><strong>Date:</strong> {{payment_date}}</p>
            <p><strong>Référence:</strong> {{payment_ref}}</p>
        </div>
        
        <p>Merci de votre confiance !</p>
        
        <p style="margin-top: 30px;">
            Cordialement,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': 'payment_received'
            },
            {
                'code': 'stock_arrived',
                'name': 'Notification arrivage',
                'category': 'stock',
                'subject': 'SERVIAC - 🎉 Nouvel arrivage disponible !',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1a237e; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #1a237e;">🚚 Nouvel arrivage !</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Un nouvel arrivage de produits vient d'être réceptionné.</p>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #1a237e;">
            <p><strong>Produits disponibles:</strong></p>
            <p>{{products_list}}</p>
        </div>
        
        <p>Passez votre commande dès maintenant !</p>
        
        <p style="margin-top: 30px;">
            Cordialement,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': 'stock_arrived'
            },
            {
                'code': 'order_delivered',
                'name': 'Confirmation livraison',
                'category': 'order',
                'subject': 'SERVIAC - Votre commande a été livrée',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #1a237e; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">SERVIAC GROUP</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #4caf50;">📦 Livraison effectuée</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Votre commande <strong>{{order_number}}</strong> a été livrée avec succès.</p>
        
        <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4caf50;">
            <p><strong>Date de livraison:</strong> {{delivery_date}}</p>
            <p><strong>N° BL:</strong> {{delivery_number}}</p>
        </div>
        
        <p>Merci de votre confiance !</p>
        
        <p style="margin-top: 30px;">
            Cordialement,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': 'order_delivered'
            },
            {
                'code': 'marketing_promo',
                'name': 'Offre promotionnelle',
                'category': 'marketing',
                'subject': 'SERVIAC - {{promo_title}}',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #ff5722; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">🔥 OFFRE SPÉCIALE</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #ff5722;">{{promo_title}}</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>{{promo_description}}</p>
        
        <div style="background: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
            <p style="font-size: 24px; color: #ff5722; margin: 0;"><strong>{{promo_discount}}</strong></p>
            <p style="margin: 5px 0 0;">Valable jusqu'au {{promo_end_date}}</p>
        </div>
        
        <p style="margin-top: 30px;">
            <strong>SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': ''
            },
            {
                'code': 'loyalty_thanks',
                'name': 'Remerciement fidélité',
                'category': 'loyalty',
                'subject': 'SERVIAC - Merci pour votre fidélité ! 🎁',
                'body_html': '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #9c27b0; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0;">🎁 MERCI !</h1>
    </div>
    
    <div style="padding: 20px; background: #f5f5f5;">
        <h2 style="color: #9c27b0;">Vous êtes un client fidèle</h2>
        
        <p>Bonjour <strong>{{client_name}}</strong>,</p>
        
        <p>Merci pour votre fidélité. Vous avez passé <strong>{{orders_count}} commandes</strong> chez nous !</p>
        
        <div style="background: #f3e5f5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #9c27b0;">
            <p><strong>Votre avantage fidélité:</strong></p>
            <p style="font-size: 18px;">{{loyalty_reward}}</p>
        </div>
        
        <p style="margin-top: 30px;">
            Avec nos sincères remerciements,<br>
            <strong>L'équipe SERVIAC GROUP</strong>
        </p>
    </div>
</div>
''',
                'auto_trigger': ''
            }
        ]
        
        created_count = 0
        for t in templates:
            template, created = EmailTemplate.objects.update_or_create(
                code=t['code'],
                defaults=t
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ Créé: {template.name}")
            else:
                self.stdout.write(f"  📝 Mis à jour: {template.name}")
        
        self.stdout.write(self.style.SUCCESS(f"\n{created_count} templates créés"))
        
        # Créer les règles d'automatisation
        automation_rules = [
            ('order_confirmed', 'order_confirm', 'Confirmation commande auto'),
            ('payment_received', 'payment_received', 'Remerciement paiement auto'),
            ('order_delivered', 'order_delivered', 'Notification livraison auto'),
        ]
        
        for trigger, template_code, name in automation_rules:
            try:
                template = EmailTemplate.objects.get(code=template_code)
                rule, created = AutomationRule.objects.update_or_create(
                    trigger_event=trigger,
                    email_template=template,
                    defaults={'name': name, 'is_active': True}
                )
                if created:
                    self.stdout.write(f"  ✅ Règle créée: {name}")
            except EmailTemplate.DoesNotExist:
                pass
        
        self.stdout.write(self.style.SUCCESS("\n✅ Initialisation emailing terminée !"))
