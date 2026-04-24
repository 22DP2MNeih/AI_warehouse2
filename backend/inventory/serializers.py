from rest_framework import serializers
from .models import Product, CompanyProduct, WarehouseStock, Order, Warehouse, Company

# PAMATA DATU SERIĀLIZĀCIJA
# Šie seriālizatori apstrādā pamata informāciju par uzņēmumu, produktiem un noliktavām.
class CompanySettingsSerializer(serializers.ModelSerializer):
    """Config for Company-wide AI stock settings."""
    class Meta:
        model = Company
        fields = ['id', 'name', 'service_level', 'prediction_period', 'ai_epochs', 'ai_update_frequency', 'created_at']
        read_only_fields = ['id', 'created_at'] # Force created_at to be read-only
        
class ProductSerializer(serializers.ModelSerializer):
    """Global product definition including the unique VIN."""
    class Meta:
        model = Product
        fields = ['id', 'name', 'vin', 'description', 'category', 'created_at']

class WarehouseSerializer(serializers.ModelSerializer):
    """Simple serializer for warehouse listings."""
    company_name = serializers.ReadOnlyField(source='company.name')
    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'company', 'company_name', 'address']

class CompanyProductSerializer(serializers.ModelSerializer):
    """Company-specific catalog entry."""
    product_name = serializers.ReadOnlyField(source='product.name')
    product_vin = serializers.ReadOnlyField(source='product.vin')
    company_name = serializers.ReadOnlyField(source='company.name')
    market_quantity = serializers.ReadOnlyField()

    class Meta:
        model = CompanyProduct
        fields = [
            'id', 'company', 'company_name', 'product', 'product_name', 'product_vin',
            'sku', 'price', 'sharing_mode', 'sharing_value', 'market_quantity'
        ]

# INVENTĀRA UN KRĀJUMU APSTRĀDE (Sarežģītā loģika)
# Šis seriālizators ir atbildīgs par fizisko krājumu izveidi.
# Tas izmanto "plakanu" datu struktūru (flat content), ko sūta frontend, un sadala to pa trim tabulām:
# Product (globālā identitāte), CompanyProduct (uzņēmuma katalogs) un WarehouseStock (fiziskais daudzums).
class WarehouseStockSerializer(serializers.ModelSerializer):
    """
    Physical inventory in a specific warehouse.
    Supports 'flat' creation/update for frontend simplicity.
    """
    warehouse_name = serializers.ReadOnlyField(source='warehouse.name')
    product_name = serializers.ReadOnlyField(source='company_product.product.name')
    vin = serializers.ReadOnlyField(source='company_product.product.vin')
    description = serializers.ReadOnlyField(source='company_product.product.description')
    sku = serializers.ReadOnlyField(source='company_product.sku')
    price = serializers.ReadOnlyField(source='company_product.price')
    sharing_mode = serializers.ReadOnlyField(source='company_product.sharing_mode')
    sharing_value = serializers.ReadOnlyField(source='company_product.sharing_value')
    market_quantity = serializers.ReadOnlyField(source='company_product.market_quantity')

    # Writable fields for convenience matching the frontend PartForm
    name = serializers.CharField(write_only=True, required=False)
    vin_input = serializers.CharField(write_only=True, required=True) # VIN is now required for identity
    sku_input = serializers.CharField(write_only=True, required=False)
    price_input = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    description_input = serializers.CharField(write_only=True, required=False)
    sharing_mode_input = serializers.CharField(write_only=True, required=False)
    sharing_value_input = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = WarehouseStock
        fields = [
            'id', 'warehouse_name', 'company_product', 
            'product_name', 'vin', 'description', 'sku', 'price', 
            'sharing_mode', 'sharing_value', 'market_quantity',
            'quantity', 'location', 'ai_stock_floor', 'last_ai_update',
            'name', 'vin_input', 'sku_input', 'price_input', 'description_input',
            'sharing_mode_input', 'sharing_value_input'
        ]
        read_only_fields = ['company_product', 'warehouse']

    # Loģika jauna krājuma ieraksta izveidei.
    # Atkarībā no ievadītā VIN, sistēma vai nu atrod esošu produktu, vai izveido jaunu.
    def create(self, validated_data):
        from .models import Company, Warehouse
        
        # 0. Extract flat data
        name = validated_data.pop('name', 'Unknown Product')
        vin = validated_data.pop('vin_input').upper() # Standardize VIN
        sku = validated_data.pop('sku_input', '')
        price = validated_data.pop('price_input', 0)
        description = validated_data.pop('description_input', '')
        sharing_mode = validated_data.pop('sharing_mode_input', 'INTERNAL')
        sharing_value = validated_data.pop('sharing_value_input', 0)
        
        # Get context
        request = self.context.get('request')
        user = request.user if request else None
        
        # 1. Dev Hygiene: Ensure user has a company/warehouse
        if user and not user.company:
            user.company, _ = Company.objects.get_or_create(name="Default Company")
            user.save()
        if user and not user.warehouse:
            user.warehouse, _ = Warehouse.objects.get_or_create(
                company=user.company, 
                name="Main Warehouse"
            )
            user.save()

        # 2. Get or Create Global Product via VIN (The Unique Identifier)
        product, created = Product.objects.get_or_create(
            vin=vin,
            defaults={
                'name': name,
                'description': description
            }
        )
        
        # 3. Get or Create Company Product (Catalog)
        company = (user.company if user else None)
        if not company:
            raise serializers.ValidationError("User or Item must belong to a company.")
            
        company_product, _ = CompanyProduct.objects.get_or_create(
            company=company,
            product=product,
            defaults={
                'sku': sku, 
                'price': price,
                'sharing_mode': sharing_mode,
                'sharing_value': sharing_value
            }
        )
        
        # 4. Handle Warehouse assignment
        warehouse = validated_data.pop('warehouse', None) or (user.warehouse if user else None)
        if not warehouse:
            raise serializers.ValidationError("Warehouse must be specified or user must be assigned to one.")

        # 5. Create Warehouse Stock
        return WarehouseStock.objects.create(
            company_product=company_product,
            warehouse=warehouse,
            **validated_data
        )

    def update(self, instance, validated_data):
        # Extract flat data
        name = validated_data.pop('name', None)
        vin = validated_data.pop('vin_input', None)
        sku = validated_data.pop('sku_input', None)
        price = validated_data.pop('price_input', None)
        description = validated_data.pop('description_input', None)
        sharing_mode = validated_data.pop('sharing_mode_input', None)
        sharing_value = validated_data.pop('sharing_value_input', None)

        # Handle quantity/location updates
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.location = validated_data.get('location', instance.location)
        
        # Update Catalog Entry
        catalog = instance.company_product
        if sku is not None: catalog.sku = sku
        if price is not None: catalog.price = price
        if sharing_mode is not None: catalog.sharing_mode = sharing_mode
        if sharing_value is not None: catalog.sharing_value = sharing_value
        
        if any(x is not None for x in [sku, price, sharing_mode, sharing_value]):
            catalog.save()

        # Update Global Product
        product = catalog.product
        if vin is not None: product.vin = vin.upper()
        if name is not None: product.name = name
        if description is not None: product.description = description
        
        if any(x is not None for x in [vin, name, description]):
            product.save()
            
        instance.save()
        return instance

