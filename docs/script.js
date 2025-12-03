const citySelect = document.getElementById("citySelect");
const yearSelect = document.getElementById("yearSelect");
const calendarImage = document.getElementById("calendarImage");
const calendarCaption = document.getElementById("calendarCaption");
const missingMessage = document.getElementById("missingMessage");

function updateCalendar(){
  const city = citySelect.value;
  const year = yearSelect.value;
  if(!city || !year){
    calendarImage.src = "";
    missingMessage.classList.remove("hidden");
    return;
  }
  const path = `img/${city}_${year}.png`;
  calendarImage.src = path;
  calendarCaption.textContent = `${city} – ${year}`;
  missingMessage.classList.add("hidden");
}

window.addEventListener("DOMContentLoaded", ()=>{
  // cities.js should define window.HEATRISK_CITIES
  const CITIES = window.HEATRISK_CITIES || [];
  CITIES.forEach(c=>{
    const opt=document.createElement("option");
    opt.value=c.slug;
    opt.textContent=c.name;
    citySelect.appendChild(opt);
  });
  citySelect.addEventListener("change", updateCalendar);
  yearSelect.addEventListener("change", updateCalendar);
});
