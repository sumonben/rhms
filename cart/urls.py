    # cart/urls.py
    from django.urls import path
    from . import views

    app_name = 'cart'

    urlpatterns = [
        path('add/<int:product_id>/', views.cart_add, name='cart_add'),
        path('', views.cart_detail, name='cart_detail'),
    ]