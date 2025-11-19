import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# ---------- CONFIG ----------
YEAR = 2026
BASE_DIR = Path("data") / "NWS Data"   # where the NWS Data folder lives
IMG_DIR = Path("docs") / "img"         # where PNGs for the website go
# -----------------------------


def get_available_cities(base_dir: Path):
    """Return a sorted list of city folder names under NWS Data."""
    if not base_dir.exists():
        raise FileNotFoundError(
            f"Base directory '{base_dir}' not found. "
            "Make sure the 'data/NWS Data' folder exists and contains city subfolders."
        )
    cities = [p.name for p in base_dir.iterdir() if p.is_dir()]
    if not cities:
        raise RuntimeError(f"No city folders found under '{base_dir}'.")
    return sorted(cities)


def ask_for_city(cities):
    """Prompt user for a city name until a valid one is entered."""
    print("Available cities:")
    for c in cities:
        print(f"  - {c}")
    print()

    city_lookup = {c.lower(): c for c in cities}

    while True:
        user_input = input("Enter city name (not case-sensitive, choose from above): ").strip().lower()
        if user_input in city_lookup:
            return city_lookup[user_input]
        else:
            print("City not found. Please choose from the list above.\n")


def parse_month_input():
    """Ask for a month and return its numeric value 1–12."""
    month_name_to_num = {
        name.lower(): idx for idx, name in enumerate(calendar.month_name) if idx > 0
    }
    month_abbr_to_num = {
        name.lower(): idx for idx, name in enumerate(calendar.month_abbr) if idx > 0
    }

    while True:
        user_input = input("Enter a month (e.g., 'June', 'Jun', or '6'): ").strip()
        # numeric
        if user_input.isdigit():
            m = int(user_input)
            if 1 <= m <= 12:
                return m
            print("Month number must be between 1 and 12.\n")
            continue

        key = user_input.lower()
        if key in month_name_to_num:
            return month_name_to_num[key]
        if key in month_abbr_to_num:
            return month_abbr_to_num[key]

        print("Could not understand that month. Try something like '6', 'June', or 'Jun'.\n")


def load_city_data(base_dir: Path, city: str) -> pd.DataFrame:
    """Load all CSV files for a given city into a single DataFrame."""
    city_dir = base_dir / city
    if not city_dir.exists():
        raise FileNotFoundError(f"City folder '{city_dir}' not found.")

    csv_files = sorted(city_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in '{city_dir}'.")

    dfs = []
    for fpath in csv_files:
        df = pd.read_csv(fpath, parse_dates=["Date"])
        dfs.append(df)

    all_data = pd.concat(dfs, ignore_index=True)

    # Ensure Date and HeatRisk columns are correct types
    all_data["Date"] = pd.to_datetime(all_data["Date"])
    all_data["HeatRisk"] = pd.to_numeric(all_data["HeatRisk"], errors="coerce")

    return all_data


def compute_daily_average_heatrisk(df: pd.DataFrame, month: int) -> pd.Series:
    """Return average HeatRisk per day-of-month across all years for a given month."""
    df_month = df[df["Date"].dt.month == month].copy()
    df_month["day"] = df_month["Date"].dt.day
    daily_avg = df_month.groupby("day")["HeatRisk"].mean()
    return daily_avg


def plot_month_calendar_with_colors(
    year: int,
    month: int,
    daily_avg: pd.Series,
    city: str,
    save_dir: Path,
):
    """Generate and save a single month calendar PNG for the given city/month."""
    cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)
    n_weeks = len(weeks)

    # Risk level matrix
    data = np.full((n_weeks, 7), np.nan)
    day_numbers = np.zeros((n_weeks, 7), dtype=int)

    def categorize_risk(avg):
        if pd.isna(avg):
            return np.nan
        level = int(round(float(avg)))
        return max(0, min(4, level))  # clamp to 0–4

    for i, week in enumerate(weeks):
        for j, day in enumerate(week):
            if day != 0:
                day_numbers[i, j] = day
                avg = daily_avg.get(day, np.nan)
                data[i, j] = categorize_risk(avg)

    # Colormap: 0–4 => green, yellow, orange, red, magenta
    cmap = ListedColormap(["green", "yellow", "orange", "red", "magenta"])
    boundaries = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = BoundaryNorm(boundaries, cmap.N)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(data, cmap=cmap, norm=norm, interpolation="none")

    # Axes: Sunday–Saturday, labels at top
    ax.set_xticks(np.arange(7))
    ax.set_xticklabels(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], fontsize=10)
    ax.xaxis.tick_top()

    ax.set_yticks(np.arange(n_weeks))
    ax.set_yticklabels([""] * n_weeks)

    # Fill full boxes
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(n_weeks - 0.5, -0.5)
    ax.set_aspect("equal", "box")
    ax.grid(False)

    # Day numbers
    for i in range(n_weeks):
        for j in range(7):
            day = day_numbers[i, j]
            if day > 0:
                ax.text(
                    j,
                    i,
                    str(day),
                    ha="center",
                    va="center",
                    fontsize=11,
                    color="black",
                    fontweight="bold",
                )

    month_name = calendar.month_name[month]
    ax.set_title(f"{city} – {month_name} {year} HeatRisk", fontsize=16, pad=30)

    # Legend
    legend_elements = [
        Patch(facecolor="green",   edgecolor="black", label="0 – None"),
        Patch(facecolor="yellow",  edgecolor="black", label="1 – Minor"),
        Patch(facecolor="orange",  edgecolor="black", label="2 – Moderate"),
        Patch(facecolor="red",     edgecolor="black", label="3 – Major"),
        Patch(facecolor="magenta", edgecolor="black", label="4 – Extreme"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper right",
        bbox_to_anchor=(1.15, 1.0),
        title="HeatRisk Levels",
        fontsize=9,
    )

    plt.tight_layout()

    # Save file where the website expects it
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_city = city.lower().replace(" ", "_")
    safe_month = month_name.lower()
    filename = f"{safe_city}_{safe_month}_{year}.png"
    save_path = save_dir / filename
    fig.savefig(save_path, dpi=150)
    plt.close(fig)

    print(f"Saved calendar to: {save_path}")


def main():
    print("--- 2026 HeatRisk Calendar Generator ---\n")
    print(f"Looking for data under: {BASE_DIR}\n")

    cities = get_available_cities(BASE_DIR)
    city = ask_for_city(cities)

    df_city = load_city_data(BASE_DIR, city)

    # Ask if user wants one month or all months
    mode = input("Generate a single month or all 12 months? Enter 'single' or 'all' [single]: ").strip().lower()
    if mode not in {"single", "all"}:
        mode = "single"

    if mode == "single":
        month = parse_month_input()
        daily_avg = compute_daily_average_heatrisk(df_city, month)
        plot_month_calendar_with_colors(YEAR, month, daily_avg, city, IMG_DIR)
    else:
        # All 12 months
        for month in range(1, 13):
            print(f"\nGenerating {calendar.month_name[month]} {YEAR} for {city}...")
            daily_avg = compute_daily_average_heatrisk(df_city, month)
            if daily_avg.empty:
                print("  No data for this month; skipping.")
                continue
            plot_month_calendar_with_colors(YEAR, month, daily_avg, city, IMG_DIR)

    print("\nDone. PNGs are in the 'docs/img' folder.")


if __name__ == "__main__":
    main()
