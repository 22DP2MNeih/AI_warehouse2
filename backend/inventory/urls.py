from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, 
    CompanyProductViewSet, 
    WarehouseStockViewSet, 
    OrderViewSet,
    MarketViewSet,
    WarehouseViewSet,
    CompanySettingsViewSet
)

# API MARŠRUTĒŠANA
# Šis fails definē visus pieejamos API galapunktus (endpoints).
# Tiek izmantots DefaultRouter, kas automātiski ģenerē URL adreses visām ViewSet darbībām.
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'company-products', CompanyProductViewSet, basename='companyproduct')
router.register(r'stock', WarehouseStockViewSet, basename='warehousestock')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'market', MarketViewSet, basename='market')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'company-settings', CompanySettingsViewSet, basename='company-settings')

urlpatterns = [
    path('', include(router.urls)),
]