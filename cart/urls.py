# cart/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('add/<int:room_id>/', views.cartAdd, name='cart_add'),
    path('', views.cartAddRoom, name='cart_add_room'),
    path('cart_details/', views.cartDetails, name='cart_detail'),
]