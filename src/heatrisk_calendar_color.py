import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# ---------- CONFIG ----------
AVERAGE_YEAR_LABEL = 2026                # The calendar layout year used for the Average view
BASE_DIR = Path("data") / "NWS Data"     # where the NWS Data folder lives
IMG_DIR = Path("docs") / "img"           # where PNGs for the website go
CITIES_JS_PATH = Path("docs") / "cities.js"
# -----------------------------


def slugify_city(name: str) -> str:
  return name.strip().lower().replace(" ", "_")


def write_cities_js(cities, years_by_city, output_path: Path = CITIES_JS_PATH):
  output_path.parent.mkdir(parents=True, exist_ok=True)
  lines = ["window.HEATRISK_CITIES = ["]
  for city in sorted(cities):
    slug = slugify_city(city)
    years = sorted(years_by_city.get(city, []))
    years_str = ", ".join(str(y) for y in years)
    lines.append(f'  {{ slug: "{slug}", name: "{city}", years: [{years_str}] }},')
  lines.append("];")
  output_path.write_text("\n".join(lines), encoding="utf-8")
  print(f"Wrote city list (with years) to {output_path}")


def get_available_cities(base_dir: Path):
  if not base_dir.exists():
    raise FileNotFoundError(f"Base directory '{base_dir}' not found.")
  cities = [p.name for p in base_dir.iterdir() if p.is_dir()]
  if not cities:
    raise RuntimeError(f"No city folders found under '{base_dir}'.")
  return sorted(cities)


def load_city_data(base_dir: Path, city: str) -> pd.DataFrame:
  city_dir = base_dir / city
  if not city_dir.exists():
    raise FileNotFoundError(f"City folder '{city_dir}' not found.")
  csv_files = sorted(city_dir.glob("*.csv"))
  if not csv_files:
    raise FileNotFoundError(f"No CSV files found in '{city_dir}'.")
  dfs = [pd.read_csv(f, parse_dates=["Date"]) for f in csv_files]
  all_data = pd.concat(dfs, ignore_index=True)
  all_data["Date"] = pd.to_datetime(all_data["Date"])
  all_data["HeatRisk"] = pd.to_numeric(all_data["HeatRisk"], errors="coerce")
  return all_data


def get_years_for_city(df: pd.DataFrame):
  years = sorted(df["Date"].dt.year.dropna().unique())
  return [int(y) for y in years]


def categorize_risk(avg):
  if pd.isna(avg):
    return np.nan
  level = int(round(float(avg)))
  return max(0, min(4, level))


def build_month_matrix(df: pd.DataFrame, month: int, calendar_year: int, data_year: int | None, average: bool):
  cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
  weeks = cal.monthdayscalendar(calendar_year, month)
  n_weeks = len(weeks)

  data_mat = np.full((n_weeks, 7), np.nan)
  day_numbers = np.zeros((n_weeks, 7), dtype=int)

  if average:
    df_month = df[df["Date"].dt.month == month].copy()
  else:
    df_month = df[(df["Date"].dt.year == data_year) & (df["Date"].dt.month == month)].copy()

  if not df_month.empty:
    df_month["day"] = df_month["Date"].dt.day
    daily_avg = df_month.groupby("day")["HeatRisk"].mean()
  else:
    daily_avg = pd.Series(dtype=float)

  for i, week in enumerate(weeks):
    for j, day in enumerate(week):
      if day != 0:
        day_numbers[i, j] = day
        avg = daily_avg.get(day, np.nan)
        data_mat[i, j] = categorize_risk(avg)

  return data_mat, day_numbers


