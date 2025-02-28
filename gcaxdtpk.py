import argparse
import gcax_classes

from gcax_classes import termcolors

from exceptions import (
    GeneralException,
    WAVException,
    GCAXException
)

from export import GCAXExporter
from extract import GCAXExtracter
from parser import GCAXParser
from ctypes import cdll


def init_dll(parser: argparse.ArgumentParser):
    try:
        dllpath = gcax_classes.get_path_in_script_dir("dsptool.dll")
        return cdll.LoadLibrary(str(dllpath))
    except FileNotFoundError:
        parser.exit(
            3, f"{termcolors.FAIL}\nError: Can't find dsptool.dll in the script directory!\n{termcolors.ENDC}")
    except OSError:
        parser.exit(
            3, f"{termcolors.FAIL}\nError: Something went wrong loading dsptool.dll. The file is most likely incompatible with your system.\n{termcolors.ENDC}")


def format_exception_error(cls_name: str, exc: Exception) -> str:
    return f"{termcolors.FAIL}{cls_name} Error:\n\t{exc.message}\n\n{termcolors.ENDC}"


def export(parser: argparse.ArgumentParser, args: argparse.Namespace):
    input = args.input
    output = args.output
    if output is None:
        output = input + '.DAT'

    file_identifier = args.file_identifier
    dsptool = init_dll(parser)

    try:
        print()

        exporter = GCAXExporter(dsptool, input, file_identifier, output)
        exporter.run()

        print(f"{termcolors.OKGREEN}Exporter Message:")
        print(f"\tSuccessfully exported to {output}{termcolors.ENDC}")

        print()
    except GeneralException as exc:
        parser.exit(1, format_exception_error("Exporter", exc))
    except WAVException as exc:
        parser.exit(2, format_exception_error("WAV File", exc))


def extract(parser: argparse.ArgumentParser, args: argparse.Namespace):
    input_path = args.input
    output_path = args.output
    dsptool = init_dll(parser)

    try:
        print()

        with GCAXExtracter(dsptool, input_path) as extracter:
            extracter.extract_to_folder(output_path)

        print(f"{termcolors.OKGREEN}Extracter Message:")
        print(
            f"\tSuccessfully extracted audio files to {output_path}{termcolors.ENDC}")

        print()
    except GeneralException as exc:
        parser.exit(1, format_exception_error("Extracter", exc))
    except GCAXException as exc:
        parser.exit(2, format_exception_error("Extracter", exc))


def info_function(parser: argparse.ArgumentParser, args: argparse.Namespace):
    input_path = args.input

    try:
        print()

        with GCAXParser(input_path) as gcax_parser:
            gcax_parser.parse_and_print()

        print()
    except GeneralException as exc:
        parser.exit(1, format_exception_error("Parser", exc))
    except GCAXException as exc:
        parser.exit(2, format_exception_error("Parser", exc))


def main():
    parser = argparse.ArgumentParser(
        description="A tool used for working with DTPK soundbanks (a proprietary file format) for the GameCube version of Sonic Riders. These soundbank files commonly have a .DAT file extension. This tool can export, extract and view information on these files.")
    subparsers = parser.add_subparsers(
        title="subcommands", required=True)

    # Subparser for parsing arguments for exporting
    export_parser = subparsers.add_parser(
        "export", help="Create a new DTPK file from the given .wav files")
    export_parser.add_argument('input', type=str,
                               help='Path to a folder that contains WAV files to be put into the DTPK archive. The WAV files must be named according to this format: "0_name.wav". This way the tool knows in which order should the WAV files go into the DTPK archive. The WAV file must also be encoded using signed 16-bit PCM, it must only be in mono channel and with a sample rate of 44100 Hz. Other sample rates may work, but aren\'t guaranteed.')
    export_parser.add_argument('file_identifier', type=str,
                               help="Used as a unique identifier to determine what file is which in terms of other DTPK archives loaded in the game. For example, calling audio with the ID 0xA9320200, means that the identifier in this case is 0xA932. You can find a specific DTPK archive's file identifier by using the info subcommand.")
    export_parser.add_argument('output', type=str, nargs='?',
                               help='Path to where the file should be saved, along with the filename. Optional.')
    export_parser.set_defaults(func=export)

    # Subparser for parsing arguments for extracting audio from a DAT file
    extract_parser = subparsers.add_parser(
        "extract", help="Extract all audio files as .wav files from a DTPK file")
    extract_parser.add_argument(
        'input', type=str, help='Path to the DTPK file to extract audio files from.')
    extract_parser.add_argument(
        'output', type=str, help="Path to the folder to save all the extracted audio files to. If the folder doesn't exist, it will be created.")
    extract_parser.set_defaults(func=extract)

    # Subparser for parsing arguments for getting information from a DAT file
    info_parser = subparsers.add_parser(
        "info", help="Print out information about the given DTPK file")
    info_parser.add_argument(
        'input', type=str, help='Path to the DTPK file to print out information about.')
    info_parser.set_defaults(func=info_function)

    parsedargs = parser.parse_args()
    parsedargs.func(parser, parsedargs)


if __name__ == "__main__":
    main()
