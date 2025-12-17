# NWS HeatRisk – Station/Year 12‑Month Calendar Viewer

This version is designed for a **single-folder data layout**:
- All HeatRisk CSVs live together in one folder
- A single `station_metadata.csv` provides station labels (name/state/lat/lon)

## Data layout

Place your files like this:

```
data/
  station_metadata.csv
  heatrisk_files/
    HeatRisk-v2.5-USC00010160-2005.csv
    HeatRisk-v2.5-USC00010160-2006.csv
    ...
```

## What it generates

- A 3×4 **12-month grid** PNG for each station/year:
  `docs/img/<STATION_ID>_<YEAR>.png`
- An **Average** PNG per station, shown on a **2026** calendar layout:
  `docs/img/<STATION_ID>_2026.png`
- A manifest for the website:
  `docs/stations.js`

## Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 src/generate_calendars.py
```

Then commit + push (GitHub Pages should serve `/docs`).
