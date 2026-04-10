from src.config import DATA_PROCESSING_REFERENCE_FIGURES
from src.plot_city_points import plot_city_points


def test_plot_city_points_writes_figure():
    out_path = DATA_PROCESSING_REFERENCE_FIGURES / "study_city_points.png"

    if out_path.exists():
        out_path.unlink()

    plot_city_points()

    assert out_path.exists()
