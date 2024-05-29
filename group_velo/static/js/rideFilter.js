import { showHideSaveFilterButton, getFormElements, clearForm } from "./main";

document.addEventListener("DOMContentLoaded", () => {
  const clubDropdown = document.querySelector("#rides_create_club select");
  clubDropdown.addEventListener("change", () => {
    showHideSaveFilterButton();
  });

  const group_classification_inputs = document.querySelectorAll(
    ".group_classifcation_multi_checkbox input",
  );
  group_classification_inputs.forEach((input) => {
    input.addEventListener("change", () => {
      showHideSaveFilterButton();
    });
  });

  const distance_textboxes = document.querySelectorAll(".distance_textbox");
  distance_textboxes.forEach((textBox) => {
    textBox.addEventListener("keyup", (_e) => {
      showHideSaveFilterButton();
    });
  });

  const clearButton = document.getElementById("clear-filter-button");
  clearButton.addEventListener("click", () => {
    showHideSaveFilterButton();
  });

  const saveFilterButton = document.getElementById("save-filter-button");
  saveFilterButton.addEventListener("click", () => {
    const new_form = document.getElementById("save-filter-modal-form");
    clearForm(new_form);
    const formElements = getFormElements("ride-filter-form");

    for (let item of formElements) {
      let new_item = item.cloneNode(true);
      const is_checked_checkbox =
        new_item.type === "checkbox" && new_item.checked;
      const is_text_field =
        new_item.type !== "checkbox" &&
        new_item.tagName === "INPUT" &&
        new_item.value;
      const is_selected_dropdown = new_item.tagName === "SELECT" && item.value;

      if (is_checked_checkbox || is_text_field) {
        new_item.type = "hidden";
        new_item.id = new_item.id + "-modal";
        if (is_checked_checkbox) {
          new_item.checked = true;
        }
        new_form.appendChild(new_item);
      } else if (is_selected_dropdown) {
        let input = document.createElement("input");
        input.type = "hidden";
        input.value = item.value;
        input.id = new_item.id + "-modal";
        input.name = item.name;
        new_form.appendChild(input);
      }
    }
  });
});
