from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Product, CompanyProduct, WarehouseStock, Order, Warehouse, Company
from .serializers import (
    ProductSerializer, 
    CompanyProductSerializer, 
    WarehouseStockSerializer, 
    OrderSerializer,
    WarehouseSerializer,
    CompanySettingsSerializer
)
from django.http import HttpResponse
from .permissions import IsAdminOrManagerOrReadOnly
from .data_exchange import (
    export_orders_to_csv, import_parts_from_csv, 
    export_parts_to_csv, import_orders_from_csv
)
from django.utils import timezone

# KONFIGURĀCIJAS UN IESTATĪJUMI
# Šie ViewSet nodrošina noliktavu un uzņēmuma AI iestatījumu pārvaldību.
# Šeit tiek definēti arī AI apmācības procesi (train un train_all).
class WarehouseViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing warehouses.
    """
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'company'):
            return Warehouse.objects.none()
        return Warehouse.objects.filter(company=user.company)

class CompanySettingsViewSet(viewsets.ModelViewSet):
    """View to manage AI settings for companies."""
    serializer_class = CompanySettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Company.objects.all()
        if not user.company:
            return Company.objects.none()
        return Company.objects.filter(id=user.company.id)

    @action(detail=True, methods=['post'])
    def train(self, request, pk=None):
        """Manually trigger the AI training process for a specific company."""
        from .ai_model import InventoryForecastModel
        
        company = self.get_object()
        if request.user.role != 'ADMIN' and request.user.company != company:
            return Response({"error": "Unauthorized"}, status=403)

        sl = float(company.service_level) if company.service_level else 0.95
        engine = InventoryForecastModel(
            company_id=company.id, 
            service_level=sl
        )
        
        predict_period = company.prediction_period or 30
        epochs = company.ai_epochs or 50
        
        success, msg = engine.train_model(epochs=epochs, prediction_period=predict_period)
        
        if success:
            return Response({"status": f"AI Engine successfully retrained for {company.name}."})
        else:
            return Response({"error": f"Training skipped: {msg}"}, status=400)

    @action(detail=False, methods=['post'])
    def train_all(self, request):
        """Trigger training for EVERY company (Admin only)."""
        if request.user.role != 'ADMIN':
            return Response({"error": "Forbidden"}, status=403)
        
        from .ai_model import InventoryForecastModel
        companies = self.get_queryset()
        
        success_count = 0
        for company in companies:
            sl = float(company.service_level) if company.service_level else 0.95
            engine = InventoryForecastModel(company_id=company.id, service_level=sl)
            success, _ = engine.train_model(
                epochs=company.ai_epochs or 50, 
                prediction_period=company.prediction_period or 30
            )
            if success:
                success_count += 1
        
        # New: After training, run a global prediction update for all stock floors
        from .ai_model import refresh_all_predictions
        refresh_all_predictions()
                
        return Response({"status": f"Global training cycle completed. {success_count}/{companies.count()} models updated. All stock floors refreshed."})

    # PATCH /api/company-settings/update_settings/
    # OR you can override the 'patch' method for the base URL
    @action(detail=False, methods=['patch'], url_path='update-settings')
    def update_settings(self, request):
        company = self.get_queryset().first()
        if not company:
            return Response({"error": "No company found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Use partial=True to allow the PATCH behavior
        serializer = self.get_serializer(company, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# PRODUKTU UN KATALOGA VADĪBA
# Nodrošina piekļuvi globālajam produktu sarakstam un konkrētā uzņēmuma katalogam.
# Piekļuve tiek filtrēta, lai lietotājs redzētu tikai sava uzņēmuma preces.
class ProductViewSet(viewsets.ModelViewSet):
    """
    Viewset for the global Product identities.
    Accessible to everyone for reading, but restricted for editing.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

class CompanyProductViewSet(viewsets.ModelViewSet):
    """
    Viewset for Company-specific catalog entries (SKU/Price).
    Filters results based on the user's company membership.
    """
    serializer_class = CompanyProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Logic: Only show products belonging to the user's company
        # (Assuming your User model has a 'company' relationship)
        if hasattr(user, 'company') and user.company:
            return CompanyProduct.objects.filter(company=user.company)
        return CompanyProduct.objects.none()

