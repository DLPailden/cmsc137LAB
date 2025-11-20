import random

# G(x) = x^3 + x + 1 -> '1011'
generator = '1011'

#Convert a text message to a string of bits (8-bit ASCII per char)
def str_to_bin(message):
    return ''.join(format(ord(c), '08b') for c in message)


#Function to perform Modulo-2 Division (XOR division) for CRC calculation.
def mod2_division(dividend, divisor):
    #dividend is the binary string (data + zeros), divisor is the generator polynomial
    #Converting strings into lists of characters
    dividend = list(dividend)
    divisor = list(divisor)
    n = len(divisor)

    #Main Modulo 2 Division Loop
    #Iterates over each bit of the dividend where the divisor can fit
    for i in range(len(dividend) - n + 1):  
        #Only perform XOR if the current bit of the dividend is 1
        if dividend[i] == '1':
            #XOR each bit of the divisor with the corresponding bit of the dividend.
            for j in range(n):
                dividend[i + j] = '1' if dividend[i + j] != divisor[j] else '0'
    # remainder is returned
    return ''.join(dividend[-(n - 1):])


#Function to encode a message with CRC before sending over the network.
def encode_message(message):
    k = len(generator)

    #converts ASCII message into binary string and appends k-1 zeros at the end
    data_bits = str_to_bin(message) + '0' * (k - 1) 
    #perform mod2 division to get the remainder
    remainder = mod2_division(data_bits, generator)

    # Append remainder (string of '0'/'1') directly to message as characters.
    # Format: original message (ASCII chars) + crc_bits (k-1 characters '0' or '1')
    return message + remainder


#Function to verify a message received over the network by checking its CRC.
def decode_message(msg_with_crc):
    k = len(generator)
    #Ensure the message is at least k-1 bits long to extract CRC
    if len(msg_with_crc) < (k - 1):
        return None, False
    
    #Separate the original message and the received CRC bits
    msg = msg_with_crc[:-(k - 1)]
    crc_received = msg_with_crc[-(k - 1):]

    #Convert Message to Binary and Append Zeros
    data_bits = str_to_bin(msg) + '0' * (k - 1)
    #Perform Modulo-2 Division to get the remainder
    remainder = mod2_division(data_bits, generator)

    #Return the original message and a boolean whether the message pass CRC validity
    return msg, (remainder == crc_received)


#Function to randomly add transmission errors in a message with CRC.
def introduce_error(msg_with_crc, error_prob=0.1):
    if not msg_with_crc:
        return msg_with_crc
    
    #Decide whether to introduce an Error
    if random.random() < error_prob:
        #Picks a random character in the string to corrupt.
        index = random.randint(0, len(msg_with_crc) - 1)
        ch = msg_with_crc[index]
        # choose a bit to flip in the 8-bit char (0..7), creates the bit mask
        bit_to_flip = 1 << random.randint(0, 7)
        # XOR the ASCII value of the character with the bit mask to flip the selected bit
        flipped_ord = ord(ch) ^ bit_to_flip
        # convert the modified ASCII value back to a character
        flipped = chr(flipped_ord)

        # Construct the new string with the flipped character replacing the original
        return msg_with_crc[:index] + flipped + msg_with_crc[index + 1:]
    
    # No error is introduced, return the original string unchanged
    return msg_with_crc
