from enum import Enum


class WAVExceptionEnum(Enum):
    InvalidFileFormatRIFF = 0,
    InvalidFileFormatWAVE = 1,
    NotEncodedInPCM = 2,
    NotEncodedInMonoChannel = 3,
    NotEncodedIn16Bit = 4


class GeneralExceptionEnum(Enum):
    NonDirectory = 0,
    OutputIsDirectory = 1,
    InvalidFileIdentifier = 2,
    InvalidTypeFileIdentifier = 3,
    InvalidFilenameFormat = 4,
    NoFiles = 5,
    NonFile = 6,
    OutputIsFile = 7,


class GeneralException(Exception):
    messages = {
        GeneralExceptionEnum.NonDirectory: "Input path is not a directory.",
        GeneralExceptionEnum.OutputIsDirectory: "Output path is an already existing directory.",
        GeneralExceptionEnum.InvalidFileIdentifier: "Invalid file identifier provided.",
        GeneralExceptionEnum.InvalidTypeFileIdentifier: "The file identifier has to be a short (16 bit value).",
        GeneralExceptionEnum.InvalidFilenameFormat: ("The given .wav files "
                                                     "have an incorrect filename format. "
                                                     "Did you specify the order of them in the filename?"),
        GeneralExceptionEnum.NoFiles: "The given input folder has no .wav files in it.",
        GeneralExceptionEnum.NonFile: "Input path is not a file.",
        GeneralExceptionEnum.OutputIsFile: "Output path is an already existing file."
    }

    def __init__(self, exception_enum):
        self.message = self.messages.get(exception_enum)
        super().__init__(self.message)


class WAVException(Exception):
    messages = {
        WAVExceptionEnum.InvalidFileFormatRIFF: "Invalid WAV file: {}. Needs to be encoded in the RIFF format.",
        WAVExceptionEnum.InvalidFileFormatWAVE: "Invalid WAV file: {}. This is not a .wav file.",
        WAVExceptionEnum.NotEncodedInPCM: "WAV file {} is not formatted using PCM.",
        WAVExceptionEnum.NotEncodedInMonoChannel: "WAV file {} is not in mono channel.",
        WAVExceptionEnum.NotEncodedIn16Bit: "WAV file {} is not encoded in signed 16-bit.",
    }

    def __init__(self, exception_enum, filename):
        message = self.messages.get(exception_enum)
        self.message = message.format(filename)
        super().__init__(self.message)


class GCAXException(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(msg)
