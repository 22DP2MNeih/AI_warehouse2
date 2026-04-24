from django.contrib import admin
from .models import Company, Warehouse, Product, CompanyProduct, WarehouseStock, Order, StockTransaction

# 1. This allows you to edit Warehouse Stock inside the Company Product page
class WarehouseStockInline(admin.TabularInline):
    model = WarehouseStock
    extra = 1 # Shows one empty row by default to add new stock

# 2. This allows you to edit the Company SKU/Price inside the Global Product page
class CompanyProductInline(admin.StackedInline):
    model = CompanyProduct
    extra = 1
    show_change_link = True # Adds a link to jump to the full edit page

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at')
    search_fields = ('name', 'description')
    inlines = [CompanyProductInline]

@admin.register(CompanyProduct)
class CompanyProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'product', 'company', 'price')
    list_filter = ('company',)
    search_fields = ('sku', 'product__name')
    inlines = [WarehouseStockInline]

@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ('company_product', 'warehouse', 'quantity', 'location')
    list_filter = ('warehouse', 'warehouse__company')
    search_fields = ('company_product__sku', 'company_product__product__name')

# Registering the rest with default views
admin.site.register(Company)
admin.site.register(Warehouse)
admin.site.register(Order)
admin.site.register(StockTransaction)
