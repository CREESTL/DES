from consts import *
from bitarray import bitarray
from bitarray.util import int2ba as int2bits
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


# Function generates 64-bit key used for encoding
# In the code itself only 56 bits are used
# Other 8 are used for parity check - they are removed with first key bits replacing
def generate_key():
    key = bitarray()
    for i in range(64):
        key.append(random.randint(0, 1))
    return key


# If it's needed the function adds empty bytes ar the end of the string to make it the size that
# can be divided by 8 (bytes)
def preprocess(text_bytes):
    b_ar = bytearray(text_bytes)
    while len(b_ar) % 8 != 0:
        b_ar.append(0)
    return bytes(b_ar)


# Function splits encoded text into 8-byte blocks
def text_to_blocks(bits):
    blocks = []
    start = 0
    end = 64
    # If text is less than 64 bits we still have to add it
    blocks.append(bits[start:end])
    while end < len(bits):
        start = end
        end += 64
        block = bits[start:end]
        blocks.append(block)
    return blocks


# Function converts 8-byte block into bits (bitarray)
# Returns bitarray - not simple list
def to_bits(_bytes):
    bits = bitarray()
    bits.frombytes(_bytes)
    return bits


# Function replaces bits in sequence according to the given matrix
def replace(bits, matrix):
    new_bits = bitarray()
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            new_bits.append(bits[el - 1])
    return new_bits


# Function replaces bits of all blocks in the text
def replace_blocks(text_blocks):
    new_text_blocks = []
    matrix = initial_replace_matrix()
    for block in text_blocks:
        new_block = replace(block, matrix)
        new_text_blocks.append(new_block)
    return new_text_blocks


# Function extracts left half of bits 2D array
def left_half(bits):
    left = bitarray()
    start = 0
    end = 4
    part = bits[start:end]
    # Sequence of bits is added via +
    left += part
    while end < (len(bits) - 4):
        start = end + 4
        end = end + 8
        part = bits[start:end]
        left += part
    return left


# Function extracts right half of bits 2D array
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


# Function separates block bits into 2 parts vertically
# Part 1 - left half of matrix of 64 bits
# Part 2 - right half of matrix of 64 bits
def separate_block(bits):
    left = left_half(bits)
    right = right_half(bits)
    return left, right


# Function for XOR operation between the key and other bits
def XOR(bits, key):
    res = bitarray()
    for bit1, bit2 in zip(bits, key):
        res_bit = bit1 ^ bit2
        res.append(res_bit)
    return res


# Function splits 48-bit bitarray into 8 blocks 6 bits each
def to8blocks(bits):
    # An array of bitarrays
    blocks = []
    start = 0
    end = 6
    block = bits[start:end]
    blocks.append(block)
    while end < len(bits):
        start = end
        end += 6
        block = bits[start:end]
        blocks.append(block)
    return blocks


# Function converts sequence of less then 4 bits to the sequence of 4 bits
def len4(bits):
    while len(bits) != 4:
        bits.insert(0, 0)
    return bits


# Function encodes a 32-bit half of a block
# Result is another 32-bit sequence
def encode_part(bits, key):
    # First we have to convert 32 bits to 48 bits
    bits = replace(bits, wide_matrix())
    # Do the bits XOR key operation
    # (key here is a 48-bit sequence generated from original 64-bit key)
    bits = XOR(bits, key)
    # Now these bits are split into eight 6-bit blocks
    bits_blocks = to8blocks(bits)
    seq = bitarray()
    # Now each block is replaced with a single 4-bit number and those numbers form a 32-bit sequence
    for i, block in enumerate(bits_blocks):
        # List of 8 S matrices
        all_S = S()
        # The matrix we need
        s = all_S[i - 1]
        # Get the number of row and column of S matrix from the bits block
        # The number of row is first two bits of the block
        # Get the binary string of bits and convert in to integer
        # We need to subtract 1 because indexing starts with 0
        num_row = int(block[:2].to01(), 2) - 1
        # The number of the column is all the rest
        # Get the binary string of bits and convert in to integer
        num_col = int(block[2:].to01(), 2) - 1
        # That is the number we use to replace a 6-bit block with
        el = s[num_row][num_col]
        # Convert the integer to bits
        el = int2bits(el)
        # Make these bits 4 units long (add zero bits at the beginning)
        el = len4(el)
        # Add element(bitarray) to sequence(bitarray)
        seq += el
    # After that we have to replace sequence's bits in a specific order
    seq = replace(seq, replace_p())
    return seq


# Function extracts upper half of bits 2D array
def up_half(bits):
    l = len(bits)
    up = bits[:int(l / 2)]
    return up


# Function extracts down half of bits 2D array
def down_half(bits):
    l = len(bits)
    down = bits[int(l / 2):]
    return down


# Function splits bit of key into 2 parts horizontally
def separate_key(key):
    up = up_half(key)
    down = down_half(key)
    return up, down


# Function moves bits 2 bits to the left for several times
def move_left(bits, iteration):
    table = bits_move_table()
    num_bits_to_move = table[iteration + 1]
    return bits << num_bits_to_move


# Function transforms a key to a new one each encoding iteration
def transform_key(original_key, iteration):
    # First we replace bits of the key in a specific order
    replaced_key = replace(original_key, key_prepare_matrix())
    # Then we have to split the replaced key bit into halfs horizontally
    left, right = separate_key(replaced_key)
    # Then we have to move each half two bits to the left a number of times
    left = move_left(left, iteration)
    right = move_left(right, iteration)
    # Concatenate parts together again
    # Result is a 56-bit sequence
    key = left + right
    # Replace bits of key once again
    key = replace(key, key_finish_matrix())
    # The new key is ready
    return key


# Main encoding function
def encode_blocks(blocks, key):
    encoded_data = bitarray()
    for block in blocks:
        left, right = separate_block(block)
        for i in range(16):
            left_copy = left
            left = right
            # A new key is generated each iteration (from original 64-bit key)
            new_key = transform_key(key, i)
            # One half is encoded per iteration
            right = XOR(left_copy, encode_part(right, new_key))
        # After 16 iterations two halfs are concatenated together again
        bits = left + right
        # Bits are replaced in a specific order
        bits = replace(bits, reverse_replace_matrix())
        encoded_data += bits
    return encoded_data


def main():
    # Generating a key
    key = generate_key()
    # Getting a raw user input
    raw_text = input("Enter text to encode: ")
    # UTF-8 encoding the text
    text_bytes = raw_text.encode('utf-8')
    # If the text is too short we add empty (0x0) bytes at the beginning to make it multiple 8-bit long
    text_bytes = preprocess(text_bytes)
    # Now convert from bytes into bits
    text_bits = to_bits(text_bytes)
    # Separating the text into 8-byte (64-bit) blocks
    text_blocks = text_to_blocks(text_bits)
    # Replacing bits in blocks
    replaced_blocks = replace_blocks(text_blocks)
    # Encoding each block
    encoded_data = encode_blocks(replaced_blocks, key)
    print(f'Encoded data in: \nBytes: {encoded_data.tobytes()[2:]} \nBits: {encoded_data.to01()}')


if __name__ == "__main__":
    main()
