import mysql.connector
global db

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Meet1234@",
    database="pandeyji_eatery"
)


## A function that takes input -> order_id and Returns its Delivery Status:
def get_order_status(order_id):
    ## Cursor -> For executing query
    cursor = db.cursor()

    # Executing the SQL query to fetch the order status
    query = f"SELECT status FROM order_tracking WHERE order_id = {order_id}"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()

    # Closing the cursor
    cursor.close()

    # Returning the order status
    if result:
        return result[0]
    else:
        return None
    

# Function to get the next available order_id
def get_next_order_id():
    cursor = db.cursor()

    # Executing the SQL query to get the next available order_id
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()


    # id no order_is is present it will return 1:
    if result is None:
        return 1
    # else it will return current order_id + 1(new_order_id)
    else:
        return result + 1
    

# Function to call the MySQL stored procedure and insert an order item - The stored procedure in MySQL Takes three inputs - Food_item,Quantity and Order_id , Therefore the Functions also needs to have 3 inputs:
def insert_order_item(food_item, quantity, order_id):
    try:

        # cursor for executing query:
        cursor = db.cursor()

        # Calling the stored procedure using call_proc
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        # Committing the changes into Database:
        db.commit()

        # Closing the cursor
        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        ## printing the error:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        db.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        # Rollback changes if necessary
        db.rollback()

        return -1
    

# Function to insert a record into the order_tracking table
def insert_order_tracking(order_id, status):
    cursor = db.cursor()

    # Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"

    # execute the query and pass the 2 fields:
    cursor.execute(insert_query, (order_id, status))

    # Committing the changes
    db.commit()

    # Closing the cursor
    cursor.close()

def get_total_order_price(order_id):
    cursor = db.cursor()

    # Executing the SQL query to get the total order price - calling the get_total_order_price function: That taked the order_id as input and returns the total bill
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    return result