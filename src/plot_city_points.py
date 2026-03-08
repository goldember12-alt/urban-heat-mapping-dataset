import matplotlib.pyplot as plt

from src.config import FIGURES
from src.make_city_points import make_city_points


def plot_city_points() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    gdf = make_city_points()

    fig, ax = plt.subplots(figsize=(10, 6))
    gdf.plot(ax=ax, markersize=20)
    ax.set_title("Study City Points")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    out_path = FIGURES / "study_city_points.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)