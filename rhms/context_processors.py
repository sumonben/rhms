from django.conf import settings
from .models import HotelDetails
from rooms.models import Room
from cart.cart import Cart
def site_info(request):
        hotel_details=HotelDetails.objects.last()
        cart=Cart(request)
        request.session = request.session
        cart = request.session.get(settings.CART_SESSION_ID)
        cart_rooms=Room.objects.filter(id__in=cart)
        total_cart_amount=0
        for cart_room in cart_rooms:
            total_cart_amount = total_cart_amount+int(cart_room.price)

        return {
            'SITE_NAME': hotel_details.title,
            'SITE_NAME_ENG': hotel_details.title_en,
            'SLOGAN': hotel_details.slogan,
            'SLOGAN_ENG': hotel_details.slogan_en,
            'UPAZILLA':hotel_details.upazilla,
            'DISTRICT':hotel_details.district,
            'LOGO': hotel_details.logo,
            'LOGO_OPACITY': hotel_details.logo_opacity,
            'LOGO_ENG': hotel_details.logo,
            'LOGO_OPACITY_ENG': hotel_details.logo_opacity_en,
            'MONOGRAM': hotel_details.monogram,
            'MONOGRAM_ENG': hotel_details.monogram_en,
            'cart_rooms':cart_rooms,
            'total_cart_amount':total_cart_amount,

        }
