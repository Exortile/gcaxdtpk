import struct, math
from ctypes import *

def align_4bit(n):
    return (n + 3) & ~3

def align_8bit(n):
    return (n + 7) & ~7

def align_16bit(n):
    return (n + 15) & ~15

def align_32bit(n):
    return (n + 31) & ~31

def align_256bit(n):  # this is actually needed LOL
    return (n + 255) & ~255

def find_msb_position(n):
    return int(math.log(n, 2))

def replace_int_bytearray(arr, offset, n):
    n = struct.pack('>I', n)
    for a, b in enumerate(range(offset, offset + 4)):
        arr[b] = n[a]

class ADPCMINFO(Structure):
    _fields_ = [
        ('coef', c_int16 * 16),
        ('gain', c_uint16),
        ('pred_scale', c_uint16),
        ('yn1', c_int16),
        ('yn2', c_int16),

        ('loop_pred_scale', c_uint16),
        ('loop_yn1', c_int16),
        ('loop_yn2', c_int16),
    ]

class FileEntry(BigEndianStructure):
    _fields_ = [
        ('start_offset', c_uint),
        ('unk', c_int),
        ('shifted_size', c_uint),
        ('coef', c_int16 * 16),
        ('unk2', c_int * 3),
        ('unk3', c_int),
        ('sample_rate', c_uint16),
        ('data_size', c_uint),
    ]