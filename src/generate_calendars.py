import calendar
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

# --------- CONFIG ---------
DATA_DIR = Path("data")
METADATA_PATH = DATA_DIR / "station_metadata.csv"
FILES_DIR = DATA_DIR / "heatrisk_files"  # single folder containing all station/year CSVs
OUT_IMG_DIR = Path("docs") / "img"
OUT_MANIFEST = Path("docs") / "stations.js"

AVERAGE_LAYOUT_YEAR = 2026

# Requested legend colors
COLORS = {
    0: "#d9f4cd",  # green
    1: "#ffde59",  # yellow
    2: "#fd933c",  # orange
    3: "#cc0000",  # red
    4: "#8f1eae",  # magenta
}
MISSING_COLOR = "#d9d9d9"

# Filename pattern example: HeatRisk-v2.5-USC00010160-2005.csv
FILENAME_RE = re.compile(r"HeatRisk-v[\d.]+-(?P<station>[A-Z0-9]+)-(?P<year>\d{4})\.csv$")
# --------------------------


def categorize_risk(value: float) -> float:
    if pd.isna(value):
        return np.nan
    lvl = int(round(float(value)))
    return max(0, min(4, lvl))


def load_metadata(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Metadata CSV not found: {path}")
    df = pd.read_csv(path, sep=None, engine="python")
    # Expected columns from your sample: GHCN, NAME, STATE, LATITUDE, LONGITUDE
    # We'll normalize to: station_id, name, state
    cols = {c.upper(): c for c in df.columns}
    if "GHCN" not in cols:
        raise ValueError("Metadata CSV must include a 'GHCN' column (station id).")

    station_col = cols["GHCN"]

    name_col = cols.get("NAME")
    state_col = cols.get("STATE")

    df_out = pd.DataFrame()
    df_out["station_id"] = df[station_col].astype(str)

    if name_col:
        df_out["name"] = df[name_col].astype(str)
    else:
        df_out["name"] = df_out["station_id"]

    if state_col:
        df_out["state"] = df[state_col].astype(str)
    else:
        df_out["state"] = ""

    df_out["display_name"] = df_out.apply(
        lambda r: f"{r['name']}, {r['state']}".strip().strip(","),
        axis=1
    )
    return df_out


def scan_data_files(files_dir: Path):
    if not files_dir.exists():
        raise FileNotFoundError(f"Data folder not found: {files_dir}")

    station_year_files: dict[str, dict[int, Path]] = {}
    for fp in sorted(files_dir.glob("*.csv")):
        m = FILENAME_RE.match(fp.name)
        if not m:
            # skip anything that doesn't match expected naming
            continue
        station = m.group("station")
        year = int(m.group("year"))
        station_year_files.setdefault(station, {})[year] = fp

    if not station_year_files:
        raise RuntimeError(
            f"No HeatRisk CSVs found matching pattern in: {files_dir}\n"
            f"Expected filenames like: HeatRisk-v2.5-USC00010160-2005.csv"
        )
    return station_year_files


def load_station_year_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["Date"])
    if "HeatRisk" not in df.columns:
        raise ValueError(f"Missing 'HeatRisk' column in {path.name}")
    df["HeatRisk"] = pd.to_numeric(df["HeatRisk"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


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


def plot_year_grid(df_all_years: pd.DataFrame, station_id: str, display_name: str, label_year: int, calendar_year: int, average: bool, data_year: int | None):
    colors_list = [COLORS[i] for i in range(5)]
    cmap = ListedColormap(colors_list)
    cmap.set_bad(MISSING_COLOR)
    boundaries = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = BoundaryNorm(boundaries, cmap.N)

    fig, axes = plt.subplots(3, 4, figsize=(16, 10), constrained_layout=False)
    axes = axes.flatten()

    for month in range(1, 13):
        ax = axes[month - 1]
        data_mat, day_numbers = build_month_matrix(df_all_years, month, calendar_year, data_year, average)
        n_weeks = data_mat.shape[0]

        ax.imshow(data_mat, cmap=cmap, norm=norm, interpolation="none")

        # day numbers
        for i in range(n_weeks):
            for j in range(7):
                day = int(day_numbers[i, j])
                if day > 0:
                    ax.text(j, i, str(day), ha="center", va="center", fontsize=8, color="black", fontweight="bold")

        ax.set_xticks(np.arange(7))
        ax.set_xticklabels(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], fontsize=7)
        ax.xaxis.tick_top()

        ax.set_yticks(np.arange(n_weeks))
        ax.set_yticklabels([""] * n_weeks)

        ax.set_xlim(-0.5, 6.5)
        ax.set_ylim(n_weeks - 0.5, -0.5)
        ax.set_aspect("equal", "box")

        ax.set_title(calendar.month_abbr[month], fontsize=10, pad=10)

    if average:
        title = f"{display_name} ({station_id}) — Average HeatRisk (shown on {calendar_year} layout)"
    else:
        title = f"{display_name} ({station_id}) — Year {label_year} HeatRisk"
    fig.suptitle(title, fontsize=16, y=0.96)

    legend_elements = [
        Patch(facecolor=COLORS[0], edgecolor="black", label="0 – None"),
        Patch(facecolor=COLORS[1], edgecolor="black", label="1 – Minor"),
        Patch(facecolor=COLORS[2], edgecolor="black", label="2 – Moderate"),
        Patch(facecolor=COLORS[3], edgecolor="black", label="3 – Major"),
        Patch(facecolor=COLORS[4], edgecolor="black", label="4 – Extreme"),
        Patch(facecolor=MISSING_COLOR, edgecolor="black", label="Missing"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, 0.02))

    plt.subplots_adjust(left=0.04, right=0.98, top=0.90, bottom=0.10, wspace=0.35, hspace=0.7)

    OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_IMG_DIR / f"{station_id}_{label_year}.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


def write_manifest(stations: list[dict], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["window.HEATRISK_STATIONS = ["]
    for s in stations:
        years_str = ", ".join(str(y) for y in s["years"])
        safe_name = s["name"].replace('"', '\"')
        lines.append(f'  {{ id: "{s["id"]}", name: "{safe_name}", years: [{years_str}] }},')
    lines.append("];")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote manifest: {out_path}")


def main():
    print("--- HeatRisk Station/Year 12‑Month Calendar Generator ---\n")
    print(f"Metadata: {METADATA_PATH}")
    print(f"Data files: {FILES_DIR}\n")

    meta = load_metadata(METADATA_PATH)
    station_year_files = scan_data_files(FILES_DIR)

    # Build manifest list (include stations even if metadata missing)
    stations_manifest = []
    for station_id in sorted(station_year_files.keys()):
        row = meta[meta["station_id"] == station_id]
        if not row.empty:
            display_name = row.iloc[0]["display_name"]
        else:
            display_name = station_id
        years = sorted(station_year_files[station_id].keys())
        stations_manifest.append({"id": station_id, "name": display_name, "years": years})

    write_manifest(stations_manifest, OUT_MANIFEST)

    mode = input("Generate calendars for 'one' station or 'all' stations? [all]: ").strip().lower()
    if mode not in {"one", "all"}:
        mode = "all"

    if mode == "one":
        print("\nAvailable stations (first 25):")
        for s in stations_manifest[:25]:
            print(f"  - {s['name']} ({s['id']})")
        station_id = input("\nEnter station id (e.g., USC00010160): ").strip().upper()
        if station_id not in station_year_files:
            raise ValueError("Station id not found in data files.")
        target_ids = [station_id]
    else:
        target_ids = [s["id"] for s in stations_manifest]

    for station_id in target_ids:
        years_map = station_year_files[station_id]
        # Load all years for this station once (concatenate)
        dfs = []
        for y, fp in sorted(years_map.items()):
            df_y = load_station_year_df(fp)
            dfs.append(df_y)
        df_all = pd.concat(dfs, ignore_index=True)

        row = meta[meta["station_id"] == station_id]
        display_name = row.iloc[0]["display_name"] if not row.empty else station_id

        # Year-specific calendars
        for y in sorted(years_map.keys()):
            plot_year_grid(df_all, station_id, display_name, label_year=y, calendar_year=y, average=False, data_year=y)

        # Average calendar (all years) shown on 2026 layout
        plot_year_grid(df_all, station_id, display_name, label_year=AVERAGE_LAYOUT_YEAR, calendar_year=AVERAGE_LAYOUT_YEAR, average=True, data_year=None)

    print("\nDone. Images are in docs/img and station list is docs/stations.js")


if __name__ == "__main__":
    main()
