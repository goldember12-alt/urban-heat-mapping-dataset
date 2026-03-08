from src.config import FIGURES
from src.plot_city_points import plot_city_points


def test_plot_city_points_writes_figure():
    out_path = FIGURES / "study_city_points.png"

    if out_path.exists():
        out_path.unlink()

    plot_city_points()

    assert out_path.exists()