# INVENTĀRA LĪMEŅI UN AI PROGNOZĒŠANA
# Šeit tiek pārvaldīts fiziskais preču daudzums noliktavās.
# 'ai_recommendations' darbība aprēķina ieteicamos krājumu sliekšņus, izmantojot AI modeli.
class WarehouseStockViewSet(viewsets.ModelViewSet):
    """
    Viewset for physical inventory levels in specific warehouses.
    """
    serializer_class = WarehouseStockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return WarehouseStock.objects.none()
        
        # Admins or managers might see more, but for now filtering by company
        if user.company:
            return WarehouseStock.objects.filter(warehouse__company=user.company)
        return WarehouseStock.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        warehouse = serializer.validated_data.get('warehouse')
        
        # If no warehouse provided, use the user's assigned warehouse
        if not warehouse and user.warehouse:
            serializer.save(warehouse=user.warehouse)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def ai_recommendations(self, request):
        """
        AI Hub: Calculates Stock Floor requirements based on company goals.
        Visible to CEO and Managers.
        """
        user = request.user
        if user.role not in ['CEO', 'WAREHOUSE_MANAGER', 'ADMIN']:
             return Response({"error": "Unauthorized"}, status=403)
        
        from .ai_model import predict_floor_for_stock
        
        stocks = self.get_queryset().select_related('company_product__product')
        company = user.company
        
        recommendations = []
        for s in stocks:
             # Basic history mock. In real app this would query daily aggregations.
             history_count = Order.objects.filter(
                 product_listing=s.company_product,
                 status='COMPLETED'
             ).count()
             
             # Call our new TensorFlow model skeleton!
             prediction_floor = predict_floor_for_stock(
                 stock_item=s, 
                 company=company, 
                 historical_data_mock=history_count
             )
             
             # New: Persist the prediction to the DB so other modules can use it
             s.ai_stock_floor = prediction_floor
             s.last_ai_update = timezone.now()
             s.save()
             
             recommendations.append({
                 'stock_id': s.id,
                 'product_name': s.company_product.product.name,
                 'vin': s.company_product.product.vin,
                 'current_quantity': s.quantity,
                 'prediction_floor': prediction_floor,
                 'last_update': s.last_ai_update,
                 'status': 'WARNING' if s.quantity < prediction_floor else 'HEALTHY',
                 'logic_applied': f"TF Pinball (SL: {company.service_level*100:.1f}%) / {company.prediction_period}d",
                 'reason': "Likely stockout risk detected by AI" if s.quantity < prediction_floor else "Sufficient buffer maintained by AI"
             })
             
        return Response(recommendations)

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        queryset = self.get_queryset()
        return export_parts_to_csv(queryset)

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        if request.user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']:
            return Response({"error": "Only management can import parts."}, status=status.HTTP_403_FORBIDDEN)
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No CSV file provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        results = import_parts_from_csv(file_obj, request.user)
        if 'error' in results:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(results)

