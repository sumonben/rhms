from django.contrib import admin
from django.urls import path,include, re_path
import static
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django import views as django_views

urlpatterns = [
    
    path('', views.SubprocessesView, name='get_district'),

    path('jsi18n/', django_views.i18n.JavaScriptCatalog.as_view(), name='jsi18n'),

]