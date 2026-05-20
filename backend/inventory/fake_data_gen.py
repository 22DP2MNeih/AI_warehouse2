import random
from datetime import datetime, timedelta

def generate_ai_training_data(num_orders):
    """
    Generates SQL INSERT statements for inventory_order table for AI training data.
    """
    sql_statements = []
    
    # Define fixed values as per your request
    ordered_by_id = 2
    from_warehouse_id = 3
    order_type = "CONSUME"
    status = "COMPLETED"
    is_historical = 1

    for i in range(num_orders):
        # Calculate product_listing_id: 10 to 250 step 10
        product_listing_id = random.randrange(9, 251, 10)
        
        # Generate a slightly varied quantity
        quantity = random.randint(1, 500)
        
        # Generate current timestamp
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Construct the INSERT statement
        sql = (
            f"INSERT INTO inventory_order (quantity, status, ordered_by_id, from_warehouse_id, order_type, product_listing_id, created_at, is_historical) VALUES "
            f"({quantity}, '{status}', {ordered_by_id}, {from_warehouse_id}, '{order_type}', {product_listing_id}, '{created_at}', '{is_historical}');"
        )
        sql_statements.append(sql)
        
    return "\n".join(sql_statements)

# --- Generation ---
# Let's generate 100 orders for this example
num_orders_to_generate = 100
generated_sql = generate_ai_training_data(num_orders_to_generate)

print(generated_sql)