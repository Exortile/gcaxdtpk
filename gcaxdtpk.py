import argparse, os, struct
import gcax_classes
from exceptions import *
from ctypes import *

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str,
                        help='Path to a folder that contains WAV files to be put into the DTPK archive. The WAV files must be named according to this format: "0_name.wav". This way the tool knows in which order should the WAV files go into the DTPK archive. The WAV file must also be encoded using signed 16-bit PCM, it must only be in mono channel and with a sample rate of 44100 Hz. Other sample rates may work, but aren\'t guaranteed.')
    parser.add_argument('file_identifier', type=str,
                        help='Used as a unique identifier to determine what file is which in terms of other DTPK archives loaded in the game. For example, calling audio with the ID 0xA9320200, means that the identifier in this case is 0xA932.')
    parser.add_argument('output', type=str, nargs='?',
                        help='Path to where the file should be saved, along with the filename.')
    parsedargs = parser.parse_args()

    input = parsedargs.input
    output = parsedargs.output
    if output is None:
        output = input + '.DAT'

    file_identifier = parsedargs.file_identifier
    dllpath = os.path.join(os.getcwd(), 'dsptool.dll')
    dsptooldll = cdll.LoadLibrary(dllpath)

    with open("template.dat", "rb") as tfile:
        template_main_body = bytearray(tfile.read(0x278))
        tfile.seek(0x300)
        template_data_header = bytearray(tfile.read(0x30))
        template_data_struct = bytearray(tfile.read(0x40))

    if not os.path.isdir(input):
        raise GeneralException(GeneralExceptionEnum.NonDirectory)

    isNormalInt = False

    try:
        file_identifier = int(file_identifier)
        isNormalInt = True
    except:
        isNormalInt = False

    if not isNormalInt:
        try:
            file_identifier = int(file_identifier[2:], base=16)
        except:
            raise GeneralException(GeneralExceptionEnum.InvalidFileIdentifier)

    if file_identifier > 0xFFFF:
        raise GeneralException(GeneralExceptionEnum.InvalidTypeFileIdentifier)

    # order all the files correctly in directory
    files = sorted([f for f in os.listdir(input) if os.path.isfile(os.path.join(input, f))],
                key=lambda x: int(x[:x.index('_')]))
    file_count = len(files)
    delta_file_count = file_count - 1

    template_main_body += struct.pack('>2HB3x', file_identifier, 0x8, delta_file_count)
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
    audio_data = bytearray(struct.pack('>8sI20x', bytes('gcaxPCMD', 'ascii'), 0x024a0100))
    for wavfilepath in files:
        info = gcax_classes.ADPCMINFO()

        fullwavfilepath = os.path.join(input, wavfilepath)

        with open(fullwavfilepath, 'rb') as wavfile:
            if wavfile.read(4).decode('ASCII') != 'RIFF':
                raise WAVException(WAVExceptionEnum.InvalidFileFormatRIFF, os.path.basename(fullwavfilepath))

            wavfile.seek(0x8)
            if wavfile.read(4).decode('ASCII') != 'WAVE':
                raise WAVException(WAVExceptionEnum.InvalidFileFormatWAVE, os.path.basename(fullwavfilepath))

            wavfile.seek(0x14)
            if struct.unpack('<H', wavfile.read(2))[0] != 1:  # if not formatted in PCM
                raise WAVException(WAVExceptionEnum.NotEncodedInPCM, os.path.basename(fullwavfilepath))

            wavfile.seek(0x16)
            if struct.unpack('<H', wavfile.read(2))[0] != 1:  # if not mono channel
                raise WAVException(WAVExceptionEnum.NotEncodedInMonoChannel, os.path.basename(fullwavfilepath))

            sample_rate = struct.unpack('<I', wavfile.read(4))[0]

            wavfile.seek(0x22)
            if struct.unpack('<H', wavfile.read(2))[0] != 16:  # if not 16 bit
                raise WAVException(WAVExceptionEnum.NotEncodedIn16Bit, os.path.basename(fullwavfilepath))

            wavfile.seek(0x28)
            data_length = struct.unpack('<I', wavfile.read(4))[0]
            wav = wavfile.read(data_length)
            wav_data = [struct.unpack('<h', wav[i:i + 2])[0] for i in range(0, len(wav), 2)]

        sample_count = len(wav_data)
        c_sample_count = c_uint32(sample_count)
        adpcm_byte_count = dsptooldll.getBytesForAdpcmBuffer(c_sample_count)
        outpcm = (c_uint8 * adpcm_byte_count)()
        inwav = (c_int16 * len(wav_data))(*wav_data)

        dsptooldll.encode(pointer(inwav), pointer(outpcm), pointer(info), c_sample_count)

        coefs = (c_int16.__ctype_be__ * 16)(*info.coef)

        fileentry = gcax_classes.FileEntry(len(audio_data), 2, (adpcm_byte_count << 1) - 1, coefs, (0, 0, 0), 0x200, sample_rate,
                            adpcm_byte_count)
        file_entry_data += fileentry

        audio_data += outpcm
        aligned_length = gcax_classes.align_8bit(len(audio_data))
        while len(audio_data) != aligned_length:
            audio_data += b'\x00'

    aligned_length = gcax_classes.align_32bit(len(audio_data))
    while len(audio_data) != aligned_length:
        audio_data += b'\x00'

    gcax_classes.replace_int_bytearray(audio_data, 0xC, aligned_length)

    end_of_info = gcax_classes.align_32bit(len(template_main_body) + len(audio_info_data) + len(file_entry_data))
    eoi_msb = gcax_classes.find_msb_position(end_of_info)
    audio_data_start_offset = 1 << eoi_msb + 1

    full_file_length = gcax_classes.align_256bit(audio_data_start_offset + len(audio_data))

    gcax_classes.replace_int_bytearray(template_main_body, 0xC, full_file_length)
    gcax_classes.replace_int_bytearray(template_main_body, 0x10, end_of_info + 0x20)
    gcax_classes.replace_int_bytearray(template_main_body, 0x18, len(audio_data) + 0x20)
    gcax_classes.replace_int_bytearray(template_main_body, 0x1C, audio_data_start_offset)

    gcax_classes.replace_int_bytearray(template_main_body, 0xA8, len(template_main_body))
    gcax_classes.replace_int_bytearray(template_main_body, 0xB8, len(template_main_body) + len(audio_info_data))
    gcax_classes.replace_int_bytearray(template_main_body, 0xBC, end_of_info)

    with open(output, 'wb') as outfile:
        outfile.write(template_main_body)
        outfile.write(audio_info_data)
        outfile.write(file_entry_data)
        while outfile.tell() != audio_data_start_offset:
            outfile.write(b'\x00')

        outfile.write(audio_data)
        while outfile.tell() != full_file_length:
            outfile.write(b'\x00')

if __name__ == "__main__":
    main()