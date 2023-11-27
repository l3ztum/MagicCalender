from .. import magic_calender as mc
import numpy as np


def test_grid_coords(example_config, example_img):
    print(example_config)
    grid = mc.Grid(example_config)
    grid._cal = np.array(
        [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    )
    assert (
        mc.Box(
            mc.Point(0, example_config.header_spacing_px),
            mc.Point(250, example_config.header_spacing_px + 250),
        ).as_tuple()
        == grid._coords_from_index(0, 0).as_tuple()
    )
    assert (0, 350, 250, 600) == grid.get_coords_to_draw(5).as_tuple()
    grid.draw(example_img)
