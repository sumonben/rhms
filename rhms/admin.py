from django.contrib import admin
from django.forms import TextInput, Textarea
from django.db import models
from .models import HotelDetails
from import_export.admin import ExportActionMixin,ImportExportMixin

# Register your models here.
@admin.register(HotelDetails)
class HotelDetailsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','title','title_en','license_no']
    search_fields=[  'title','license_no']
    list_display_links = ['serial','title']