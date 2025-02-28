import struct
import math
import pathlib

from ctypes import (
    Structure,
    BigEndianStructure,
    c_int16,
    c_uint16,
    c_uint,
    c_int
)


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


def get_path_in_script_dir(*paths) -> pathlib.Path:
    full_path = pathlib.Path(__file__).parent.resolve()
    for path in paths:
        full_path = full_path / path

    return full_path


def validate_gcaxdtpk(file) -> bool:
    file.seek(0)
    try:
        return file.read(8).decode("ascii") == "gcaxDTPK"
    except Exception:
        return False


class termcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


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
