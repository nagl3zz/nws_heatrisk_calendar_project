const citySelect = document.getElementById("citySelect");
const yearSelect = document.getElementById("yearSelect");
const calendarImage = document.getElementById("calendarImage");
const calendarCaption = document.getElementById("calendarCaption");
const missingMessage = document.getElementById("missingMessage");

const CITIES = window.HEATRISK_CITIES || [];

function buildImagePath(citySlug, yearValue) {
  // For "avg", we use 2026 as the label year in the filename
  const labelYear = yearValue === "avg" ? "2026" : yearValue;
  return `img/${citySlug}_${labelYear}.png`;
}

function populateCities() {
  citySelect.innerHTML = "";

  if (!CITIES.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No cities available";
    citySelect.appendChild(opt);
    citySelect.disabled = true;
    yearSelect.disabled = true;
    return;
  }

  const sorted = CITIES.slice().sort((a, b) => a.name.localeCompare(b.name));

  sorted.forEach((city, index) => {
    const opt = document.createElement("option");
    opt.value = city.slug;
    opt.textContent = city.name;
    if (index === 0) opt.selected = true;
    citySelect.appendChild(opt);
  });

  citySelect.disabled = false;
}

function getCityBySlug(slug) {
  return CITIES.find((c) => c.slug === slug) || null;
}

function populateYears() {
  yearSelect.innerHTML = "";
  const citySlug = citySelect.value;
  const city = getCityBySlug(citySlug);

  if (!city) {
    yearSelect.disabled = true;
    return;
  }

  // Add data years
  const years = (city.years || []).slice().sort((a, b) => a - b);
  years.forEach((y) => {
    const opt = document.createElement("option");
    opt.value = String(y);
    opt.textContent = String(y);
    yearSelect.appendChild(opt);
  });

  // Add Average option
  const avgOpt = document.createElement("option");
  avgOpt.value = "avg";
  avgOpt.textContent = "Average";
  yearSelect.appendChild(avgOpt);

  yearSelect.disabled = false;
  yearSelect.value = "avg"; // default to Average
}

function updateCalendar() {
  const citySlug = citySelect.value;
  const yearValue = yearSelect.value;

  if (!citySlug || !yearValue) {
    calendarImage.src = "";
    calendarCaption.textContent = "No city/year selected.";
    missingMessage.classList.add("hidden");
    return;
  }

  const imgPath = buildImagePath(citySlug, yearValue);
  calendarImage.src = imgPath;

  const prettyCity = citySlug
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  let captionLabel;
  if (yearValue === "avg") {
    captionLabel = "Average HeatRisk (shown on 2026 calendar layout)";
  } else {
    captionLabel = `Year ${yearValue}`;
  }

  calendarCaption.textContent = `${prettyCity} – ${captionLabel}`;
  missingMessage.classList.add("hidden");
}

// If the image fails to load, show the warning message
calendarImage.addEventListener("error", () => {
  missingMessage.classList.remove("hidden");
});

citySelect.addEventListener("change", () => {
  populateYears();
  updateCalendar();
});

yearSelect.addEventListener("change", updateCalendar);

window.addEventListener("DOMContentLoaded", () => {
  populateCities();
  populateYears();
  updateCalendar();
});
