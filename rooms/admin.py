from django.contrib import admin
from import_export.admin import ExportActionMixin,ImportExportMixin
from .models import RoomType, Room, BedType, RoomReview
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

# Register your models here.
class InlineEditableAdmin(admin.ModelAdmin):
    """
    Admin class with inline editing and AJAX saving for each row
    """
    change_list_template = 'admin/inline_editable_change_list.html'
    
    def get_urls(self):
        """Add custom URL for AJAX save"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/inline-save/',
                self.admin_site.admin_view(self.inline_save_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_inline_save',
            ),
        ]
        return custom_urls + urls
    
    def inline_save_view(self, request, object_id):
        """Handle AJAX save for inline editing"""
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'POST required'}, status=400)
        
        try:
            obj = self.get_object(request, object_id)
            if obj is None:
                return JsonResponse({'status': 'error', 'message': 'Object not found'}, status=404)
            
            data = json.loads(request.body)
            
            # Update fields
            for field_name, value in data.items():
                if hasattr(obj, field_name):
                    field = obj._meta.get_field(field_name)
                    
                    # Handle different field types
                    if field.get_internal_type() == 'BooleanField':
                        value = value in [True, 'true', 'True', '1', 1]
                    elif field.get_internal_type() in ['DecimalField', 'FloatField']:
                        value = float(value) if value else 0
                    elif field.get_internal_type() in ['IntegerField', 'PositiveIntegerField']:
                        value = int(value) if value else None
                    
                    setattr(obj, field_name, value)
            
            obj.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'{self.model._meta.verbose_name} updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    def get_list_display(self, request):
        """Add edit button to list display"""
        list_display = list(super().get_list_display(request))
        if 'edit_button' not in list_display:
            list_display.append('edit_button')
        return list_display
    
    def changelist_view(self, request, extra_context=None):
        """
        Add inline_editable_fields to template context as JSON
        """
        extra_context = extra_context or {}
        editable_fields = self.get_inline_editable_fields()
        extra_context['inline_editable_fields_json'] = json.dumps(editable_fields)
        return super().changelist_view(request, extra_context=extra_context)
    
    def edit_button(self, obj):
        """Render edit button for each row"""
        return format_html(
            '<button class="button inline-edit-btn" data-id="{}" '
            'data-app="{}" data-model="{}" onclick="enableInlineEdit(this, event);">Edit</button>',
            obj.pk,
            obj._meta.app_label,
            obj._meta.model_name
        )
    edit_button.short_description = 'Actions'
    
    def get_inline_editable_fields(self):
        """Override this in child classes to specify which fields are inline editable"""
        return []

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
class RoomAdmin(ImportExportMixin, InlineEditableAdmin):
    list_display=[ 'serial','name','name_eng','room_no','room_type','bed_type','status']
    list_filter=['room_type','bed_type']
    search_fields = ['name','name_eng','room_no']
    list_editable =['name','name_eng','status']
    def get_inline_editable_fields(self):
        # ONLY these fields will be editable
        return ['name','name_eng','room_no']


@admin.register(RoomReview)
class RoomReviewAdmin(admin.ModelAdmin):
    list_display = ['room', 'name', 'email', 'phone', 'rating', 'created_at', 'is_approved']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['name', 'email', 'comment', 'room__name_eng']
    

