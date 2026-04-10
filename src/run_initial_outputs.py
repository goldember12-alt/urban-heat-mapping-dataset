from src.config import DATA_PROCESSING_REFERENCE_FIGURES, DATA_PROCESSED
from src.plot_city_points import plot_city_points
from src.save_city_points import save_city_points


def main() -> None:
    save_city_points()
    plot_city_points()

    print(DATA_PROCESSED / "city_points" / "city_points.gpkg")
    print(DATA_PROCESSING_REFERENCE_FIGURES / "study_city_points.png")


if __name__ == "__main__":
    main()