# PASŪTĪJUMU UN KUSTĪBAS APSTRĀDE
# Galvenais dzinējs pasūtījumu izveidei, apstiprināšanai un pabeigšanai.
# Pasūtījuma pabeigšana automātiski ietekmē krājumu līmeņus datubāzē.
class OrderViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing Orders and internal transfers.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        from .models import Company, Warehouse
        user = self.request.user
        
        # 1. Dev Hygiene: Ensure user has a company/warehouse
        if not user.company:
            user.company, _ = Company.objects.get_or_create(name="Default Company")
            user.save()
        if not user.warehouse:
            user.warehouse, _ = Warehouse.objects.get_or_create(
                company=user.company, 
                name="Main Warehouse"
            )
            user.save()

        # 2. Logic: If no destination warehouse specified, use user's warehouse
        # EXCEPT for CONSUME orders, where the part leaves the system (no destination warehouse)
        order_type = serializer.validated_data.get('order_type')
        to_warehouse = serializer.validated_data.get('to_warehouse')
        
        if order_type == 'CONSUME':
            serializer.save(ordered_by=user)
        elif not to_warehouse:
            serializer.save(ordered_by=user, to_warehouse=user.warehouse)
        else:
            serializer.save(ordered_by=user)
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not hasattr(user, 'company') or not user.company:
            return Order.objects.none()
        
        # All employees can see all orders for their company
        return Order.objects.filter(ordered_by__company=user.company).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        queryset = self.get_queryset()
        return export_orders_to_csv(queryset)

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        if request.user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']:
            return Response({"error": "Permission denied"}, status=403)
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file"}, status=400)
        
        results = import_orders_from_csv(file_obj, request.user)
        return Response(results)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        user = request.user
        MANAGEMENT_ROLES = ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']
        
        # If trying to modify (PUT/PATCH/DELETE)
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Deletion logic
            if request.method == 'DELETE':
                if user.role not in MANAGEMENT_ROLES and obj.ordered_by != user:
                     self.permission_denied(request, message="You can only delete your own orders.")
                if obj.status != 'PENDING':
                    self.permission_denied(request, message="You can only delete pending orders.")
                return

            # Update logic (PUT/PATCH)
            if user.role in MANAGEMENT_ROLES:
                # Even managers shouldn't change core details of a COMPLETED order 
                # to keep paper trail integrity.
                if obj.status in ['COMPLETED', 'REJECTED'] and request.method in ['PUT', 'PATCH']:
                    self.permission_denied(request, message="Cannot modify orders that are already completed or rejected.")
                return
            
            # Mechanics can only modify their own orders
            if obj.ordered_by != user:
                self.permission_denied(request, message="You can only modify your own orders.")
            
            # Can only modify if still PENDING
            if obj.status != 'PENDING':
                self.permission_denied(request, message="You cannot modify an order that is no longer pending.")

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        order = self.get_object()
        if request.user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        if order.status != 'PENDING':
            return Response({"error": "Only pending orders can be approved"}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'APPROVED'
        order.save()
        return Response({"status": "Order approved"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = self.get_object()
        if request.user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        if order.status != 'PENDING':
            return Response({"error": "Only pending orders can be rejected"}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'REJECTED'
        order.save()
        return Response({"status": "Order rejected"})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        user = request.user
        
        is_management = user.role in ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']
        is_own_consumption = (order.order_type == 'CONSUME' and order.ordered_by == user)
        
        if not (is_management or is_own_consumption):
            return Response({"error": "Permission denied. Only managers can complete general orders, or you can complete your own consumption records."}, status=status.HTTP_403_FORBIDDEN)
        
        if order.status != 'APPROVED':
            if order.status == 'PENDING':
                 # Allow direct completion of pending orders if manager wants to skip approval step
                 pass
            else:
                return Response({"error": "Order must be approved (or pending) to be completed"}, status=status.HTTP_400_BAD_REQUEST)
        
        # The actual stock movement logic is in the post_save signal in models.py
        order.status = 'COMPLETED'
        order.save()
        return Response({"status": "Order completed and stock updated"})

    @action(detail=False, methods=['post'])
    def bulk_complete(self, request):
        """Allows management to complete all pending/approved company orders at once."""
        user = request.user
        if user.role not in ['ADMIN', 'WAREHOUSE_MANAGER', 'CEO']:
            return Response({"error": "Permission denied"}, status=403)
        
        orders = Order.objects.filter(
            ordered_by__company=user.company,
            status__in=['PENDING', 'APPROVED']
        )
        
        count = orders.count()
        for order in orders:
            order.status = 'COMPLETED'
            order.save() # Triggers logic in post_save
            
        return Response({"status": f"Successfully completed {count} orders."})

# GLOBĀLAIS TIRGUS
# ViewSet, kas ļauj lietotājiem pārlūkot citu uzņēmumu koplietotās preces.
# 'availability' parāda konkrētu noliktavu krājumus, balstoties uz koplietošanas politiku.
class MarketViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset for the Global Market.
    Shows products that other companies are willing to share/sell.
    """
    serializer_class = CompanyProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated or not user.company:
            return CompanyProduct.objects.none()
            
        # Filter for other companies' products that are shared
        return CompanyProduct.objects.exclude(
            company=user.company
        ).exclude(
            sharing_mode='INTERNAL'
        ).select_related('product', 'company')

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Shows which specific warehouses have this part available
        based on the company's sharing policy.
        """
        product = self.get_object()
        stocks = WarehouseStock.objects.filter(company_product=product)
        
        available_list = []
        for s in stocks:
            qty = 0
            if product.sharing_mode == 'GLOBAL':
                qty = s.quantity
            elif product.sharing_mode == 'WAREHOUSE_LIMIT':
                qty = max(0, s.quantity - product.sharing_value)
            elif product.sharing_mode == 'MARKET_FIXED':
                qty = min(product.sharing_value, s.quantity)
            
            if qty > 0:
                available_list.append({
                    'warehouse_id': s.warehouse.id,
                    'warehouse_name': s.warehouse.name,
                    'location': s.location,
                    'available_quantity': qty
                })
        
        return Response(available_list)