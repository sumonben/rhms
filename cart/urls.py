# cart/urls.py
from django.urls import path
from . import views
from django import views as django_views


urlpatterns = [
    path('add/<int:room_id>/', views.cartAdd, name='cart_add'),
    path('', views.cartAddRoom, name='cart_add_room'),
    path('cart_details/', views.cartDetails, name='cart_detail'),
    path('cart_clear/', views.cartClear, name='cart_clear'),
    path('order_cart/', views.orderCartView.as_view(), name='order_cart'),
    path('order_page/', views.orderPage, name='order_page'),
]