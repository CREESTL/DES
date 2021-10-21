from bitarray import bitarray
import random
import string
from consts import *


# TODO Make an odd block size work!

# Size of the block of bits (set by user)
BLOCK_SIZE = None


# Function converts value into a string of bits of a given size
def to_bits(val, size) -> str:
    # If value is an integer - convert it to bin and cut the '0b' part
    if isinstance(val, int):
        bits = bin(val)[2:]
    # If value is a string - convert it to int first, then convert to bin and cut the '0b' part
    else:
        bits = bin(ord(val))[2:]
    # Add empty bits to fit the size
    while len(bits) < size:
        bits = "0" + bits
    return bits


# Function generates random key
def generate_key() -> str:
    # Generate a sequence of characters and numbers
    key = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(8))
    return key


# Function generates random initial vector (key)
def generate_vector() -> [int]:
    # Generate a sequence of bits
    vec = [random.randint(0, 1) for _ in range(64)]
    return vec


# Function adds padding to the end of the text is length of text is not multiple of BLOCK_SIZE
def add_padding(text) -> str:
    pad_len = BLOCK_SIZE - (len(text) % BLOCK_SIZE)
    text += pad_len * chr(pad_len)
    return text


# Function removes padding from the end of the text
def remove_padding(text) -> str:
    pad_len = ord(text[-1])
    text = text[:-pad_len]
    return text


# Function converts a string into an array of bits
def string_to_bits(text) -> [int]:
    array = []
    for char in text:
        # Each character is converted to 8 bits (string)
        bits = to_bits(char, 8)
        # Have to raise Exception here. The reason is:
        # In UTF-8 characters might have 1-4 bytes size. So if a user wants to decode a string containing characters of
        # different sizes, the program will not manage to separate a large array of bits into parts for each character.
        # That's why user should only use UTF-8 characters of one size for the program to work correctly. That size
        # is 8 bits by default.
        if len(bits) > 8:
            raise Exception("Please use only UTF-8 characters of size of under 1 byte!")
        # String is converted into array of integers
        array.extend([int(x) for x in list(bits)])
    return array


# Function converts array of bits into a string
def bits_to_string(array):
    _bytes = split(array, 8)
    res = ''
    for byte in _bytes:
        str_byte = ''
        for bit in byte:
            str_byte += str(bit)
        res += chr(int(str_byte, 2))
    return res


# Function replaces bits of the block according to the matrix
def replace(block, matrix) -> [int]:
    return [block[x - 1] for x in matrix]


# Function moves bits to the left for several positions
def move_left(bits, n) -> [int]:
    return bits[n:] + bits[:n]


# Function creates a list of 48-bit keys generated from 56-bit original key
def transform_key(key) -> [[int]]:
    keys = []
    key = string_to_bits(key)
    # Replace bits of the key once
    key = replace(key, key_prepare_matrix())
    # Split the key in 2 parts
    right, left = split(key, 28)
    shifts = shifts_array()
    # Apply 16 rounds of encoding
    for i in range(16):
        # Do bit shift for both parts (1 or 2 bits)
        right = move_left(right, shifts[i])
        left = move_left(left, shifts[i])
        # Merge both parts again
        tmp = right + left
        # Replace bits of the key the second time
        keys.append(replace(tmp, key_finish_matrix()))
    return keys


# Function splits array into parts of size 'n'
def split(s, n) -> [[int]]:
    blocks = [s[k:k + n] for k in range(0, len(s), n)]
    return blocks


# Function applies the XOR operation between to arrays of bits
def xor(bits_1, bits_2) -> [int]:
    return [x ^ y for x, y in zip(bits_1, bits_2)]


# Function replaces bits according to S boxes
def substitute(part) -> [int]:
    # A 48-bit part is separated into 8 6-bit blocks
    blocks = split(part, 6)
    result = []
    # Array of s_boxes
    s = s_boxes()
    for i in range(len(blocks)):
        block = blocks[i]
        # Get the row and the column number from the block
        row = int(str(block[0]) + str(block[5]), 2)
        column = int(''.join([str(x) for x in block[1:][:-1]]), 2)
        # Get the value with these row and column numbers
        val = s[i][row][column]
        # Convert it to binary
        bits = to_bits(val, 4)
        # Append it to the result list
        result += [int(x) for x in bits]
    return result


# Function encodes array of bits using DES algorithm
def DES(bits, key, mode) -> [int]:
    # Generate keys for all 16 rounds of encoding
    keys = transform_key(key)
    result = []
    # Replace block's bits once
    bits = replace(bits, initial_replace_matrix())
    # Split the block bits in two halfs
    left, right = split(bits, int(len(bits) / 2))
    # 16 rounds of encoding
    for i in range(16):
        # Convert a 32-bit array to 48-bit array
        wide_right = replace(right, expand_matrix())
        # If encoding - use key according to iteration number
        if mode == 0:
            tmp = xor(keys[i], wide_right)
        # If decoding - start with the last key
        elif mode == 1:
            tmp = xor(keys[15 - i], wide_right)
        # Replace bits according to s_boxes
        tmp = substitute(tmp)
        # Replace bits according to the matrix
        tmp = replace(tmp, replace_p_matrix())
        # Apply the XOR operation to the bits
        tmp = xor(left, tmp)
        # Change halfs' places
        left = right
        right = tmp
        # Replace block's bits the second time
        result += replace(right + left, final_p_matrix())
    return result


# Main encoding/decoding function
def main(text, key, vec, mode):
    # Convert text and key to bits to work only with bits arrays
    text = string_to_bits(text)
    key = string_to_bits(key)
    # If there are less bits in the text then bits in the block of desired size - cut the block size and alert user
    print(f'Your desired block size {BLOCK_SIZE} has been reduced to {len(text)} - the number of bits in the text!')
    # The result - bits of encoded text
    result = []
    # Split the text to blocks of the same size
    blocks = split(text, BLOCK_SIZE)
    for block in blocks:
        # Encode initial vector using DES
        vec = DES(vec, key, mode)
        # Get number of first bits
        first_bits = vec[:BLOCK_SIZE]
        # XOR between text bits block and these first bits
        encoded_block = xor(first_bits, block)
        # Update the vector (place the first bits to the end of it)
        vec[-len(encoded_block):] = first_bits
        # Add encoded block to the result
        result += encoded_block
    # Convert result into string
    str_result = bits_to_string(result)
    return str_result


# Function encodes the data
def encode(text, key, vec):
    return main(text, key, vec, mode=0)


# Function decodes the data
def decode(text, key, vec):
    return main(text, key, vec, mode=1)


if __name__ == '__main__':
    # Generating a random key
    user_key = generate_key()
    # Generating a random initial vector
    initial_vector = generate_vector()
    # Getting a raw user input
    raw_text = input("Enter text to encode: ")
    # Setting size of the block
    BLOCK_SIZE = int(input("Enter block size in bits: "))
    # TODO Make an odd block size work as well (even size works every time)
    if BLOCK_SIZE % 2 != 0:
        raise Exception("Block size must be an even number!")
    print(f"Generated key is: {user_key}")
    # Encoding / Decoding the text
    encoded_text = encode(raw_text, user_key, initial_vector)
    #decoded_text = decode(encoded_text, user_key, initial_vector)
    print(f"Encoded text is: {encoded_text}")
    #print(f"Decoded text is: {decoded_text}")

