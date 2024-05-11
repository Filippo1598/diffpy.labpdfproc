import sys
from argparse import ArgumentParser

from diffpy.labpdfproc.functions import apply_corr, compute_cve
from diffpy.labpdfproc.tools import (
    expand_list_file,
    known_sources,
    load_user_metadata,
    set_input_lists,
    set_output_directory,
    set_wavelength,
)
from diffpy.utils.parsers.loaddata import loadData
from diffpy.utils.scattering_objects.diffraction_objects import XQUANTITIES, Diffraction_object


def get_args(override_cli_inputs=None):
    p = ArgumentParser()
    p.add_argument("mud", help="Value of mu*D for your " "sample. Required.", type=float)
    p.add_argument(
        "input",
        nargs="+",
        help="The filename(s) or folder(s) of the datafile(s) to load.  "
        "Required.\nSupply a space-separated list of files or directories."
        "Long lists can be supplied, one per line, in a file with name "
        "file_list.txt. If one or more directory is provided, all valid "
        "data-files in that directory will be processed. Examples of valid "
        "inputs are 'file.xy', 'data/file.xy', 'file.xy, data/file.xy', "
        "'.' (load everything in the current directory), 'data' (load"
        "everything in the folder ./data), 'data/file_list.txt' (load"
        " the list of files contained in the text-file called "
        "file_list.txt that can be found in the folder ./data).",
    )
    p.add_argument(
        "-a",
        "--anode-type",
        help=f"The type of the x-ray source. Allowed values are "
        f"{*[known_sources], }. Either specify a known x-ray source or specify wavelength.",
        default="Mo",
    )
    p.add_argument(
        "-w",
        "--wavelength",
        help="X-ray source wavelength in angstroms. Not needed if the anode-type "
        "is specified. This wavelength will override the anode wavelength if both are specified.",
        default=None,
        type=float,
    )
    p.add_argument(
        "-o",
        "--output-directory",
        help="The name of the output directory. If not specified "
        "then corrected files will be written to the current directory."
        "If the specified directory doesn't exist it will be created.",
        default=None,
    )
    p.add_argument(
        "-x",
        "--xtype",
        help=f"The quantity on the independent variable axis. Allowed "
        f"values: {*XQUANTITIES, }. If not specified then two-theta "
        f"is assumed for the independent variable. Only implemented for "
        f"tth currently.",
        default="tth",
    )
    p.add_argument(
        "-c",
        "--output-correction",
        action="store_true",
        help="The absorption correction will be output to a file if this "
        "flag is set. Default is that it is not output.",
        default="tth",
    )
    p.add_argument(
        "-f",
        "--force-overwrite",
        action="store_true",
        help="Outputs will not overwrite existing file unless --force is specified.",
    )
    p.add_argument(
        "-u",
        "--user-metadata",
        metavar="KEY=VALUE",
        nargs="+",
        help="Specify key-value pairs to be loaded into metadata using the format key=value. "
        "Separate pairs with whitespace, and ensure no whitespaces before or after the = sign. "
        "Avoid using = in keys. If multiple = signs are present, only the first separates the key and value. "
        "If a key or value contains whitespace, enclose it in quotes. "
        "For example, facility='NSLS II', 'facility=NSLS II', beamline=28ID-2, "
        "'beamline'='28ID-2', 'favorite color'=blue, are all valid key=value items. ",
    )
    args = p.parse_args(override_cli_inputs)
    return args


def main():
    args = get_args()
    args = expand_list_file(args)
    args = set_input_lists(args)
    args.output_directory = set_output_directory(args)
    args.wavelength = set_wavelength(args)
    args = load_user_metadata(args)

    for filepath in args.input_directory:
        outfilestem = filepath.stem + "_corrected"
        corrfilestem = filepath.stem + "_cve"
        outfile = args.output_directory / (outfilestem + ".chi")
        corrfile = args.output_directory / (corrfilestem + ".chi")

        if outfile.exists() and not args.force_overwrite:
            sys.exit(
                f"Output file {str(outfile)} already exists. Please rerun "
                f"specifying -f if you want to overwrite it."
            )
        if corrfile.exists() and args.output_correction and not args.force_overwrite:
            sys.exit(
                f"Corrections file {str(corrfile)} was requested and already "
                f"exists. Please rerun specifying -f if you want to overwrite it."
            )

        input_pattern = Diffraction_object(wavelength=args.wavelength)
        xarray, yarray = loadData(args.input_file, unpack=True)
        input_pattern.insert_scattering_quantity(
            xarray,
            yarray,
            "tth",
            scat_quantity="x-ray",
            name=str(args.input_file),
            metadata={"muD": args.mud, "anode_type": args.anode_type},
        )

        absorption_correction = compute_cve(input_pattern, args.mud, args.wavelength)
        corrected_data = apply_corr(input_pattern, absorption_correction)
        corrected_data.name = f"Absorption corrected input_data: {input_pattern.name}"
        corrected_data.dump(f"{outfile}", xtype="tth")

        if args.output_correction:
            absorption_correction.dump(f"{corrfile}", xtype="tth")


if __name__ == "__main__":
    main()
