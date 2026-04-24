import csv
import io
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from .models import Product, CompanyProduct, WarehouseStock, Order, Warehouse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

# DATU EKSPORTĒŠANA UZ CSV
# Šī funkcija ģenerē CSV failu ar visiem uzņēmuma pasūtījumiem.
def export_orders_to_csv(queryset):
    """
    Exports a queryset of Orders to a CSV response.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Type', 'Status', 'Part Name', 'VIN', 'Quantity', 
        'From Warehouse', 'To Warehouse', 'Destination External', 
        'Ordered By', 'Created At'
    ])
    
    for order in queryset:
        part_name = order.product_listing.product.name if order.product_listing else order.custom_part_name
        vin = order.product_listing.product.vin if order.product_listing else 'N/A'
        
        writer.writerow([
            order.id,
            order.get_order_type_display(),
            order.get_status_display(),
            part_name,
            vin,
            order.quantity,
            order.from_warehouse.name if order.from_warehouse else 'N/A',
            order.to_warehouse.name if order.to_warehouse else 'N/A',
            order.destination_external or 'N/A',
            order.ordered_by.username,
            order.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="company_orders.csv"'
    return response

# DATU IMPORTĒŠANA NO CSV (Detaļas)
# Funkcija ļauj masveidā pievienot jaunas detaļas noliktavā no CSV faila.
# Tiek automātiski izveidoti Product, CompanyProduct un WarehouseStock ieraksti.
def import_parts_from_csv(file_obj, user):
    """
    Imports parts from a CSV file.
    Expected format: name, vin, sku, quantity, price, location, description
    """
    decoded_file = file_obj.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)
    
    results = {
        'created': 0,
        'updated': 0,
        'errors': []
    }
    
    if not user.company or not user.warehouse:
        return {'error': 'User must have an assigned company and warehouse to import parts.'}

    for row in reader:
        try:
            name = row.get('name', 'Unknown Part').strip()
            vin = row.get('vin', '').strip().upper()
            sku = row.get('sku', '').strip()
            quantity = int(row.get('quantity', 0))
            price = float(row.get('price', 0.0))
            location = row.get('location', 'UNASSIGNED').strip()
            description = row.get('description', '').strip()

            if not vin or len(vin) != 17:
                results['errors'].append(f"Invalid VIN for part {name}: {vin}")
                continue

            # 1. Product (Identity)
            product, p_created = Product.objects.get_or_create(
                vin=vin,
                defaults={'name': name, 'description': description}
            )

            # 2. CompanyProduct (Catalog)
            company_product, cp_created = CompanyProduct.objects.get_or_create(
                company=user.company,
                product=product,
                defaults={'sku': sku, 'price': price}
            )

            # 3. WarehouseStock (Inventory)
            stock, s_created = WarehouseStock.objects.get_or_create(
                warehouse=user.warehouse,
                company_product=company_product,
                defaults={'quantity': quantity, 'location': location}
            )

            if not s_created:
                stock.quantity += quantity
                stock.save()
                results['updated'] += 1
            else:
                results['created'] += 1

        except Exception as e:
            results['errors'].append(f"Row error: {str(e)}")
            
    return results

def export_parts_to_csv(queryset):
    """
    Exports a queryset of WarehouseStock (Parts) to a CSV response.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Name', 'VIN', 'SKU', 'Quantity', 'Price', 'Location', 'Warehouse'])
    
    for stock in queryset:
        writer.writerow([
            stock.company_product.product.name,
            stock.company_product.product.vin,
            stock.company_product.sku,
            stock.quantity,
            stock.company_product.price,
            stock.location,
            stock.warehouse.name
        ])
    
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="warehouse_inventory.csv"'
    return response

from django.db import transaction

# VĒSTURISKO PASŪTĪJUMU IMPORTS (AI Apmācībai)
# Ļauj augšupielādēt vēsturiskos datus, lai AI modelis varētu mācīties no pagātnes patēriņa.
# Šie pasūtījumi tiek atzīmēti kā 'is_historical', lai tie neietekmētu pašreizējo krājumu daudzumu.
def import_orders_from_csv(file_obj, user):
    """
    Imports historical orders from a CSV file.
    Expected format: order_type, vin, quantity, from_warehouse, to_warehouse, status, destination_external
    """
    decoded_file = file_obj.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)
    
    results = {'created': 0, 'errors': []}
    
    for row in reader:
        try:
            with transaction.atomic():
                order_type = row.get('order_type', 'SALE').upper()
                vin = row.get('vin', '').strip().upper()
                quantity = int(row.get('quantity', 1))
                from_warehouse_name = row.get('from_warehouse', '').strip()
                to_warehouse_name = row.get('to_warehouse', '').strip()
                status_code = row.get('status', 'COMPLETED').upper()
                dest_ext = row.get('destination_external', '').strip()
                date_str = row.get('date', '').strip()
                
                is_historical = False
                created_at = timezone.now()

                if date_str:
                    parsed_dt = parse_datetime(date_str)
                    if parsed_dt:
                        if timezone.is_naive(parsed_dt):
                            created_at = timezone.make_aware(parsed_dt)
                        else:
                            created_at = parsed_dt
                        
                        # If it's a completed past record, mark as historical to skip stock processing
                        if status_code == 'COMPLETED':
                            is_historical = True

                # 1. Lookup Product
                product = Product.objects.filter(vin=vin).first()
                if not product:
                    results['errors'].append(f"Product with VIN {vin} not found.")
                    continue
                
                # 2. Lookup CompanyProduct (Catalog)
                listing = CompanyProduct.objects.filter(company=user.company, product=product).first()
                if not listing:
                    results['errors'].append(f"Product {vin} not in company catalog.")
                    continue

                # 3. Lookup Warehouses
                from_w = Warehouse.objects.filter(company=user.company, name=from_warehouse_name).first() if from_warehouse_name else None
                to_w = Warehouse.objects.filter(company=user.company, name=to_warehouse_name).first() if to_warehouse_name else None

                # 4. Create Order
                order = Order.objects.create(
                    order_type=order_type,
                    status=status_code,
                    product_listing=listing,
                    quantity=quantity,
                    from_warehouse=from_w,
                    to_warehouse=to_w,
                    destination_external=dest_ext,
                    ordered_by=user,
                    is_historical=is_historical,
                    created_at=created_at
                )
                results['created'] += 1

        except Exception as e:
            results['errors'].append(f"Row error: {str(e)}")
            
    return results