def plot_year_grid_for_city(df_city: pd.DataFrame, city: str, label_year: int, calendar_year: int, average: bool, data_year: int | None):
    # Color map using requested hex colors
    colors = ["#d9f4cd", "#ffde59", "#fd933c", "#cc0000", "#8f1eae"]
    cmap = ListedColormap(colors)
    cmap.set_bad("#d9d9d9")  # missing data
    boundaries = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = BoundaryNorm(boundaries, cmap.N)

    # 3 rows x 4 columns, with extra spacing between rows/columns
    fig, axes = plt.subplots(3, 4, figsize=(16, 10), constrained_layout=False)
    axes = axes.flatten()

    for month in range(1, 13):
        ax = axes[month - 1]
        data_mat, day_numbers = build_month_matrix(
            df_city,
            month=month,
            calendar_year=calendar_year,
            data_year=data_year,
            average=average,
        )

        n_weeks = data_mat.shape[0]
        ax.imshow(data_mat, cmap=cmap, norm=norm, interpolation="none")

        # Day numbers
        for i in range(n_weeks):
            for j in range(7):
                day = int(day_numbers[i, j])
                if day > 0:
                    ax.text(
                        j,
                        i,
                        str(day),
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="black",
                        fontweight="bold",
                    )

        # Axis formatting
        ax.set_xticks(np.arange(7))
        ax.set_xticklabels(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], fontsize=7)
        ax.xaxis.tick_top()

        ax.set_yticks(np.arange(n_weeks))
        ax.set_yticklabels([""] * n_weeks)

        ax.set_xlim(-0.5, 6.5)
        ax.set_ylim(n_weeks - 0.5, -0.5)
        ax.set_aspect("equal", "box")
        ax.grid(False)

        # Month title with extra padding so it doesn't collide
        month_name = calendar.month_abbr[month]
        ax.set_title(month_name, fontsize=10, pad=10)

    # Overall title
    if average:
        title_label = f"{city} – Average HeatRisk (shown on {calendar_year} calendar layout)"
    else:
        title_label = f"{city} – Year {label_year} HeatRisk"

    fig.suptitle(title_label, fontsize=16, y=0.96)

    # Legend (single for whole figure)
    legend_elements = [
        Patch(facecolor="#d9f4cd", edgecolor="black", label="0 – None"),
        Patch(facecolor="#ffde59", edgecolor="black", label="1 – Minor"),
        Patch(facecolor="#fd933c", edgecolor="black", label="2 – Moderate"),
        Patch(facecolor="#cc0000", edgecolor="black", label="3 – Major"),
        Patch(facecolor="#8f1eae", edgecolor="black", label="4 – Extreme"),
        Patch(facecolor="#d9d9d9", edgecolor="black", label="Missing data"),
    ]
    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=3,
        fontsize=9,
        bbox_to_anchor=(0.5, 0.02),
    )

    # Add generous spacing between rows/columns so month titles don't overlap
    plt.subplots_adjust(
        left=0.04,
        right=0.98,
        top=0.90,
        bottom=0.10,
        wspace=0.35,   # space between columns
        hspace=0.7     # space between rows
    )

    # Save file
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    safe_city = slugify_city(city)
    filename = f"{safe_city}_{label_year}.png"
    save_path = IMG_DIR / filename
    fig.savefig(save_path, dpi=150)
    plt.close(fig)

    print(f"Saved calendar grid to: {save_path}")



def main():
  print("--- HeatRisk 12‑Month Calendar Generator ---\n")
  print(f"Looking for data under: {BASE_DIR}\n")

  cities = get_available_cities(BASE_DIR)
  dfs_by_city = {}
  years_by_city = {}
  for city in cities:
    print(f"Loading data for city: {city}")
    df_city = load_city_data(BASE_DIR, city)
    dfs_by_city[city] = df_city
    years_by_city[city] = get_years_for_city(df_city)

  write_cities_js(cities, years_by_city, CITIES_JS_PATH)

  mode = input("Generate 12‑month grids for one city or all cities? Enter 'one' or 'all' [all]: ").strip().lower()
  if mode not in {"one", "all"}:
    mode = "all"

  if mode == "one":
    print("\nAvailable cities:")
    for c in cities:
      print(f"  - {c}")
    print()
    city_lookup = {c.lower(): c for c in cities}
    while True:
      user_input = input("Enter city name (not case-sensitive, choose from above): ").strip().lower()
      if user_input in city_lookup:
        city = city_lookup[user_input]
        break
      print("City not found. Please choose from the list above.\n")

    df_city = dfs_by_city[city]
    years = years_by_city[city]
    print(f"Generating 12‑month grids for city '{city}' for all data years and the Average view...")
    for y in years:
      print(f"  -> Year {y}")
      plot_year_grid_for_city(df_city, city, label_year=y, calendar_year=y, average=False, data_year=y)
    print(f"  -> Average (all years, shown on {AVERAGE_YEAR_LABEL} calendar layout)")
    plot_year_grid_for_city(df_city, city, label_year=AVERAGE_YEAR_LABEL, calendar_year=AVERAGE_YEAR_LABEL, average=True, data_year=None)

  else:
    for city in cities:
      print(f"\n=== Generating for city: {city} ===")
      df_city = dfs_by_city[city]
      years = years_by_city[city]
      for y in years:
        print(f"  -> Year {y}")
        plot_year_grid_for_city(df_city, city, label_year=y, calendar_year=y, average=False, data_year=y)
      print(f"  -> Average (all years, shown on {AVERAGE_YEAR_LABEL} calendar layout)")
      plot_year_grid_for_city(df_city, city, label_year=AVERAGE_YEAR_LABEL, calendar_year=AVERAGE_YEAR_LABEL, average=True, data_year=None)

  print("\nDone. PNGs are in 'docs/img', and 'docs/cities.js' lists all cities and years.")


if __name__ == "__main__":
  main()
