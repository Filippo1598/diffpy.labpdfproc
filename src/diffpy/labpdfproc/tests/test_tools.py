import json
import os
import re
from pathlib import Path

import pytest

from diffpy.labpdfproc.labpdfprocapp import get_args
from diffpy.labpdfproc.tools import (
    known_sources,
    load_user_info,
    load_user_metadata,
    set_input_lists,
    set_output_directory,
    set_wavelength,
)

# Use cases can be found here: https://github.com/diffpy/diffpy.labpdfproc/issues/48

# This test covers existing single input file, directory, a file list, and multiple files
# We store absolute path into input_directory and file names into input_file
params_input = [
    (["good_data.chi"], ["good_data.chi"]),  # single good file, same directory
    (["input_dir/good_data.chi"], ["input_dir/good_data.chi"]),  # single good file, input directory
    (  # glob current directory
        ["."],
        ["good_data.chi", "good_data.xy", "good_data.txt", "unreadable_file.txt", "binary.pkl"],
    ),
    (  # glob input directory
        ["./input_dir"],
        [
            "input_dir/good_data.chi",
            "input_dir/good_data.xy",
            "input_dir/good_data.txt",
            "input_dir/unreadable_file.txt",
            "input_dir/binary.pkl",
        ],
    ),
    (  # glob list of input directories
        [".", "./input_dir"],
        [
            "./good_data.chi",
            "./good_data.xy",
            "./good_data.txt",
            "./unreadable_file.txt",
            "./binary.pkl",
            "input_dir/good_data.chi",
            "input_dir/good_data.xy",
            "input_dir/good_data.txt",
            "input_dir/unreadable_file.txt",
            "input_dir/binary.pkl",
        ],
    ),
    (  # file_list_example2.txt list of files provided in different directories with wildcard
        ["input_dir/file_list_example2.txt"],
        ["input_dir/good_data.chi", "good_data.xy", "input_dir/good_data.txt", "input_dir/unreadable_file.txt"],
    ),
    (  # wildcard pattern, matching files with .chi extension in the same directory
        ["./*.chi"],
        ["good_data.chi"],
    ),
    (  # wildcard pattern, matching files with .chi extension in the input directory
        ["input_dir/*.chi"],
        ["input_dir/good_data.chi"],
    ),
    (  # wildcard pattern, matching files starting with good_data
        ["good_data*"],
        ["good_data.chi", "good_data.xy", "good_data.txt"],
    ),
]


@pytest.mark.parametrize("inputs, expected", params_input)
def test_set_input_lists(inputs, expected, user_filesystem):
    base_dir = Path(user_filesystem)
    os.chdir(base_dir)
    expected_paths = [base_dir.resolve() / expected_path for expected_path in expected]

    cli_inputs = ["2.5"] + inputs
    actual_args = get_args(cli_inputs)
    actual_args = set_input_lists(actual_args)
    assert sorted(actual_args.input_paths) == sorted(expected_paths)


# This test covers non-existing single input file or directory, in this case we raise an error with message
params_input_bad = [
    (
        ["non_existing_file.xy"],
        "Cannot find non_existing_file.xy. Please specify valid input file(s) or directories.",
    ),
    (
        ["./input_dir/non_existing_file.xy"],
        "Cannot find ./input_dir/non_existing_file.xy. Please specify valid input file(s) or directories.",
    ),
    (["./non_existing_dir"], "Cannot find ./non_existing_dir. Please specify valid input file(s) or directories."),
    (  # list of files provided (with missing files)
        ["good_data.chi", "good_data.xy", "unreadable_file.txt", "missing_file.txt"],
        "Cannot find missing_file.txt. Please specify valid input file(s) or directories.",
    ),
    (  # file_list.txt list of files provided (with missing files)
        ["input_dir/file_list.txt"],
        "Cannot find missing_file.txt. Please specify valid input file(s) or directories.",
    ),
]


@pytest.mark.parametrize("inputs, msg", params_input_bad)
def test_set_input_files_bad(inputs, msg, user_filesystem):
    base_dir = Path(user_filesystem)
    os.chdir(base_dir)
    cli_inputs = ["2.5"] + inputs
    actual_args = get_args(cli_inputs)
    with pytest.raises(FileNotFoundError, match=msg[0]):
        actual_args = set_input_lists(actual_args)


params1 = [
    ([], ["."]),
    (["--output-directory", "."], ["."]),
    (["--output-directory", "new_dir"], ["new_dir"]),
    (["--output-directory", "input_dir"], ["input_dir"]),
]


