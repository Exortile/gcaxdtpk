from enum import Enum

class WAVExceptionEnum(Enum):
    InvalidFileFormatRIFF = 0,
    InvalidFileFormatWAVE = 1,
    NotEncodedInPCM = 2,
    NotEncodedInMonoChannel = 3,
    NotEncodedIn16Bit = 4

class GeneralExceptionEnum(Enum):
    NonDirectory = 0,
    InvalidFileIdentifier = 1,
    InvalidTypeFileIdentifier = 2

class GeneralException(Exception):
    messages = {
        GeneralExceptionEnum.NonDirectory : "Input path is not a directory.",
        GeneralExceptionEnum.InvalidFileIdentifier : "Invalid file identifier provided.",
        GeneralExceptionEnum.InvalidTypeFileIdentifier : "The file identifier has to be a short (16 bit value)."
    }

    def __init__(self, exception_enum):
        self.message = self.messages.get(exception_enum)
        super().__init__(self.message)

class WAVException(Exception):
    messages = {
        WAVExceptionEnum.InvalidFileFormatRIFF : "Invalid WAV file: {}. Needs to be encoded in the RIFF format.",
        WAVExceptionEnum.InvalidFileFormatWAVE : "Invalid WAV file: {}. This is not a .wav file.",
        WAVExceptionEnum.NotEncodedInPCM : "WAV file {} is not formatted using PCM.",
        WAVExceptionEnum.NotEncodedInMonoChannel : "WAV file {} is not in mono channel.",
        WAVExceptionEnum.NotEncodedIn16Bit : "WAV file {} is not encoded in signed 16-bit.",
    }

    def __init__(self, exception_enum, filename):
        message = self.messages.get(exception_enum)
        self.message = message.format(filename)
        super().__init__(self.message)