from unittest.mock import MagicMock

import pytest

from diffpy.labpdfproc.tools import set_wavelength

WAVELENGTHS = {"Mo": 0.71, "Ag": 0.59, "Cu": 1.54}

params1 = [
    ([None, None], [0.71]),
    ([None, "Ag"], [0.59]),
    ([0.25, "Ag"], [0.25]),
    ([0.25, None], [0.25]),
]


@pytest.mark.parametrize("inputs, expected", params1)
def test_set_wavelength(inputs, expected):
    expected_wavelength = expected[0]
    actual_args = MagicMock()
    actual_args.wavelength, actual_args.anode_type = inputs[0], inputs[1]
    actual_wavelength = set_wavelength(actual_args)
    assert actual_wavelength == expected_wavelength
