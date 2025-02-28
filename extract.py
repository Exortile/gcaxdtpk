import struct
import pathlib

from exceptions import (
    GCAXException,
    GeneralException,
    GeneralExceptionEnum
)

from gcax_classes import (
    validate_gcaxdtpk,
    FileEntry,
    ADPCMINFO,
    termcolors
)

from ctypes import (
    sizeof,
    byref,
    c_uint8,
    c_int16,
    c_uint32
)


class WAVWriter:
    """Class that handles writing a signed 16-bit PCM wave file."""
    HEADER_SIZE = 0x2C

    def __init__(self, path: pathlib.Path):
        self.path = path

    def __enter__(self):
        self.file = open(self.path, "wb")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def _write_header(self, sample_rate: int, audio_data_len: int):
        self.file.write(b"RIFF")

        # calc size of file
        size_of_file = audio_data_len + self.HEADER_SIZE
        size_of_file -= 8  # to not account for "RIFF" and size of file description

        self.file.write(struct.pack("<I", size_of_file))
        self.file.write(b"WAVEfmt ")

        # size of wav type format
        self.file.write(struct.pack("<I", 0x10))

        # format type
        self.file.write(struct.pack("<H", 1))

        # number of channels
        self.file.write(struct.pack("<H", 1))

        self.file.write(struct.pack("<I", sample_rate))

        # audio data rate
        self.file.write(struct.pack("<I", sample_rate * 2))

        # block alignment
        self.file.write(struct.pack("<H", 2))

        # bits per sample
        self.file.write(struct.pack("<H", 16))

        self.file.write(b"data")
        self.file.write(struct.pack("<I", audio_data_len))

    def write(self, sample_rate: int, audio_data):
        self._write_header(sample_rate, len(audio_data))
        self.file.write(audio_data)


class GCAXExtracter:
    audio_data_offset: int
    file_entries_offset: int

    def __init__(self, dsptool, input_path: str):
        self.dsptool = dsptool
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

    def _extract_adpcm(self):
        file_entry = FileEntry.from_buffer_copy(
            self.file.read(sizeof(FileEntry)))
        last_offset = self.file.tell()

        self.file.seek(self.audio_data_offset + file_entry.start_offset)
        adpcm_data = self.file.read(file_entry.data_size)

        # calculate sample count
        SAMPLES_PER_FRAME = 14
        BYTES_PER_FRAME = 8
        frame_count = file_entry.data_size // BYTES_PER_FRAME
        sample_count = frame_count * SAMPLES_PER_FRAME

        # setup info coefs
        info = ADPCMINFO()
        info.coef = (c_int16 * 16)(*file_entry.coef)

        # setup buffers
        pcm_buf_size = self.dsptool.getBytesForPcmBuffer(
            c_uint32(sample_count))
        out_pcm_buf = (c_int16 * (pcm_buf_size // 2))()

        in_adpcm_buf = (c_uint8 * file_entry.data_size)(*adpcm_data)

        # decode
        self.dsptool.decode(byref(in_adpcm_buf), byref(
            out_pcm_buf), byref(info), c_uint32(sample_count))

        self.file.seek(last_offset)

        return bytes(out_pcm_buf), file_entry.sample_rate

    def extract_to_folder(self, folder: str):
        # read necessary info from dtpk file
        self.file.seek(0x1C)
        self.audio_data_offset = self._read_u32()

        self.file.seek(0xB8)
        self.file_entries_offset = self._read_u32()

        # make output folder if necessary
        folder = pathlib.Path(folder)

        if folder.exists() and folder.is_file():
            raise GeneralException(GeneralExceptionEnum.OutputIsFile)

        folder.mkdir(exist_ok=True)

        self.file.seek(self.file_entries_offset)
        audio_file_count = self._read_u32() + 1

        print(f"{termcolors.OKCYAN}Found {audio_file_count} audio files.")
        print(f"Extracting...{termcolors.ENDC}")
        print()

        # extract audio files
        for i in range(audio_file_count):
            audio_data, sample_rate = self._extract_adpcm()
            with WAVWriter(folder / f"{i}_Sound.wav") as writer:
                writer.write(sample_rate, audio_data)
