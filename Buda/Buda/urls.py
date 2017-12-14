"""Buda URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^tablero-instituciones/$', views.tabla_comparativa),
    url(r'^tablero-instituciones/detalle/(?P<slug>[-_a-zA-Z0-9]+)/$', views.detalle_institucion),
    url(r'^tablero-instituciones/generar-resumen/$', views.genera_resumen_dependencias),
    url(r'^tablero-instituciones/apicomparativa/$', views.api_comparativa),
    url(r'^tablero-instituciones/apicomparativa/recursos-mas-descargados/$', views.recursos_mas_descargados),
    url(r'^tablero-instituciones/apicomparativa/total-recursos/$', views.total_de_recursos),
    url(r'^tablero-instituciones/apicomparativa/recursos-mas-descargados/(?P<slug>[-_a-zA-Z0-9]+)/$', views.recursos_mas_descargados_dep),
    url(r'^tablero-instituciones/apicomparativa/(?P<slug>[-_a-zA-Z0-9]+)/$', views.api_comparativa_dependencia),
]
