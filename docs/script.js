const citySelect = document.getElementById("citySelect");
const monthSelect = document.getElementById("monthSelect");
const yearInput = document.getElementById("yearInput");
const calendarImage = document.getElementById("calendarImage");
const calendarCaption = document.getElementById("calendarCaption");
const missingMessage = document.getElementById("missingMessage");

function buildImagePath(citySlug, monthSlug, year) {
  return `img/${citySlug}_${monthSlug}_${year}.png`;
}

function updateCalendar() {
  const citySlug = citySelect.value;
  const monthSlug = monthSelect.value;
  const year = yearInput.value || "2026";

  const imgPath = buildImagePath(citySlug, monthSlug, year);

  calendarImage.src = imgPath;
  calendarImage.alt = `${citySlug} ${monthSlug} ${year} HeatRisk calendar`;

  const prettyCity = citySlug
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
  const prettyMonth = monthSlug.charAt(0).toUpperCase() + monthSlug.slice(1);

  calendarCaption.textContent = `${prettyCity} – ${prettyMonth} ${year} HeatRisk Calendar`;

  missingMessage.classList.add("hidden");
}

calendarImage.addEventListener("error", () => {
  missingMessage.classList.remove("hidden");
});

citySelect.addEventListener("change", updateCalendar);
monthSelect.addEventListener("change", updateCalendar);

window.addEventListener("DOMContentLoaded", () => {
  updateCalendar();
});
