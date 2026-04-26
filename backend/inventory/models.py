from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone

# ORGANIZĀCIJAS STRUKTŪRA
# Uzņēmuma un noliktavu modeļi, kas definē sistēmas hierarhiju.
class Company(models.Model):
    STRATEGY_CHOICES = (
        ('CUSTOMER_FRIENDLY', 'Customer Friendly (Max Availability)'),
        ('COST_EFFICIENT', 'Cost Efficient (Minimum Stock)'),
    )

    name = models.CharField(max_length=255)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    
    # AI Settings
    service_level = models.DecimalField(max_digits=3, decimal_places=3, null=True, blank=True)
    prediction_period = models.IntegerField(default=30, help_text="Number of days to predict stock floor for")
    
    # AI Training Parameters (Admin only tuning)
    ai_epochs = models.IntegerField(default=50)
    ai_update_frequency = models.IntegerField(default=24, help_text="Update frequency in hours")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

# PRODUKTU KATALOGS
# Sistēma nošķir produkta "identitāti" (Product) no uzņēmuma specifiskā "kataloga ieraksta" (CompanyProduct).
# Tas ļauj vienai precei (ar to pašu VIN) piederēt dažādiem uzņēmumiem ar dažādām cenām.
class Product(models.Model):
    """
    The 'Identity' table. 
    Defines what the item IS, regardless of who owns it or where it is.
    """
    name = models.CharField(max_length=255)
    
    # VIN Implementation
    # Standard VINs are 17 characters and exclude I, O, and Q.
    vin = models.CharField(
        max_length=17,
        unique=True,
        help_text="17-character unique Vehicle Identification Number",
        validators=[
            MinLengthValidator(17),
            RegexValidator(
                regex=r'^[A-HJ-NPR-Z0-9]{17}$',
                message='VIN must be 17 alphanumeric characters and exclude I, O, and Q.'
            )
        ]
    )
    
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.vin})"
    
    def save(self, *args, **kwargs):
        # Logic: Always normalize VIN to uppercase before saving
        self.vin = self.vin.upper()
        super().save(*args, **kwargs)

class CompanyProduct(models.Model):
    """
    The 'Catalog' table.
    Links a Product to a Company and assigns business-specific data (SKU, Price).
    Now includes Sharing Policies for the Global Market.
    """
    SHARING_CHOICES = (
        ('INTERNAL', 'Internal Only (Private)'),
        ('WAREHOUSE_LIMIT', 'Warehouse Buffer (Share surplus)'),
        ('AI_BUFFER', 'AI Predicted Buffer (Auto-share surplus)'),
        ('MARKET_FIXED', 'Fixed Quantity (Share specific amount)'),
        ('GLOBAL', 'All Shared (Public)'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='catalog')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='company_listings')
    sku = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Sharing Policy
    sharing_mode = models.CharField(max_length=20, choices=SHARING_CHOICES, default='INTERNAL')
    sharing_value = models.IntegerField(default=0, help_text="Limit or Fixed amount depending on mode")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'sku'], name='unique_sku_per_company'),
            models.UniqueConstraint(fields=['company', 'product'], name='unique_product_per_company')
        ]

    @property
    def total_quantity(self):
        return sum(stock.quantity for stock in self.inventory.all())

    @property
    def market_quantity(self):
        """
        Calculates how much of this product is visible to the Global Market
        based on the company's sharing policy.
        """
        stocks = self.inventory.all()
        total = sum(s.quantity for s in stocks)

        if self.sharing_mode == 'INTERNAL':
            return 0
        elif self.sharing_mode == 'GLOBAL':
            return total
        elif self.sharing_mode == 'WAREHOUSE_LIMIT':
            # Share everything above the buffer limit PER warehouse
            return sum(max(0, s.quantity - self.sharing_value) for s in stocks)
        elif self.sharing_mode == 'AI_BUFFER':
            # Share everything above the AI calculated floor PER warehouse
            return sum(max(0, s.quantity - s.ai_stock_floor) for s in stocks)
        elif self.sharing_mode == 'MARKET_FIXED':
            # Share up to a fixed amount, but not more than we actually have
            return min(self.sharing_value, total)
        return 0

    def __str__(self):
        return f"{self.sku} - {self.product.name} ({self.company.name})"

# FIZISKAIS INVENTĀRS
# Šī tabula izseko konkrētas preces daudzumu konkrētā noliktavā.
# Šeit tiek glabātas arī AI aprēķinātās vērtības par nepieciešamajiem krājumu sliekšņiem.
class WarehouseStock(models.Model):
    """
    The 'Inventory' table.
    Tracks physical quantity of a CompanyProduct in a specific Warehouse.
    """
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock')
    company_product = models.ForeignKey(CompanyProduct, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0)
    location = models.CharField(max_length=100, help_text="Shelf/Bin (e.g., A1-B2)")
    
    # AI Stats (Persisted per part)
    ai_stock_floor = models.IntegerField(default=0)
    last_ai_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['warehouse', 'company_product'], name='unique_stock_per_warehouse')
        ]

    def clean(self):
        # Integrity Check: Ensure warehouse belongs to the same company as the product listing
        if self.warehouse.company != self.company_product.company:
            raise ValidationError("Warehouse and Product Company mismatch.")

    def __str__(self):
        return f"{self.company_product.product.name} in {self.warehouse.name}: {self.quantity}"
    
    # NEW: Warehouse-specific price. If null, we use the CompanyProduct price.
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Overwrites company price for this specific warehouse."
    )

    def get_effective_price(self):
        """
        Returns the warehouse-specific price if set, 
        otherwise falls back to the company-level price.
        """
        return self.price if self.price is not None else self.company_product.price

