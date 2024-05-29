const conditional_fields = document.getElementById("div_id_club");
conditional_fields.style.display = "none";

document.addEventListener("DOMContentLoaded", () => {
  const checkbox = document.getElementById("id_shared");
  if (checkbox.checked) {
    conditional_fields.style.display = "block";
  } else {
    conditional_fields.style.display = "none";
  }
});

document.getElementById("id_shared").addEventListener("change", (e) => {
  if (e.target.checked) {
    conditional_fields.style.display = "block";
  } else {
    conditional_fields.style.display = "none";
  }
});
