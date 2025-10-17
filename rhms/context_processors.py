from django.conf import settings
from .models import HotelDetails
def site_info(request):
        hotel_details=HotelDetails.objects.last()

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
        }
