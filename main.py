from fastapi import FastAPI
app = FastAPI()
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import helper

## Dictionary to save current orders(entered by user)
inprogress_orders = {}

@app.get('/')
async def root():
    return {'message':'setting up Fast-API Backend'}


@app.post('/')
async def handle_request(request : Request):
    ## The Dialogflow returns a Raw api response:
    ## Retrieveing the JSON Data From the Request:
    payload = await request.json()

    ## Extracting the necessary information from the payload
    ## based on the structure of the WebhookRequest from Dialogflow(the Raw api response)

    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_context = payload['queryResult']['outputContexts']

    ## since output_context ka first element i.e name mai session id stored hai: Vaha se session_id extract karenge using RegEx:
    session_id = helper.extract_session_id(output_context[0]['name'])
    
    ## A MAPPING DICTIONARY WHICH MMAPS INTENTS TO THEIR RESPECTIVE FUNCTION FOR FETCHING ORDERS:
    intent_handler_dict = {
        'order.add - context:ongoing-order': add_to_order,
        'order.remove - context:ongoing-order': remove_from_order,
        'order.complete - context : ongoing-order':complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters,session_id)
    ## intent ke andar displayName mai - kaunsa intent call hua vo stored hai! -> vohi return kar raha hai!


def track_order(parameters:dict,session_id:str):
    order_id = int(parameters['number'])
    ## db_helper se get_order_status function call karke , order_id pass kar rahe hai! -> aur uska status return ho raha hai!
    order_status = db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_Text = f"The order status for order_id  {order_id} is {order_status}"
    else:
        fulfillment_Text = f"No Order found with order id : {order_id}"

    ## Returning the  JSON Response:
    return JSONResponse(content={
        "fulfillmentText": fulfillment_Text
    })



def add_to_order(parameters:dict,session_id:str):
    ## parameters ke andar 'Food-items'me stored hai -> user entered food-itemsand its quantities:
    food_items = parameters['Food-items']
    quantities = parameters['number']

    ## If user enters 2 samosa and vadapav(Didnt mention the quantity for second order , It will raise this error)
    if len(food_items) != len(quantities):
        fulfillmentText  = "Sorry i didnt understand . Can you please specify the items and their Quantities properly?"
    else:

        ## new_food_dict Name ki dictionary me food_item aur uski respective quantity ko save kiya!(converting 2 list 'food_items' and 'quantities' into Single Dictionary using: -> zip() function)
        new_food_dict = dict(zip(food_items,quantities))

        ## if current session_id is in current orders(i.e it already exists) then we have to merge two dictionaries
        if session_id in inprogress_orders:

            ## getting the old food dictionary
            current_food_dict = inprogress_orders[session_id]

            ## merging with new_food_dict using '.update':
            current_food_dict.update(new_food_dict)

            ## returning back the merged dictionary to the inprogress_order with respective session_id
            inprogress_orders[session_id] = current_food_dict

        # inprogress_orders = {
        # User ordered in the first session:

        #    'session_id_1':{'pizza':2,'mangolassi':2}

        # But he forgot to add some food items  in the first go so, he said ohh "add 3          samosas" , this will create new dictionary and we need to append both the dictionaries for complete order

        #    'session_id_1':{''samosa':3}

        # }


        ## if current session_id is not in current orders(i.e it dosent exists) then we add the new_food_dict with the respective session_id to inprogress_orders
        else:
            inprogress_orders[session_id] = new_food_dict

        print('***********************')

        print(inprogress_orders)

        ## Getting the order as String , from dictionary
        order_str = helper.get_str_from_food_dict(inprogress_orders[session_id])

        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })



## to Hnadle complete order Request
def complete_order(parameters:dict,session_id:str):

    ## checking if the order is made properly and the respective session_id is in inprogress_orders:
    ## if not:
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    ## if it is:
    else:
        ## Storing the order:
        order = inprogress_orders[session_id]

        ## Calling the function save_to_db that takes input the orders:and returns order_id
        order_id = save_to_db(order)

        ##
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


## Function to store theorder ordered by user as new row into the database:
def save_to_db(order: dict):

    ## getting new_order_id for the order
    next_order_id = db_helper.get_next_order_id()

    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():

        ## calling function insert_order_item from db_helper which calls the Stored_procedure: passing the 3 inputs(required by the function)
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    # Now insert order tracking status of current order:
    db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id

def remove_from_order(parameters: dict, session_id: str):
     
    ## Checking if the repective session id is present in inprogress_orders:
    ## if not:
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            'fullfillmentText':"I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })
    ## Fetching the food_items list
    food_items = parameters['food-items']
    ## tracking the current order:
    current_order = inprogress_orders[session_id]
    print(current_order)

    removed_items = []
    no_such_items = []

    ## Iterating through all the food items that are ordered:
    for item in food_items:
        ## If the requested item that is to be removed is not in current order , we will append that item to no_such_items
        if item not in current_order:
            no_such_items.append(item)

        ## If the requested item that is to be removed is in current order , we will append that item removed_items and delete it from current_order:
        else:
            removed_items.append(item)
            del current_order[item]


    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'       

    if len(current_order.keys()) == 0:
        fulfillment_text += "your order is Empty!"
    else:
        
        food_str = helper.get_str_from_food_dict(current_order)
        fulfillment_text += f"Here is what is Left in your Current Order: {food_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