@pytest.mark.parametrize("inputs, expected", params1)
def test_set_output_directory(inputs, expected, user_filesystem):
    os.chdir(user_filesystem)
    expected_output_directory = Path(user_filesystem) / expected[0]
    cli_inputs = ["2.5", "data.xy"] + inputs
    actual_args = get_args(cli_inputs)
    actual_args.output_directory = set_output_directory(actual_args)
    assert actual_args.output_directory == expected_output_directory
    assert Path(actual_args.output_directory).exists()
    assert Path(actual_args.output_directory).is_dir()


def test_set_output_directory_bad(user_filesystem):
    os.chdir(user_filesystem)
    cli_inputs = ["2.5", "data.xy", "--output-directory", "good_data.chi"]
    actual_args = get_args(cli_inputs)
    with pytest.raises(FileExistsError):
        actual_args.output_directory = set_output_directory(actual_args)
        assert Path(actual_args.output_directory).exists()
        assert not Path(actual_args.output_directory).is_dir()


params2 = [
    ([], [0.71]),
    (["--anode-type", "Ag"], [0.59]),
    (["--wavelength", "0.25"], [0.25]),
    (["--wavelength", "0.25", "--anode-type", "Ag"], [0.25]),
]


@pytest.mark.parametrize("inputs, expected", params2)
def test_set_wavelength(inputs, expected):
    expected_wavelength = expected[0]
    cli_inputs = ["2.5", "data.xy"] + inputs
    actual_args = get_args(cli_inputs)
    actual_args.wavelength = set_wavelength(actual_args)
    assert actual_args.wavelength == expected_wavelength


params3 = [
    (
        ["--anode-type", "invalid"],
        [f"Anode type not recognized. Please rerun specifying an anode_type from {*known_sources, }."],
    ),
    (
        ["--wavelength", "0"],
        ["No valid wavelength. Please rerun specifying a known anode_type or a positive wavelength."],
    ),
    (
        ["--wavelength", "-1", "--anode-type", "Mo"],
        ["No valid wavelength. Please rerun specifying a known anode_type or a positive wavelength."],
    ),
]


@pytest.mark.parametrize("inputs, msg", params3)
def test_set_wavelength_bad(inputs, msg):
    cli_inputs = ["2.5", "data.xy"] + inputs
    actual_args = get_args(cli_inputs)
    with pytest.raises(ValueError, match=re.escape(msg[0])):
        actual_args.wavelength = set_wavelength(actual_args)


params5 = [
    ([], []),
    (
        ["--user-metadata", "facility=NSLS II", "beamline=28ID-2", "favorite color=blue"],
        [["facility", "NSLS II"], ["beamline", "28ID-2"], ["favorite color", "blue"]],
    ),
    (["--user-metadata", "x=y=z"], [["x", "y=z"]]),
]


@pytest.mark.parametrize("inputs, expected", params5)
def test_load_user_metadata(inputs, expected):
    expected_args = get_args(["2.5", "data.xy"])
    for expected_pair in expected:
        setattr(expected_args, expected_pair[0], expected_pair[1])
    delattr(expected_args, "user_metadata")

    cli_inputs = ["2.5", "data.xy"] + inputs
    actual_args = get_args(cli_inputs)
    actual_args = load_user_metadata(actual_args)
    assert actual_args == expected_args


params6 = [
    (
        ["--user-metadata", "facility=", "NSLS II"],
        [
            "Please provide key-value pairs in the format key=value. "
            "For more information, use `labpdfproc --help.`"
        ],
    ),
    (
        ["--user-metadata", "favorite", "color=blue"],
        "Please provide key-value pairs in the format key=value. "
        "For more information, use `labpdfproc --help.`",
    ),
    (
        ["--user-metadata", "beamline", "=", "28ID-2"],
        "Please provide key-value pairs in the format key=value. "
        "For more information, use `labpdfproc --help.`",
    ),
    (
        ["--user-metadata", "facility=NSLS II", "facility=NSLS III"],
        "Please do not specify repeated keys: facility. ",
    ),
    (
        ["--user-metadata", "wavelength=2"],
        "wavelength is a reserved name.  Please rerun using a different key name. ",
    ),
]


@pytest.mark.parametrize("inputs, msg", params6)
def test_load_user_metadata_bad(inputs, msg):
    cli_inputs = ["2.5", "data.xy"] + inputs
    actual_args = get_args(cli_inputs)
    with pytest.raises(ValueError, match=msg[0]):
        actual_args = load_user_metadata(actual_args)


def _setup_dirs(monkeypatch, user_filesystem):
    cwd = Path(user_filesystem)
    home_dir = cwd / "home_dir"
    monkeypatch.setattr("pathlib.Path.home", lambda _: home_dir)
    os.chdir(cwd)
    return home_dir