# DARĪJUMI UN KUSTĪBA
# Visas inventāra izmaiņas tiek reģistrētas caur pasūtījumiem (SALE, TRANSFER, CONSUME u.c.).
# Tas nodrošina pilnu auditācijas pēdu par katru preces kustību.
class Order(models.Model):
    ORDER_TYPES = (
        ('SALE', 'Sale to Customer'),
        ('TRANSFER', 'Internal Warehouse Transfer'),
        ('PURCHASE', 'Purchase/Restock'),
        ('ADJUSTMENT', 'Manual Adjustment/Loss'),
        ('CONSUME', 'Consumed for Repair'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    )

    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='SALE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    product_listing = models.ForeignKey(
        'CompanyProduct', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='orders'
    )
    custom_part_name = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    
    from_warehouse = models.ForeignKey(
        'Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_orders'
    )
    to_warehouse = models.ForeignKey(
        'Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_orders'
    )

    # NEW FIELD
    destination_external = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Name of external source/destination if not an internal warehouse transfer."
    )
    
    ordered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_historical = models.BooleanField(default=False, help_text="Used for AI training only, skips stock updates.")
    created_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        """
        Custom validation logic:
        1. If destination_external is set: Exactly one of (from_warehouse, to_warehouse) must be set.
        2. If destination_external is null: Both (from_warehouse, to_warehouse) must be set.
        """
        super().clean()
        
        has_external = bool(self.destination_external)
        has_from = bool(self.from_warehouse)
        has_to = bool(self.to_warehouse)

        if has_external:
            # XOR logic: Must have from OR to, but not both or none.
            if not (has_from ^ has_to):
                raise ValidationError(
                    "When an external destination is provided, you must specify exactly one internal warehouse (either source or destination)."
                )
        else:
            # Internal logic: Must have both.
            if not (has_from and has_to):
                raise ValidationError(
                    "For internal transfers without an external destination, both 'from' and 'to' warehouses are required."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class StockTransaction(models.Model):
    """
    Audit Ledger linked to the new WarehouseStock model.
    """
    warehouse_stock = models.ForeignKey(
        'inventory.WarehouseStock', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='stock_logs')
    # warehouse_stock = models.ForeignKey(WarehouseStock, on_delete=models.CASCADE)
    change_amount = models.IntegerField() 
    timestamp = models.DateTimeField(auto_now_add=True)

from django.db.models import F

# TRANSAKCIJU LOĢIKA (ACID)
# Šis signāls tiek izpildīts ikreiz, kad pasūtījums tiek atzīmēts kā pabeigts.
# Tiek izmantots 'select_for_update', lai novērstu vienlaicīgu datu labošanas kļūdas (race conditions).
@receiver(post_save, sender=Order)
def process_order_completion(sender, instance, created, **kwargs):
    """
    Transactional logic to move stock. 
    Uses row-level locking (select_for_update) to ensure ACID compliance.
    """
    # Historical logs are for AI only and should NOT affect current stock
    if instance.is_historical:
        return

    if instance.status == 'COMPLETED' and not instance.stock_logs.exists():
        if not instance.product_listing:
            return

        try:
            with transaction.atomic():
                # 1. Handle Source (Deduction)
                if instance.from_warehouse:
                    # select_for_update() locks the row until the transaction ends
                    source_stock = WarehouseStock.objects.select_for_update().get(
                        warehouse=instance.from_warehouse,
                        company_product=instance.product_listing
                    )
                    
                    if source_stock.quantity < instance.quantity:
                        raise ValidationError(f"Insufficient stock in {instance.from_warehouse.name}")

                    # Use F expression to avoid race conditions (Atomicity/Isolation)
                    source_stock.quantity = F('quantity') - instance.quantity
                    source_stock.save()
                    
                    StockTransaction.objects.create(
                        order=instance, 
                        warehouse_stock=source_stock, 
                        change_amount=-instance.quantity
                    )

                # 2. Handle Destination (Addition)
                if instance.to_warehouse:
                    dest_stock, created = WarehouseStock.objects.select_for_update().get_or_create(
                        warehouse=instance.to_warehouse,
                        company_product=instance.product_listing,
                        defaults={'location': 'UNASSIGNED', 'quantity': 0}
                    )
                    
                    dest_stock.quantity = F('quantity') + instance.quantity
                    dest_stock.save()

                    StockTransaction.objects.create(
                        order=instance, 
                        warehouse_stock=dest_stock, 
                        change_amount=instance.quantity
                    )
        except (WarehouseStock.DoesNotExist, ValidationError) as e:
            # In a real product, we'd log this and potentially revert the status
            # For school, we'll let it fail or handle gracefully
            print(f"Transaction failed: {e}")
            # Reset status to PENDING using update() to avoid triggering post_save signal again
            Order.objects.filter(pk=instance.pk).update(status='PENDING')