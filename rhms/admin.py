from django.contrib import admin
from django.forms import TextInput, Textarea
from django.db import models
from .models import HotelDetails, Carousel, Booking, ImportantLinks, ColorRoot
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
    list_display=[   'id','tracking_no','guest_details','start_day','end_day','check_in_status','check_in_time','check_out_status','booked_on','transaction_details']
    search_fields=[  'tracking_no',]
    list_display_links = ['id','tracking_no']
    list_filter=( 'booked_on','check_in_status','check_out_status',("booked_on", DateRangeFilterBuilder()),)
    filter_horizontal = ['room',]
    readonly_fields = ['check_in_time', 'check_out_time']

@admin.register(ImportantLinks)
class ImportantLinksAdmin(ImportExportMixin,admin.ModelAdmin):
    pass
@admin.register(ColorRoot)
class ColorRootAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','title','title_en','body',
    'weather',
    'service',
    'card',
    'heading',
    'sub_heading',
    'navitem',
    'navbar_collaps',
    'member_registration',
    'internal',
    'other_text',
    'hotel_details',
    'is_active']
    search_fields=[  'title','title_en']
    list_display_links = ['serial','title']
    list_editable=[ 'title_en','body',
    'weather',
    'service',
    'card',
    'heading',
    'sub_heading',
    'navitem',
    'navbar_collaps',
    'member_registration',
    'internal',
    'other_text',
    'is_active']