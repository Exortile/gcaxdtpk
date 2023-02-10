# GCAXDTPK

This repo contains a Python script that generates a GameCube DTPK sound bank from .WAV files. Widely tested and confirmed working in Sonic Riders.

## Dependencies

* Nintendo's dsptool.dll **(I cannot pass this library through this repository. Find your own way of obtaining this.)**
* python3

## Usage

Keep in mind, this is a command-line tool, so this may make it a little bit harder to use for newbies.

General command:

    python gcaxdtpk.py pathToFolder fileIdentifier [output]

If `[output]` isn't specified at the end of the command, the generated file will be in the same folder, with the same name as the folder itself, but with `.DAT` added to the end.

`pathToFolder`:

    Path to a folder that contains WAV files to be put into the DTPK archive. The WAV files must be named according to this format: "0_name.wav". This way the tool knows in which order should the WAV files go into the DTPK archive. The WAV file must also be encoded using signed 16-bit PCM, it must only be in mono channel and with a sample rate of 44100 Hz. Other sample rates may work, but aren't guaranteed.

`fileIdentifier`:

    Used as a unique identifier to determine what file is which in terms of other DTPK archives loaded in the game. For example, calling audio with the ID 0xA9320200, means that the identifier in this case is 0xA932.

`output`:

    Path to where the file should be saved, along with the filename.

You can also display the help output via these commands:

    python gcaxdtpk.py -h
    python gcaxdtpk.py --help