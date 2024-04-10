import pytest

from diffpy.labpdfproc.functions import Gridded_circle

params1 = [
    ([0.5, 3, 1], {(0.0, -0.5), (0.0, 0.0), (0.5, 0.0), (-0.5, 0.0), (0.0, 0.5)}),
    ([1, 4, 1], {(-0.333333, -0.333333), (0.333333, -0.333333), (-0.333333, 0.333333), (0.333333, 0.333333)}),
]


@pytest.mark.parametrize("inputs, expected", params1)
def test_get_grid_points(inputs, expected):
    expected_grid = expected
    actual_gs = Gridded_circle(radius=inputs[0], n_points_on_diameter=inputs[1], mu=inputs[2])
    actual_grid_sorted = sorted(actual_gs.grid)
    expected_grid_sorted = sorted(expected_grid)
    for actual_point, expected_point in zip(actual_grid_sorted, expected_grid_sorted):
        assert actual_point == pytest.approx(expected_point, rel=1e-4, abs=1e-6)


params3 = [
    ([1, 3, 1, 45], [1, 0.135335, 0.135335, 0.2431167, 0.2431167]),
    ([1, 3, 1, 90], [1, 1, 0.135335, 0.135335, 0.135335]),
    ([1, 3, 1, 120], [1, 1, 0.135335, 0.049787, 0.176921]),
]


@pytest.mark.parametrize("inputs, expected", params3)
def test_set_distances_at_angle(inputs, expected):
    expected_muls = expected
    actual_gs = Gridded_circle(radius=inputs[0], n_points_on_diameter=inputs[1], mu=inputs[2])
    actual_gs.set_distances_at_angle(inputs[3])
    actual_gs.set_muls_at_angle(inputs[3])
    actual_muls_sorted = sorted(actual_gs.muls)
    expected_muls_sorted = sorted(expected_muls)
    assert actual_muls_sorted == pytest.approx(expected_muls_sorted, rel=1e-4, abs=1e-6)
