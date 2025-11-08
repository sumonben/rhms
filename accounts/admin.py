from django.contrib import admin
from .models import Department, Designation, Guest, Staff,Comment
from import_export.admin import ExportActionMixin,ImportExportMixin

# Register your models here.


@admin.register(Department)
class DepartmentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','name','name_eng']
    search_fields=[   'serial','name','name_eng']
    list_display_links = ['serial','name']
@admin.register(Designation)
class DesignationAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','name','name_eng']
    search_fields=[   'serial','name','name_eng']
    list_display_links = ['serial','name']
@admin.register(Staff)
class StaffAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[   'serial','name','name_eng','phone','email']
    search_fields=[   'serial','name','name_eng','phone','email']
    list_display_links = ['serial','name']
@admin.register(Guest)
class GuestAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[ 'id','name','name_eng','phone','email']
    search_fields=[   'name','name_eng','phone']
    list_display_links = ['id','name']
@admin.register(Comment)
class CommentAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display=[ 'id','name','email','guest','content','date_posted']
    search_fields=[   'name','email',]
    list_display_links = ['id','name']