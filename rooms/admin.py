from django.contrib import admin
from import_export.admin import ExportActionMixin,ImportExportMixin
from .models import RoomType, Room,BedType
# Register your models here.
@admin.register(BedType)
class BedType(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_eng','description','occupancy']
    list_display_links = ['name','name_eng']
    search_fields = ['name','name_eng']
@admin.register(RoomType)
class RoomTypeAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_eng','description','occupancy']
    list_display_links = ['name','name_eng']
    search_fields = ['name','name_eng']
@admin.register(Room)
class RoomAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'serial','name','name_eng','room_no','room_type','bed_type']
    list_display_links = ['name','name_eng','room_no']
    list_filter=['room_type','bed_type']
    search_fields = ['name','name_eng','room_no']
