import re

## Function to extract Session id , that take inputs the Session String:
def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""


## Function to convert 'key-value' pair of 'food_items' and 'respective quantity' in food_dict to string as value-key
## eg: {'samosa':2,'dosa':3} --> 2 samosa and 3 dosa
def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result


if __name__ == '__main__':
    print(get_str_from_food_dict({"samosa":2,"pav bhaji":3}))