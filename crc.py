# crc.py
import random

# G(x) = x^3 + x + 1 -> '1011'
generator = '1011'

def str_to_bin(message):
    """ Convert a text message to a string of bits (8-bit ASCII per char) """
    return ''.join(format(ord(c), '08b') for c in message)


def mod2_division(dividend, divisor):
    """
    Perform modulo-2 division (binary XOR) and return remainder of length len(divisor)-1.
    dividend and divisor are strings of '0'/'1'.
    """
    dividend = list(dividend)
    divisor = list(divisor)
    n = len(divisor)
    for i in range(len(dividend) - n + 1):
        if dividend[i] == '1':
            for j in range(n):
                dividend[i + j] = '1' if dividend[i + j] != divisor[j] else '0'
    # remainder is appended as the last n-1 bits
    return ''.join(dividend[-(n - 1):])


def encode_message(message):
    """
    Return message with CRC bits appended as characters '0'/'1'.
    Format: original message (ASCII chars) + crc_bits (k-1 characters '0' or '1')
    """
    k = len(generator)
    data_bits = str_to_bin(message) + '0' * (k - 1)
    remainder = mod2_division(data_bits, generator)
    # Append remainder (string of '0'/'1') directly to message as characters.
    return message + remainder


def decode_message(msg_with_crc):
    """
    Given a string of original_message + crc_bits, returns (message, valid_bool).
    If input is too short to contain crc, returns (None, False).
    """
    k = len(generator)
    if len(msg_with_crc) < (k - 1):
        return None, False
    msg = msg_with_crc[:-(k - 1)]
    crc_received = msg_with_crc[-(k - 1):]
    data_bits = str_to_bin(msg) + '0' * (k - 1)
    remainder = mod2_division(data_bits, generator)
    return msg, (remainder == crc_received)


def introduce_error(msg_with_crc, error_prob=0.1):
    """
    With probability error_prob, flips one bit of a randomly chosen character in the string.
    Returns possibly-modified string.
    """
    if not msg_with_crc:
        return msg_with_crc
    if random.random() < error_prob:
        index = random.randint(0, len(msg_with_crc) - 1)
        ch = msg_with_crc[index]
        # choose a bit to flip in the 8-bit char (0..7)
        bit_to_flip = 1 << random.randint(0, 7)
        flipped_ord = ord(ch) ^ bit_to_flip
        flipped = chr(flipped_ord)
        return msg_with_crc[:index] + flipped + msg_with_crc[index + 1:]
    return msg_with_crc
