import string
import os
from dotenv import load_dotenv

load_dotenv()

xor_mask = os.getenv("SHORTLINK_XOR_MASK", 0)

def encode_to_base62( number: int):
    number ^= int(xor_mask)
    chars = string.digits + string.ascii_letters
    if number == 0:
        return chars[0]
    base62 = []
    while number > 0:
        print("This is running still")
        number, rem = divmod(number, 62)
        base62.append(chars[rem])
    print("Finished")
    return "".join(reversed(base62))
    
def decode_from_base62( short_string: str):
    if  not short_string.isalnum() or short_string is None:
        return None
    short_string = short_string.strip().lower()
    try:
        chars = string.digits + string.ascii_letters
        char_map = {char: i for i, char in enumerate(chars)}
        num = 0
        for char in short_string:
            if char not in char_map:
                return None
            num = num * 62 + char_map[char]
        return num ^ int(xor_mask)
    except Exception as e:
        print(e)
        return None
    
