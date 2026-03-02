"""SERVIAC Website - Public Views"""
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Page d'accueil SERVIAC GROUP"""
    template_name = 'website/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Accueil'
        return context


class ProductsView(TemplateView):
    """Catalogue produits public"""
    template_name = 'website/products.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nos Produits'
        return context


class AboutView(TemplateView):
    """Page À propos"""
    template_name = 'website/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'À Propos'
        return context


class ContactView(TemplateView):
    """Page Contact"""
    template_name = 'website/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contact'
        return context


class OrderFormView(TemplateView):
    """Formulaire de commande public - Interface officielle"""
    template_name = 'website/order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Commander'
        return context
