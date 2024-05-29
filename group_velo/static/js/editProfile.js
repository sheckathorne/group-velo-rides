const EMERGENCY_CONTACT_COUNT_LIMIT = 4;

document.getElementById("id_zip_code").addEventListener("input", limit_input);

document.addEventListener("contactDelete", function () {
  labelContactTitles();
  contactCount = countEmergencyContacts();
  if (contactCount < EMERGENCY_CONTACT_COUNT_LIMIT) {
    showFormButton();
  }
});

document.addEventListener("contactDeleteHideFormButton", function () {
  labelContactTitles();
  hideFormButton();
  document
    .getElementById("add-emergency-contact-form")
    .addEventListener("click", showFormButton());
});

document.addEventListener("contactDeleteShowFormButton", function () {
  labelContactTitles();
  contactCount = countEmergencyContacts();
  if (contactCount < EMERGENCY_CONTACT_COUNT_LIMIT) {
    showFormButton();
  }

  if (contactCount >= EMERGENCY_CONTACT_COUNT_LIMIT) {
    hideFormButton();
  }
});

function limit_input() {
  var field = document.getElementById("id_zip_code");
  var max_length = 5;
  if (field.value.length > max_length) {
    field.value = field.value.slice(0, max_length);
  }
}

function showContactModal(e, attributeName) {
  return () => {
    const attributeValue = e.getAttribute(attributeName);
    const modalButton = document.getElementById("contact-delete-submit");
    modalButton.setAttribute(
      "hx-post",
      `/profile/edit/delete_emergency_contact/${attributeValue}/`,
    );
    modalButton.setAttribute(
      "hx-target",
      `#emergency-contact-row-${attributeValue}`,
    );
    htmx.process(modalButton);
  };
}

function labelContactTitles() {
  contactTitles = document.querySelectorAll(".contact-title");
  contactTitles.forEach((title, i) => {
    title.innerText = `Contact #${i + 1}`;
  });
}

function showFormButton() {
  btn = document.getElementById("open-emergency-contact-form");
  btn.style.display = "block";
}

function hideFormButton() {
  btn = document.getElementById("open-emergency-contact-form");
  btn.style.display = "none";
}

function countEmergencyContacts() {
  contacts = document.querySelectorAll(".contact-title");
  if (typeof contacts !== "undefined" && contacts.length > 0) {
    return contacts.length;
  }
  return 0;
}
