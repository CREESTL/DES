from consts import *
from bitarray import bitarray

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


# Function padding the string to 8-byte size
def preprocess(text_bytes):
    b_ar = bytearray(text_bytes)
    if len(b_ar) < 8:
        new_b_ar = bytearray()
        for i in range(8 - len(b_ar)):
            new_b_ar.append(0)
        new_b_ar += b_ar
    t_bytes = bytes(new_b_ar)
    return t_bytes


# Function splits encoded text into 8-byte blocks
def to_blocks(text_bytes):
    blocks = []
    start = 0
    end = 8
    # If text is less than 8 bytes we still have to add it
    blocks.append(text_bytes[start:end])
    while end < len(text_bytes) - 1:
        block = text_bytes[start:end]
        start = end
        end += 8
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


def main():
    # Getting a raw user input
    raw_text = input("Введите исходный текст: ")
    # UTF-8 encoding the text
    text_bytes = raw_text.encode('utf-8')
    # If the text is too short we add empty (0x0) bytes at the beginning to make it 8 bytes long
    text_bytes = preprocess(text_bytes)
    # Separating the text into 8-byte blocks
    text_blocks = to_blocks(text_bytes)
    # Replacing bits in blocks
    replaced_blocks = initial_replace_blocks(text_blocks)
    # Separating bits in blocks in 2 parts




if __name__ == "__main__":
    main()