def _run_tests(inputs, expected):
    expected_username, expected_email = expected
    cli_inputs = ["2.5", "data.xy", "--username", inputs[0], "--email", inputs[1]]
    actual_args = get_args(cli_inputs)
    actual_args = load_user_info(actual_args)
    assert actual_args.username == expected_username
    assert actual_args.email == expected_email


params_user_info_with_home_conf_file = [
    (["", ""], ["home_username", "home@email.com"]),
    (["cli_username", ""], ["cli_username", "home@email.com"]),
    (["", "cli@email.com"], ["home_username", "cli@email.com"]),
    ([None, None], ["home_username", "home@email.com"]),
    (["cli_username", None], ["cli_username", "home@email.com"]),
    ([None, "cli@email.com"], ["home_username", "cli@email.com"]),
    (["cli_username", "cli@email.com"], ["cli_username", "cli@email.com"]),
]
params_user_info_with_local_conf_file = [
    (["", ""], ["cwd_username", "cwd@email.com"]),
    (["cli_username", ""], ["cli_username", "cwd@email.com"]),
    (["", "cli@email.com"], ["cwd_username", "cli@email.com"]),
    ([None, None], ["cwd_username", "cwd@email.com"]),
    (["cli_username", None], ["cli_username", "cwd@email.com"]),
    ([None, "cli@email.com"], ["cwd_username", "cli@email.com"]),
    (["cli_username", "cli@email.com"], ["cli_username", "cli@email.com"]),
]
params_user_info_with_no_home_conf_file = [
    (
        [None, None],
        ["input_username", "input@email.com"],
        ["input_username", "input@email.com"],
    ),
    (
        ["cli_username", None],
        ["", "input@email.com"],
        ["cli_username", "input@email.com"],
    ),
    (
        [None, "cli@email.com"],
        ["input_username", ""],
        ["input_username", "cli@email.com"],
    ),
    (
        ["", ""],
        ["input_username", "input@email.com"],
        ["input_username", "input@email.com"],
    ),
    (
        ["cli_username", ""],
        ["", "input@email.com"],
        ["cli_username", "input@email.com"],
    ),
    (
        ["", "cli@email.com"],
        ["input_username", ""],
        ["input_username", "cli@email.com"],
    ),
    (
        ["cli_username", "cli@email.com"],
        ["input_username", "input@email.com"],
        ["cli_username", "cli@email.com"],
    ),
]
params_user_info_no_conf_file_no_inputs = [
    ([None, None], ["", ""], ["", ""]),
]


@pytest.mark.parametrize("inputs, expected", params_user_info_with_home_conf_file)
def test_load_user_info_with_home_conf_file(monkeypatch, inputs, expected, user_filesystem):
    _setup_dirs(monkeypatch, user_filesystem)
    _run_tests(inputs, expected)


@pytest.mark.parametrize("inputs, expected", params_user_info_with_local_conf_file)
def test_load_user_info_with_local_conf_file(monkeypatch, inputs, expected, user_filesystem):
    _setup_dirs(monkeypatch, user_filesystem)
    local_config_data = {"username": "cwd_username", "email": "cwd@email.com"}
    with open(Path(user_filesystem) / "diffpyconfig.json", "w") as f:
        json.dump(local_config_data, f)
    _run_tests(inputs, expected)
    os.remove(Path().home() / "diffpyconfig.json")
    _run_tests(inputs, expected)


@pytest.mark.parametrize("inputsa, inputsb, expected", params_user_info_with_no_home_conf_file)
def test_load_user_info_with_no_home_conf_file(monkeypatch, inputsa, inputsb, expected, user_filesystem):
    _setup_dirs(monkeypatch, user_filesystem)
    os.remove(Path().home() / "diffpyconfig.json")
    inp_iter = iter(inputsb)
    monkeypatch.setattr("builtins.input", lambda _: next(inp_iter))
    _run_tests(inputsa, expected)
    confile = Path().home() / "diffpyconfig.json"
    assert confile.is_file()


@pytest.mark.parametrize("inputsa, inputsb, expected", params_user_info_no_conf_file_no_inputs)
def test_load_user_info_no_conf_file_no_inputs(monkeypatch, inputsa, inputsb, expected, user_filesystem):
    _setup_dirs(monkeypatch, user_filesystem)
    os.remove(Path().home() / "diffpyconfig.json")
    inp_iter = iter(inputsb)
    monkeypatch.setattr("builtins.input", lambda _: next(inp_iter))
    _run_tests(inputsa, expected)
    confile = Path().home() / "diffpyconfig.json"
    assert confile.exists() is False
