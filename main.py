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


# TODO make a single replace function that takes the sequence of bits and the replace matrix as arguments
# TODO and does all the stuff
# TODO how many bits is there in the key? 64 or 56?

# Function generates 6-byte (48-bit) key used for encoding
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
    # Sequence of bits is added via +
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


# Function separates block bits into 2 parts vertically
# Part 1 - left half of matrix of 64 bits
# Part 2 - right half of matrix of 64 bits
def separate_block(bits):
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
            index_to_take_from = el - 1
            # Take the element with that index from the original matrix and put it to the new matrix
            new_matrix.append(half[index_to_take_from])
    # Now this is a bitarray of length 48 formed from a 32-bit bitarray
    return new_matrix


# Function for XOR operation between the key and other bits
def XOR(bits, key):
    res = bitarray()
    for bit1, bit2 in zip(bits, key):
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


# Function replaces bits of the 32-bit sequence (result of S)
def initial_replace_sequence(bits):
    matrix = replace_p()
    new_bits = bitarray()
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            # Move bit with index 16 to the place with index 1 and so on...
            index = el - 1
            # A single bit is added using append
            new_bits.append(bits[index])
    return new_bits


# Function encodes a 32-bit half of a block
# Result is another 32-bit sequence
def encode_part(bits, key):
    # First we have to convert 32 bits to 48 bits
    bits = wide(bits)
    # Do the bits XOR key operation
    bits = XOR(bits, key)
    # Now these bits are split into eight 6-bit blocks
    bits_blocks = bits_to_blocks(bits)
    # A sequence of 4-bit numbers
    seq = bitarray()
    # Now each block is replaced with a single 4-bit number and those numbers form a 32-bit sequence
    for i, block in enumerate(bits_blocks):
        # List of 8 S matrix
        all_S = S()
        # The matrix we need
        s = all_S[i - 1]
        # Get the number of row and column of S matrix from the bits block
        # The number of row is first two bits of the block
        # Get the binary string of bits and convert in to integer
        num_row = int(block[:2].to01(), 2)
        # The number of the column is all the rest
        # Get the binary string of bits and convert in to integer
        # TODO num col in some block = 20 - max is 15! (input string is 'aaa')
        # TODO FINISHED HERE!
        num_col = int(block[2:].to01(), 2)
        # That is the number we use to replace a 6-bit block with
        el = s[num_row][num_col]
        # Convert the number to bits
        el = bitarray(el)
        # Add element(bitarray) to sequence(bitarray)
        seq += el
    # After that we have to replace sequence's bits in a specific order
    seq = initial_replace_sequence(seq)
    return seq


# Function replaces bits of the key in a specific order
# It removes 8 bits from the key
# Returns a 56-bit sequence
def initial_replace_key(key):
    matrix = key_prepare_matrix()
    new_bits = bitarray()
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            # Move bit with index 16 to the place with index 1 and so on...
            index = el - 1
            new_bits.append(key[index])
    return new_bits


# Function extracts upper half of bits
def up_half(bits):
    l = len(bits)
    up = bits[:int(l / 2)]
    return up


# Function extracts down half of bits
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


# Function replaces bits of the key in a specific order
def finish_replace_key(key):
    matrix = key_finish_matrix()
    new_bits = bitarray()
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            # Move bit with index 16 to the place with index 1 and so on...
            index = el - 1
            new_bits.append(key[index])
    return new_bits


# Function transforms a key to a new one each encoding iteration
def transform_key(original_key, iteration):
    # First we replace bits of the key in a specific order
    replaced_key = initial_replace_key(original_key)
    # Then we have to split the replaced key bit into halfs horizontally
    left, right = separate_key(replaced_key)
    # Then we have to move each half two bits to the left a number of times
    left = move_left(left, iteration)
    right = move_left(right, iteration)
    # Concatenate parts together again
    # Result is a 56-bit sequence
    key = left + right
    # Replace bits of key once again
    key = finish_replace_key(key)
    # The new key is ready
    return key


# Function replaces bits one final time
# Result is the encoded 64-bit block
def final_replace_bits(bits):
    matrix = reverse_replace_matrix()
    new_bits = bitarray()
    for row_num, row in enumerate(matrix):
        for col_num, el in enumerate(row):
            # Move bit with index 16 to the place with index 1 and so on...
            index = el - 1
            new_bits.append(bits[index])
    return new_bits


# Function does the following things:
# - Separate each block's bits in 2 parts
# - Encode those parts for 16 iterations
# - Сoncatenate two parts in one block back again
# - Replace block's bits ones again
def encode_blocks(blocks, key):
    encoded_data = bitarray()
    for block in blocks:
        bits = to_bits(block)
        # Two halfs of the block - 32 bits each
        left, right = separate_block(bits)
        for i in range(16):
            left_copy = left
            left = right
            # A new key is generated each iteration
            new_key = transform_key(key, i)
            right = XOR(left_copy, encode_part(right, new_key))
        # After 16 iterations two halfs are concatenated together again
        bits = left + right
        # Bits are replaced in a specific order
        bits = final_replace_bits(bits)
        encoded_data += bits
    return encoded_data


def main():
    # Generating a key
    key = generate_key()
    # Getting a raw user input
    raw_text = input("Введите исходный текст: ")
    # UTF-8 encoding the text
    text_bytes = raw_text.encode('utf-8')
    # If the text is too short we add empty (0x0) bytes at the beginning to make it /8 bytes long
    text_bytes = preprocess(text_bytes)
    print(f"Text bytes are {text_bytes}")
    # Separating the text into 8-byte blocks
    text_blocks = text_to_blocks(text_bytes)
    print(f"Text blocks are {text_blocks}")
    # Replacing bits in blocks
    replaced_blocks = initial_replace_blocks(text_blocks)
    print(f"Replaced blocks are {replaced_blocks}")
    # Encoding each block
    encoded_data = encode_blocks(replaced_blocks, key)
    print(f'Encoded data is: \n {encoded_data}')



if __name__ == "__main__":
    main()
