import cv2
import numpy as np

L_CODES = {
    "0001101": "0", "0011001": "1", "0010011": "2", "0111101": "3",
    "0100011": "4", "0110001": "5", "0101111": "6", "0111011": "7",
    "0110111": "8", "0001011": "9"
}
G_CODES = {
    "0100111": "0", "0110011": "1", "0011011": "2", "0100001": "3",
    "0011101": "4", "0111001": "5", "0000101": "6", "0010001": "7",
    "0001001": "8", "0010111": "9"
}
R_CODES = {
    "1110010": "0", "1100110": "1", "1101100": "2", "1000010": "3",
    "1011100": "4", "1001110": "5", "1010000": "6", "1000100": "7",
    "1001000": "8", "1110100": "9"
}

PARITY_PATTERNS = {
    "LLLLLL": "0",
    "LLGLGG": "1",
    "LLGGLG": "2",
    "LLGGGL": "3",
    "LGLLGG": "4",
    "LGGLLG": "5",
    "LGGGLL": "6",
    "LGLGLG": "7",
    "LGLGGL": "8",
    "LGGLGL": "9"
}


def get_scanlines(image_path):
    img = cv2.imread(image_path)
    height, width = img.shape[:2]
    if height < 10 or width < 10:
        raise Exception("Zbyt mały obraz")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lines = []
    for i in range(10, 255, 20):
        _, binary = cv2.threshold(gray, i, 255, cv2.THRESH_BINARY_INV)
        # display binary
        # dilation to make the lines thicker
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.erode(binary, kernel, iterations=1)
        for j in range(0, height, height // 5):
            scanline = [1 if dilated[j, x] == 255 else 0 for x in range(width)]
            print(scanline)
            lines.append(scanline)
            scanline = [1 if binary[j, x] == 255 else 0 for x in range(width)]
            lines.append(scanline)
        for j in range(0, height, height // 5):
            scanline = [1 if dilated[j, x] == 255 else 0 for x in range(width)]
            lines.append(scanline)
            scanline = [1 if binary[j, x] == 255 else 0 for x in range(width)]
            lines.append(scanline)
    return lines


def determine_bit_width(binary_line, blocks_to_skip=0):
    START_GUARD = [1, 0, 1]
    blocks = 0
    pos = 0
    cur_block = binary_line[0]
    for i in range(len(binary_line)):
        if binary_line[i] != cur_block:
            if cur_block == START_GUARD[0]:
                blocks += 1
            else:
                if blocks == blocks_to_skip:
                    pos = i
                    break
            cur_block = binary_line[i]
    beg_pos = pos
    bit_lens = [0, 0, 0]
    for i in range(len(START_GUARD)):
        for j in range(pos, len(binary_line)):
            if binary_line[j] == START_GUARD[i]:
                bit_lens[i] += 1
            else:
                pos = j
                break
    bit_width = sum(bit_lens) // len(START_GUARD)
    if all(0.5 < (bit_len / bit_width) < 1.5 for bit_len in bit_lens):
        return bit_width, beg_pos
    else:
        if blocks_to_skip < 50:
            return determine_bit_width(binary_line, blocks_to_skip+1)
        else:
            return None, None

def read_bits(binary_line, bit_width, start_pos):
    bits = []
    pos = start_pos
    cur_bit = 0
    run = 0
    for i in range(pos, len(binary_line)):
        if binary_line[i] != cur_bit:
            how_many = round(run / bit_width)
            bits.extend([cur_bit] * how_many)
            if len(bits) == 95:
                break
            # if len(bits) > 95:
            #     return None
            cur_bit = binary_line[i]
            run = 1
        else:
            run += 1
    return bits[:95]


def decode_ean13(code):
    if len(code) != 95:
        raise Exception("Kod kreskowy nie ma 95 bitów")
    EDGE_GUARD_LEN = 3
    CENTER_GUARD_LEN = 5
    left_section = code[EDGE_GUARD_LEN:EDGE_GUARD_LEN+6*7]
    right_section = code[EDGE_GUARD_LEN+6*7+CENTER_GUARD_LEN:-3]

    left_digits = []
    parity_pattern = ""
    for i in range(0, len(left_section), 7):
        bits = ''.join(map(str, left_section[i:i + 7]))
        if bits in L_CODES:
            left_digits.append(L_CODES[bits])
            parity_pattern += "L"
        elif bits in G_CODES:
            left_digits.append(G_CODES[bits])
            parity_pattern += "G"
        else:
            raise Exception("Błąd w dekodowaniu sekcji lewej")

    right_digits = []
    for i in range(0, len(right_section), 7):
        bits = ''.join(map(str, right_section[i:i + 7]))
        if bits in R_CODES:
            right_digits.append(R_CODES[bits])
        else:
            raise Exception("Błąd w dekodowaniu sekcji prawej")

    first_digit = PARITY_PATTERNS[parity_pattern]
    return first_digit + ''.join(left_digits + right_digits)


def read_barcode(img_path):
    results = []
    try:
        scanlines = get_scanlines(img_path)
    except Exception as e:
        print(f"Błąd: {e}")
        return None
    for scanline in scanlines:
        try:
            bit_width, start_pos = determine_bit_width(scanline)
            print("bit_width", bit_width)
            code = read_bits(scanline, bit_width, start_pos)
            print("code", code)
            results.append(decode_ean13(code))
        except Exception as e:
            print(f"Błąd: {e}")
    if len(results) == 0:
        return None
    barcode = max(set(results), key=results.count)
    return barcode