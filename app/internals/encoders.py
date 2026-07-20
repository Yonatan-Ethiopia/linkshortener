import string
import os
from dotenv import load_dotenv

load_dotenv()

xor_mask = os.getenv("SHORTLINK_XOR_MASK", "")

def encode_to_base62( number: int):
    number ^= XOR_MASK
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
    chars = string.digits + string.ascii_letters
    char_map = {char: i for i, char in enumerate(chars)}
    num = 0
    for char in short_string:
        if char not in char_map:
            return None
        num = num * 62 + char_map[char]
    return num ^ XOR_MASK