# PASŪTĪJUMU SERIĀLIZĀCIJA
# Šis seriālizators parūpējas par pasūtījumu un preču kustības datu validāciju.
# Tiek pārbaudīts, vai ir norādīta pareiza avota un mērķa noliktava.
class OrderSerializer(serializers.ModelSerializer):
    part_name = serializers.SerializerMethodField()
    vin = serializers.ReadOnlyField(source='product_listing.product.vin')
    ordered_by_username = serializers.ReadOnlyField(source='ordered_by.username')
    from_warehouse_name = serializers.ReadOnlyField(source='from_warehouse.name')
    to_warehouse_name = serializers.ReadOnlyField(source='to_warehouse.name')

    class Meta:
        model = Order
        fields = [
            'id', 'order_type', 'status', 'product_listing', 'part_name', 'vin',
            'custom_part_name', 'quantity', 'from_warehouse', 'from_warehouse_name',
            'to_warehouse', 'to_warehouse_name', 'destination_external', 
            'ordered_by', 'ordered_by_username', 'created_at'
        ]
        read_only_fields = ['ordered_by', 'status', 'created_at']

    def validate(self, data):
        dest_ext = data.get('destination_external')
        f_wh = data.get('from_warehouse')
        t_wh = data.get('to_warehouse')

        if dest_ext:
            if not (bool(f_wh) ^ bool(t_wh)):
                raise serializers.ValidationError({
                    "non_field_errors": "External orders require exactly one internal warehouse reference."
                })
        else:
            if not (f_wh and t_wh):
                raise serializers.ValidationError({
                    "non_field_errors": "Internal orders require both source and destination warehouses."
                })
        return data

    def get_part_name(self, obj):
        if obj.product_listing and obj.product_listing.product:
            return obj.product_listing.product.name
        return obj.custom_part_name