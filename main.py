from consts import *
from bitarray import bitarray
import random

"""
1) Convert text to bytes
2) Separate bytes into 8-byte blocks
3) Replace each 8-byte block's bits
4) Separate each block's bits in 2 parts 
5) Encode those parts for 16 iterations
6) Сoncatenate two parts in one block back again 
7) Replace block's bits ones again
8) Done
"""


# Function generates 6-byte (48-bit) key used for encoding
def generate_key():
    key = bitarray()
    for i in range(48):
        # Includes right border (255)
        key.append(random.randint(0, 255))
    return key


# If it's needed the function adds empty bytes ar the end of the string to make it the size that
# can be divided by 8 (bytes)
def preprocess(text_bytes):
    b_ar = bytearray(text_bytes)
    while len(b_ar) % 8 != 0:
        b_ar.append(0)
    return bytes(b_ar)


# Function splits encoded text into 8-byte blocks
# If there is not enough characters to form another 8-byte block
# empty 0x0 bytes are added to the end of the block
def text_to_blocks(text_bytes):
    blocks = []
    start = 0
    end = 8
    # If text is less than 8 bytes we still have to add it
    blocks.append(text_bytes[start:end])
    while end < len(text_bytes):
        start = end
        end += 8
        block = text_bytes[start:end]
        blocks.append(block)
    return blocks


# Function converts 8-byte block into bits (bitarray)
# Returns bitarray - not simple list
def to_bits(block):
    bits = bitarray()
    bits.frombytes(block)
    return bits


# Function replaces bits of a 8-byte block
def initial_replace_block(block):
    matrix = initial_replace_matrix()
    block_bits = to_bits(block)
    line_length = len(matrix[0])
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            old_index = line_length * row_num + col_num
            # Original matrix is created for arrays with indexing starting with 1 - no 0
            # So we have to decrease each value from the matrix by one
            new_index = el - 1
            block_bits[new_index], block_bits[old_index] = block_bits[old_index], block_bits[new_index]
    new_block = block_bits.tobytes()
    return new_block


# Function replaces bits of all blocks in the text
def initial_replace_blocks(text_blocks):
    new_text_blocks = []
    for block in text_blocks:
        new_block = initial_replace_block(block)
        new_text_blocks.append(new_block)
    return new_text_blocks


# Function extracts left half of bits
def left_half(bits):
    left = bitarray()
    start = 0
    end = 4
    part = bits[start:end]
    left += part
    while end < (len(bits) - 4):
        start = end + 4
        end = end + 8
        part = bits[start:end]
        left += part
    return left


# Function extracts right half of bits
def right_half(bits):
    right = bitarray()
    start = 4
    end = 8
    part = bits[start:end]
    right += part
    # Final value of end must be last index + 1
    while end < len(bits):
        start = end + 4
        end = end + 8
        part = bits[start:end]
        right += part
    return right


# Function separates block bits into 2 parts
# Part 1 - left half of matrix of 64 bits
# Part 2 - right half of matrix of 64 bits
def separate(bits):
    # left, right - both are bitarrays
    left = left_half(bits)
    right = right_half(bits)
    return left, right


# Function converts 32-bit bitarray into 48-bit bitarray
def wide(half):
    matrix = wide_matrix()
    # Actually this is not a matrix but rather a 1D array - easier to work with
    new_matrix = bitarray()
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            # Each element of wide-matrix represents the index of the element of the original
            # matrix. Wide-matrix itself stays untouched
            index_to_take_from = el
            # Take the element with that index from the original matrix and put it to the new matrix
            new_matrix.append(half[index_to_take_from])
    # Now this is a bitarray of length 48 formed from a 32-bit bitarray
    return new_matrix


# Function for XOR operation between the key and other bits
def XOR(bits, key):
    res = bitarray()
    for bit1 in bits:
        for bit2 in key:
            res_bit = bit1 ^ bit2
            res.append(res_bit)
    return res


# Function splits 48-bit bitarray into 8 blocks 6 bits each
def bits_to_blocks(bits):
    # An array of bitarrays
    blocks = []
    start = 0
    end = 7
    block = bits[start:end]
    blocks.append(block)
    while end < len(bits):
        start = end
        end += 6
        block = bits[start:end]
        blocks.append(block)
    return blocks


# Function encodes a 32-bit half of a block
def encode_part(bits, key):
    # First we have to convert 32-bit half into 48-bit one
    bits = wide(bits)
    # Do the bits XOR key operation
    bits = XOR(bits, key)
    # Separate bits into 8 blocks 6 bits each
    bit_blocks = bits_to_blocks(bits)


# Function does the following things:
# - Separate each block's bits in 2 parts
# - Encode those parts for 16 iterations
# - Сoncatenate two parts in one block back again
# - Replace block's bits ones again
def encode_blocks(blocks, key):
    for block in blocks:
        bits = to_bits(block)
        left, right = separate(bits)
        encoded_left = encode_part(left, key)
        encoded_right = encode_part(right, key)



def main():
    # Generating a key
    key = generate_key()
    # Getting a raw user input
    raw_text = input("Введите исходный текст: ")
    # UTF-8 encoding the text
    text_bytes = raw_text.encode('utf-8')
    # If the text is too short we add empty (0x0) bytes at the beginning to make it 8 bytes long
    text_bytes = preprocess(text_bytes)
    print(f"Text bytes are {text_bytes}")
    # Separating the text into 8-byte blocks
    text_blocks = text_to_blocks(text_bytes)
    print(f"Text blocks are {text_blocks}")
    # Replacing bits in blocks
    replaced_blocks = initial_replace_blocks(text_blocks)
    print(f"Replaced blocks are {replaced_blocks}")
    # Encoding each block
    encoded_blocks = encode_blocks(replaced_blocks, key)




if __name__ == "__main__":
    main()
