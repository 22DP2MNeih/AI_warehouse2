import random
from datetime import datetime, timedelta

def generate_ai_training_data(num_orders, days_back):
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

    now = datetime.now()

    for i in range(num_orders):
        # Calculate product_listing_id: 10 to 250 step 10
        product_listing_id = random.randrange(9, 251, 10)
        
        # Generate a slightly varied quantity
        quantity = random.randint(1, 150)
        
        # Calculate a random time delta between now and 'days_back' ago
        # We calculate a random number of seconds to subtract from 'now'
        time_delta_seconds = random.randint(0, days_back * 24 * 60 * 60)
        random_time = now - timedelta(seconds=time_delta_seconds + 8 * 24 * 60 * 60)
        
        # Format the timestamp
        created_at = random_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Construct the INSERT statement
        sql = (
            f"INSERT INTO inventory_order (quantity, status, ordered_by_id, from_warehouse_id, order_type, product_listing_id, created_at, is_historical) VALUES "
            f"({quantity}, '{status}', {ordered_by_id}, {from_warehouse_id}, '{order_type}', {product_listing_id}, '{created_at}', '{is_historical}');"
        )
        sql_statements.append(sql)
        
    return "\n".join(sql_statements)

# --- Generation ---
# Let's generate 100 orders for this example
num_orders_to_generate = 30
generated_sql = generate_ai_training_data(num_orders_to_generate, 20)

print(generated_sql)