import numpy as np

from lib.box import Box
from lib.grid import Grid
from lib.point import Point

def test_grid_coords(example_config, example_img):
    print(example_config)
    grid = Grid(example_config)
    grid._cal = np.array(
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    )
    assert (
        Box(
            Point(0, example_config.header_spacing_px),
            Point(250, example_config.header_spacing_px + 250),
        ).as_tuple()
        == grid._coords_from_index(0, 0).as_tuple()
    )
    assert (0, 350, 250, 600) == grid.get_coords_to_draw(5).as_tuple()
    grid.draw(example_img)

def test_grid_coords_multiday(example_config, example_img):
    print(example_config)
    grid = Grid(example_config)
    grid._cal = np.array(
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    )
    assert (
        Box(
            Point(0, example_config.header_spacing_px),
            Point(1000, example_config.header_spacing_px + 250),
        ).as_tuple()
        == grid._coords_from_index(0, 0, 4).as_tuple()
    )
    assert (0, 350, 500, 600) == grid.get_coords_to_draw(5,2).as_tuple()
    assert (250, example_config.header_spacing_px, 750, example_config.header_spacing_px + 250) == grid.get_coords_to_draw(2,2).as_tuple()
    assert (250, example_config.header_spacing_px, 750, example_config.header_spacing_px + 250) == grid.get_coords_to_draw(2,2).as_tuple()
    grid.draw(example_img)

def test_weekend(example_grid):
    assert example_grid.is_weekend(17)

