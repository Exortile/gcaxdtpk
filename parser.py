import pathlib
import struct

from exceptions import (
    GeneralException,
    GeneralExceptionEnum,
    GCAXException
)

from gcax_classes import validate_gcaxdtpk, termcolors


class GCAXParser:
    def __init__(self, input_path: str):
        self.input_path = pathlib.Path(input_path)

        if not self.input_path.is_file():
            raise GeneralException(GeneralExceptionEnum.NonFile)

    def __enter__(self):
        self.file = open(self.input_path, "rb")
        if not validate_gcaxdtpk(self.file):
            raise GCAXException(
                "Supplied input file is an invalid DTPK soundbank file.")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def _read_u32(self):
        return struct.unpack(">I", self.file.read(4))[0]

    def _read_u16(self):
        return struct.unpack(">H", self.file.read(2))[0]

    def parse_and_print(self):
        def hex_upper(num):
            return "0x" + hex(num)[2:].upper()

        self.file.seek(0xC)
        full_file_size = self._read_u32()

        self.file.seek(0x1C)
        audio_data_offset = self._read_u32()

        self.file.seek(0xB8)
        file_entries_offset = self._read_u32()

        self.file.seek(file_entries_offset)
        audio_file_count = self._read_u32() + 1

        self.file.seek(0x278)
        file_identifier = self._read_u16()

        self.file.seek(audio_data_offset)
        self.file.seek(0xC, 1)  # relative
        audio_data_size = self._read_u32()

        centered_info_header = " General Info ".center(40, '-')
        centered_details_header = " Technical Details ".center(40, '-')

        print(f"{termcolors.HEADER}{centered_info_header}{termcolors.ENDC}")
        print(termcolors.OKCYAN)

        print(f"File: {self.input_path.name}")
        print(f"File Identifier: {hex_upper(file_identifier)}")
        print(f"Audio File Count: {audio_file_count}")

        print(termcolors.ENDC)

        print(f"{termcolors.HEADER}{centered_details_header}{termcolors.ENDC}")
        print(termcolors.OKCYAN)

        print(f"Full File Size: {hex_upper(full_file_size)}")
        print(f"File Entries Offset: {hex_upper(file_entries_offset)}")
        print(f"Audio Data Offset: {hex_upper(audio_data_offset)}")
        print(f"Audio Data Size: {hex_upper(audio_data_size)}")

        print(termcolors.ENDC)
