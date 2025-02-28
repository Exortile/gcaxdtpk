# GCAXDTPK

This repo contains a Python script that generates a GameCube DTPK sound bank from .WAV files. Widely tested and confirmed working in Sonic Riders.

## Dependencies

* Nintendo's dsptool.dll. *(NOTE: If you're running Python as 64-bit, the .dll has to be 64-bit as well and vice versa.)* **[Also, I cannot pass this library through this repository. Find your own way of obtaining this.]**
* python3

## Usage

Keep in mind, this is a command-line tool, so this may make it a little bit harder to use for newbies.

General export command:

    python gcaxdtpk.py export pathToFolder fileIdentifier [output]

If `[output]` isn't specified at the end of the command, the generated file will be in the same folder as the input folder, with the same name as the folder itself, but with `.DAT` added to the end.

This tool can also be used to extract the audio files out of a DTPK archive, and to also view information on them.

General extract command:

    python gcaxdtpk.py extract input output

General info command:

    python gcaxdtpk.py info input

You can also display the help output via these commands:

    python gcaxdtpk.py -h
    python gcaxdtpk.py --help

If you wish to see help about each subcommand and how to use them you can do so like this, for example:

    python gcaxdtpk.py export -h
    python gcaxdtpk.py export --help
    python gcaxdtpk.py extract -h

