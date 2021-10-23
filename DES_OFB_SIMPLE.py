from bitarray import bitarray
import random
import string
from consts import *

# Size of user key and initial vector (must be equal)
KEY_SIZE = 64
VEC_SIZE = 64
# Size of the block of bits (set by user)(must be <= VEC_SIZE)
BLOCK_SIZE = None


# TODO Delete padding? Says here https://www.youtube.com/watch?v=TQsYcCPatjk (tried)
# TODO Try without first bits and left shifting - just pass DES result to the next step (tried)
# TODO Delete mode from DES - run it the same both times - HELPED!!!!!

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
def generate_key(size) -> [int]:
    # Generate a sequence of bits
    key = [random.randint(0, 1) for _ in range(size)]
    return key


# Function generates random initial vector (key)
def generate_vector(size) -> [int]:
    # Generate a sequence of bits
    vec = [random.randint(0, 1) for _ in range(size)]
    return vec


# Function adds padding to the end of text if it's needed
def add_padding(bits) -> [int]:
    global BLOCK_SIZE
    # The number of empty bits to add to the end
    pad_len = BLOCK_SIZE - (len(bits) % BLOCK_SIZE)
    for i in range(pad_len):
        bits.append(0)
    return bits


# Function removes padding from the end of the text (works with strings)
def remove_padding(text) -> str:
    allowed = string.ascii_letters + string.digits + string.whitespace + string.punctuation
    for el in text:
        if el not in allowed:
            return text[:text.index(el)]
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
    # Each character of UTF-8 is limited to 1 byte size in this program
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
    if n > len(bits):
        return [0 for i in bits]
    else:
        return bits[n:] + [0 for _ in range(n)]


# Function splits array into parts of size 'n'
def split(s, n) -> [[int]]:
    blocks = [s[k:k + n] for k in range(0, len(s), n)]
    return blocks


# Function splits array into parts if size 'n' and adds padding if needed
def split_pad(text, num_parts) -> [[int]]:
    # Add padding (if needed)
    text = add_padding(text)
    blocks = [text[k:k + num_parts] for k in range(0, len(text), num_parts)]
    return blocks


# Function creates a list of 48-bit keys generated from 56-bit original key
def transform_key(key) -> [[int]]:
    keys = []
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
def DES(bits, key) -> [int]:
    # Generate keys for all 16 rounds of encoding
    keys = transform_key(key)
    result = []
    # Replace block's bits once
    bits = replace(bits, initial_replace_matrix())
    # Split the block bits in two halfs
    left, right = split(bits, int(VEC_SIZE / 2))
    # 16 rounds of encoding
    for i in range(16):
        # Convert a 32-bit array to 48-bit array
        wide_right = replace(right, expand_matrix())
        tmp = xor(keys[i], wide_right)
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
# First argument 'text' can be either raw or encoded one
def main(text, key, vec, mode):
    global BLOCK_SIZE
    # Convert text to bits to work only with bits arrays
    text = string_to_bits(text)
    # The result - bits of encoded/decoded text
    result = []
    # Split the text to blocks of the same size and add padding if needed
    blocks = split_pad(text, BLOCK_SIZE)
    for block in blocks:
        # Encode initial vector using DES
        # Result is 64 bit array
        vec = DES(vec, key)
        # Get number of first bits
        first_bits = vec[:BLOCK_SIZE]
        # It can be either encoded or decoded block
        processed_block = xor(first_bits, block)
        result += processed_block
        # Just pass the vector to the next iteration...
        # Update the vector: left shift it for 't' bits and put first bits to the end of it
        vec = move_left(vec, BLOCK_SIZE)
        vec[-BLOCK_SIZE:] = first_bits
    # Convert result from bits into string
    str_result = bits_to_string(result)
    # Remove padding if decoding
    if mode == 1:
        str_result = remove_padding(str_result)
    return str_result


# Function encodes the data
def encode(text, key, vec):
    return main(text, key, vec, mode=0)


# Function decodes the data
def decode(text, key, vec):
    return main(text, key, vec, mode=1)


if __name__ == '__main__':
    # Getting a raw user input
    raw_text = input("Enter text to encode: ")
    # Setting size of the block
    BLOCK_SIZE = int(input("Enter block size in bits: "))
    if BLOCK_SIZE > 10_000:
        raise Exception("Please, enter a smaller block size for faster calculations")
    elif BLOCK_SIZE < 8:
        raise Exception("Please, enter a bigger block size")
    # Generating a random key
    user_key = generate_key(KEY_SIZE)
    # Generating a random initial vector
    initial_vector = generate_vector(VEC_SIZE)
    # Encoding / Decoding the text
    encoded_text = encode(raw_text, user_key, initial_vector)
    decoded_text = decode(encoded_text, user_key, initial_vector)
    print(f"Encoded text is: {encoded_text}")
    print(f"Decoded text is: {decoded_text}")