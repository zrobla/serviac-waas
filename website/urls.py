"""SERVIAC Website - URL Configuration"""
from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('produits/', views.ProductsView.as_view(), name='products'),
    path('a-propos/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('commander/', views.OrderFormView.as_view(), name='order_form'),
]
