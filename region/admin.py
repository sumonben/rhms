from django.contrib import admin
from .models import Division, District, Upazilla, Address
from import_export.admin import ExportActionMixin,ImportExportMixin

# Register your models here.
@admin.register(Division)
class DivisionAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_en','link']
    list_display_links = ['name','name_en']
@admin.register(District)
class DistrictAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_en','division','link']
    list_display_links = ['name','name_en']
    list_filter=['division']
    search_fields = ['name','name_en','division']

@admin.register(Upazilla)
class UpazillaAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_en','district','link']
    list_display_links = ['name','name_en']
    list_filter=['district']
    search_fields = ['name','name_en','district']
@admin.register(Address)
class AddressAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display=['id','village_or_street','division','district','upazilla']
    search_fields=['village_or_street']
    list_filter=['division','district']
