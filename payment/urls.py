from django.contrib import admin
from django.urls import path,include, re_path
from . import views

urlpatterns = [
    
        # path('', views.searchPayment, name='search_payment'),
        # path('proceed_payment/', views.ProceedPayment, name='proceed_payment'),
        # path('get_payment_receipt/', views.getPaymentReceipt, name='get_payment_receipt'),
        path('success/', views.CheckoutSuccessView.as_view(), name='success'),
        path('failed/', views.CheckoutFaildView.as_view(), name='failed'),
        path('canceled/', views.CheckoutCanceledView.as_view(), name='canceled'),
        path('ipn/', views.CheckoutIPNView.as_view(), name='ipn'),






]