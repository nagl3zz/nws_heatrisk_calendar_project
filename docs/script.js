const stationSelect = document.getElementById("stationSelect");
const yearSelect = document.getElementById("yearSelect");
const calendarImage = document.getElementById("calendarImage");
const calendarCaption = document.getElementById("calendarCaption");
const missingMessage = document.getElementById("missingMessage");

const STATIONS = window.HEATRISK_STATIONS || [];

function buildImagePath(stationId, yearValue) {
  const labelYear = yearValue === "avg" ? "2026" : yearValue;
  return `img/${stationId}_${labelYear}.png`;
}

function populateStations() {
  stationSelect.innerHTML = "";

  if (!STATIONS.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No stations found (run generator)";
    stationSelect.appendChild(opt);
    stationSelect.disabled = true;
    yearSelect.disabled = true;
    return;
  }

  const sorted = STATIONS.slice().sort((a, b) => a.name.localeCompare(b.name));

  sorted.forEach((s, idx) => {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = `${s.name} (${s.id})`;
    if (idx === 0) opt.selected = true;
    stationSelect.appendChild(opt);
  });

  stationSelect.disabled = false;
}

function getStationById(id) {
  return STATIONS.find((s) => s.id === id) || null;
}

function populateYears() {
  yearSelect.innerHTML = "";
  const stationId = stationSelect.value;
  const station = getStationById(stationId);

  if (!station) {
    yearSelect.disabled = true;
    return;
  }

  const years = (station.years || []).slice().sort((a, b) => a - b);
  years.forEach((y) => {
    const opt = document.createElement("option");
    opt.value = String(y);
    opt.textContent = String(y);
    yearSelect.appendChild(opt);
  });

  const avgOpt = document.createElement("option");
  avgOpt.value = "avg";
  avgOpt.textContent = "Average (shown on 2026 layout)";
  yearSelect.appendChild(avgOpt);

  yearSelect.value = "avg";
  yearSelect.disabled = false;
}

function updateCalendar() {
  const stationId = stationSelect.value;
  const yearValue = yearSelect.value;

  if (!stationId || !yearValue) {
    calendarImage.src = "";
    calendarCaption.textContent = "";
    missingMessage.classList.add("hidden");
    return;
  }

  const station = getStationById(stationId);
  const imgPath = buildImagePath(stationId, yearValue);
  calendarImage.src = imgPath;

  const label = yearValue === "avg" ? "Average (2026 layout)" : `Year ${yearValue}`;
  calendarCaption.textContent = station ? `${station.name} (${station.id}) — ${label}` : `${stationId} — ${label}`;

  missingMessage.classList.add("hidden");
}

calendarImage.addEventListener("error", () => {
  missingMessage.classList.remove("hidden");
});

stationSelect.addEventListener("change", () => {
  populateYears();
  updateCalendar();
});

yearSelect.addEventListener("change", updateCalendar);

window.addEventListener("DOMContentLoaded", () => {
  populateStations();
  populateYears();
  updateCalendar();
});
