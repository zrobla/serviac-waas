"""SERVIAC GROUP - URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse

# SEO Files
def robots_txt(request):
    content = """# robots.txt for SERVIAC GROUP
User-agent: *
Allow: /
Disallow: /crm/
Disallow: /admin/
Disallow: /api/

Sitemap: https://serviac-group.com/sitemap.xml
"""
    return HttpResponse(content, content_type="text/plain")

def sitemap_xml(request):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://serviac-group.com/</loc><priority>1.0</priority></url>
    <url><loc>https://serviac-group.com/produits/</loc><priority>0.9</priority></url>
    <url><loc>https://serviac-group.com/a-propos/</loc><priority>0.7</priority></url>
    <url><loc>https://serviac-group.com/contact/</loc><priority>0.8</priority></url>
    <url><loc>https://serviac-group.com/commander/</loc><priority>0.9</priority></url>
</urlset>"""
    return HttpResponse(content, content_type="application/xml")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('crm.api.urls')),
    path('crm/', include('crm.urls')),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
    path('', include('website.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
