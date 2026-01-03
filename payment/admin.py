from django.contrib import admin
from .models import Transaction,PaymentGateway
from import_export.admin import ExportActionMixin,ImportExportMixin

from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display=[ 'gateway_name','store_id', 'store_pass', 'is_sandbox', 'is_active']
    filter_fields=['is_active',]


# Register your models here.
@admin.register(Transaction)
class TransactionAdmin(ImportExportMixin,admin.ModelAdmin):
    list_display = ('name','tracking_no','email','phone', 'card_no', 'amount', 'tran_id','guest','status', 'created_at',)
    search_fields = ('tracking_no','phone', 'status')
    list_filter=( 'created_at',("created_at", DateRangeFilterBuilder()),)
    filter_horizontal = ['room']

