import struct
import pathlib

from ctypes import (
    byref,
    c_uint32,
    c_uint8,
    c_int16
)

from exceptions import (
    GeneralException,
    GeneralExceptionEnum,
    WAVException,
    WAVExceptionEnum
)

from gcax_classes import (
    ADPCMINFO,
    FileEntry,
    termcolors,
    get_path_in_script_dir,
    replace_int_bytearray,
    find_msb_position,
    align_256bit,
    align_32bit,
    align_8bit
)


class GCAXExporter:
    input: pathlib.Path
    file_identifier: int
    output: pathlib.Path

    def __init__(self, dsptool, input: str, file_identifier: str, output: str):
        self.dsptool = dsptool  # dsptool.dll
        self.input = pathlib.Path(input)
        self.output = pathlib.Path(output)
        self._set_file_identifier(file_identifier)

        if not self.input.is_dir():
            raise GeneralException(GeneralExceptionEnum.NonDirectory)

        if self.output.exists() and self.output.is_dir():
            raise GeneralException(GeneralExceptionEnum.OutputIsDirectory)

    def _set_file_identifier(self, file_identifier: str):
        try:
            file_identifier = int(file_identifier)
        except ValueError:
            try:
                file_identifier = int(file_identifier[2:], base=16)
            except ValueError:
                raise GeneralException(
                    GeneralExceptionEnum.InvalidFileIdentifier)

        if file_identifier > 0xFFFF:
            raise GeneralException(
                GeneralExceptionEnum.InvalidTypeFileIdentifier)

        self.file_identifier = file_identifier

    def _encode_wav(self, file, data_offset):
        info = ADPCMINFO()

        with open(self.input / file.name, 'rb') as wavfile:
            if wavfile.read(4).decode('ASCII') != 'RIFF':
                raise WAVException(
                    WAVExceptionEnum.InvalidFileFormatRIFF, file.name)

            wavfile.seek(0x8)
            if wavfile.read(4).decode('ASCII') != 'WAVE':
                raise WAVException(
                    WAVExceptionEnum.InvalidFileFormatWAVE, file.name)

            wavfile.seek(0x14)
            # if not formatted in PCM
            if struct.unpack('<H', wavfile.read(2))[0] != 1:
                raise WAVException(
                    WAVExceptionEnum.NotEncodedInPCM, file.name)

            wavfile.seek(0x16)
            # if not mono channel
            if struct.unpack('<H', wavfile.read(2))[0] != 1:
                raise WAVException(
                    WAVExceptionEnum.NotEncodedInMonoChannel, file.name)

            sample_rate = struct.unpack('<I', wavfile.read(4))[0]
            if sample_rate != 44100:
                print(
                    f"{termcolors.WARNING}WARNING: File '{file.name}' "
                    "does not have a sample rate of 44100 Hz! "
                    f"Audio file may behave improperly.{termcolors.ENDC}")

            wavfile.seek(0x22)
            # if not 16 bit
            if struct.unpack('<H', wavfile.read(2))[0] != 16:
                raise WAVException(
                    WAVExceptionEnum.NotEncodedIn16Bit, file.name)

            wavfile.seek(0x28)
            data_length = struct.unpack('<I', wavfile.read(4))[0]
            wav = wavfile.read(data_length)
            wav_data = [struct.unpack('<h', wav[i:i + 2])[0]
                        for i in range(0, len(wav), 2)]

        sample_count = len(wav_data)
        c_sample_count = c_uint32(sample_count)
        adpcm_byte_count = self.dsptool.getBytesForAdpcmBuffer(
            c_sample_count)
        outpcm = (c_uint8 * adpcm_byte_count)()
        inwav = (c_int16 * len(wav_data))(*wav_data)

        self.dsptool.encode(byref(inwav), byref(
            outpcm), byref(info), c_sample_count)

        coefs = (c_int16.__ctype_be__ * 16)(*info.coef)

        fileentry = FileEntry(data_offset, 2, (adpcm_byte_count << 1) - 1,
                              coefs, (0, 0, 0), 0x200,
                              sample_rate, adpcm_byte_count)

        return outpcm, fileentry

    def run(self):
        with open(get_path_in_script_dir("Template.dat"), "rb") as tfile:
            template_main_body = bytearray(tfile.read(0x278))
            tfile.seek(0x300)
            template_data_header = bytearray(tfile.read(0x30))
            template_data_struct = bytearray(tfile.read(0x40))

        # order all the files correctly in directory
        try:
            files = sorted(self.input.glob("*.wav"),
                           key=lambda x: int(x.name[:x.name.index('_')]))
        except ValueError:
            raise GeneralException(GeneralExceptionEnum.InvalidFilenameFormat)

        file_count = len(files)

        if file_count == 0:
            raise GeneralException(GeneralExceptionEnum.NoFiles)

        delta_file_count = file_count - 1

        template_main_body += struct.pack('>2HB3x',
                                          self.file_identifier, 0x8, delta_file_count)
        sndfile_table_offset = (file_count * 4) + 0xC
        for _ in range(file_count):
            template_main_body += struct.pack('>I', sndfile_table_offset)
            sndfile_table_offset += 6
        for f in range(file_count):
            template_main_body += struct.pack('>HBHB', 0xC0DF, f, 0x7F80, 0xFF)

        while len(template_main_body) & 0x3:  # 4 bit alignment
            template_main_body += b'\x00'

        audio_info_data = template_data_header
        audio_info_data[0x11] = delta_file_count
        for f in range(file_count):
            audio_info_struct = template_data_struct
            audio_info_struct[0x0] = f
            audio_info_struct[0x3] = f
            audio_info_data += audio_info_struct

        file_entry_data = struct.pack('>I', delta_file_count)
        audio_data = bytearray(struct.pack(
            '>8sI20x', bytes('gcaxPCMD', 'ascii'), 0x024a0100))
        for wavfilename in files:
            print(
                f"{termcolors.OKCYAN}Encoding '{wavfilename.name}'{termcolors.ENDC}")

            outpcm, fileentry = self._encode_wav(wavfilename, len(audio_data))

            file_entry_data += fileentry
            audio_data += outpcm

            aligned_length = align_8bit(len(audio_data))
            while len(audio_data) != aligned_length:
                audio_data += b'\x00'

        print()

        aligned_length = align_32bit(len(audio_data))
        while len(audio_data) != aligned_length:
            audio_data += b'\x00'

        replace_int_bytearray(audio_data, 0xC, aligned_length)

        end_of_info = align_32bit(
            len(template_main_body) + len(audio_info_data) + len(file_entry_data))
        eoi_msb = find_msb_position(end_of_info)
        audio_data_start_offset = 1 << eoi_msb + 1

        full_file_length = align_256bit(
            audio_data_start_offset + len(audio_data))

        replace_int_bytearray(
            template_main_body, 0xC, full_file_length)
        replace_int_bytearray(
            template_main_body, 0x10, end_of_info + 0x20)
        replace_int_bytearray(
            template_main_body, 0x18, len(audio_data) + 0x20)
        replace_int_bytearray(
            template_main_body, 0x1C, audio_data_start_offset)

        replace_int_bytearray(
            template_main_body, 0xA8, len(template_main_body))
        replace_int_bytearray(template_main_body, 0xB8, len(
            template_main_body) + len(audio_info_data))
        replace_int_bytearray(
            template_main_body, 0xBC, end_of_info)

        with open(self.output, 'wb') as outfile:
            outfile.write(template_main_body)
            outfile.write(audio_info_data)
            outfile.write(file_entry_data)
            while outfile.tell() != audio_data_start_offset:
                outfile.write(b'\x00')

            outfile.write(audio_data)
            while outfile.tell() != full_file_length:
                outfile.write(b'\x00')
