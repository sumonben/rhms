from django.contrib import admin
from import_export.admin import ExportActionMixin,ImportExportMixin
from .models import RoomType, Room
# Register your models here.
@admin.register(RoomType)
class RoomTypeAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_eng','description','occupancy']
    list_display_links = ['name','name_eng']
    search_fields = ['name','name_eng']
@admin.register(Room)
class RoomAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'name','name_eng','room_no','room_type']
    list_display_links = ['name','name_eng','room_no']
    list_filter=['room_type']
    search_fields = ['name','name_eng','room_no']