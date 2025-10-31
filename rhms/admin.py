from django.contrib import admin
from django.forms import TextInput, Textarea
from django.db import models
from .models import HotelDetails, Carousel, Booking
from import_export.admin import ExportActionMixin,ImportExportMixin
from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)
# Register your models here.
@admin.register(HotelDetails)
class HotelDetailsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','title','title_en','license_no']
    search_fields=[  'title','license_no']
    list_display_links = ['serial','title']
@admin.register(Carousel)
class CarouselAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','title','title_en']
    search_fields=[  'title','title_en']
    list_display_links = ['serial','title']
@admin.register(Booking)
class BookingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'id','tracking_no','guest_details','start_day','end_day','booked_on','transaction_details']
    search_fields=[  'tracking_no',]
    list_display_links = ['id','tracking_no']
    list_filter=( 'booked_on',("booked_on", DateRangeFilterBuilder()),)
    filter_horizontal = ['room',]

