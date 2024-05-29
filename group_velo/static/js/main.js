function removeCaret(th) {
  th.innerHTML = th.getAttribute("data-original-text");
}

function removeAllCarets(thead) {
  const newTheadList = [...thead];
  newTheadList.shift();
  newTheadList.forEach((th) => {
    removeCaret(th);
  });
}

export function addCaret(direction, th, allTh) {
  removeAllCarets(allTh);

  let caret = "";
  if (direction === "up") {
    caret = ' <i class="fa-solid fa-caret-up"></i>';
  } else if (direction === "down") {
    caret = ' <i class="fa-solid fa-caret-down"></i>';
  }

  th.innerHTML += caret;
}

export function setAlertTimeout() {
  setTimeout(() => {
    document.querySelectorAll(".message-alert").forEach((alert) => {
      let timeout_value = parseInt(alert.getAttribute("data-timeout"));
      if (timeout_value) {
        setTimeout(() => {
          alert.style.display = "none";
        }, timeout_value);
      }
    });
  }, 1000);
}

export function showHideSaveFilterButton() {
  const button = document.getElementById("save-filter-button");
  if (formIsValidAndHasMinimumOneValue("ride-filter-form")) {
    button.style.display = "block";
  } else {
    button.style.display = "none";
  }
}

function formIsValidAndHasMinimumOneValue(formId) {
  let hasInvalidValue = false;
  let hasOneValidValue = false;
  const formElements = getFormElements(formId);

  for (let el of formElements) {
    if (!hasInvalidValue && elementIsInvalid(el)) {
      hasInvalidValue = true;
    }

    if (!hasOneValidValue && elementHasAValue(el)) {
      hasOneValidValue = true;
    }
  }

  return !hasInvalidValue && hasOneValidValue;
}

export function getFormElements(formId) {
  const form = document.getElementById(formId);
  const els = form.elements;
  return els;
}

function elementIsInvalid(el) {
  if (
    el.tagName === "INPUT" &&
    el.type !== "checkbox" &&
    el.value &&
    !isNumeric(el.value)
  ) {
    return true;
  }
  return false;
}

function elementHasAValue(el) {
  const checkedBox = el.type === "checkbox" && el.checked;
  const selectedValue = el.tagName === "SELECT" && el.value;
  const nonBlankText =
    el.type !== "checkbox" && el.tagName === "INPUT" && el.value;
  return checkedBox || selectedValue || nonBlankText;
}

function isNumeric(str) {
  if (typeof str != "string") return false;
  return !isNaN(str) && !isNaN(parseFloat(str));
}

export function notificationSelectAll() {
  const allBox = document.getElementById("checkbox-all");
  const allChecks = document.querySelectorAll(".notification-check");

  allChecks.forEach((box) => {
    box.checked = allBox.checked;
  });
}

export function getNotificationChecks() {
  const allChecks = document.querySelectorAll(".notification-check");
  let checked_ids = [];

  allChecks.forEach((check) => {
    if (check.checked) {
      const id = check.getAttribute("data-notification-id");
      checked_ids.push(id);
    }
  });

  return checked_ids;
}

export function alterRequestPath(detail, checked_ids, path) {
  const window_url = window.location.href;
  const hashes = window_url.split("?")[1];
  let url = `/notifications/${path}/`;
  url += hashes ? checked_ids + "/?" + hashes : checked_ids + "/";
  detail.path = url;
}

export function handleMarking(detail, checked_ids) {
  if (detail.elt.id === "mark-read-btn") {
    alterRequestPath(detail, checked_ids, "read_many");
  } else if (detail.elt.id === "mark-unread-btn") {
    alterRequestPath(detail, checked_ids, "unread_many");
  }
}

export function clearForm(form) {
  let idsToRemove = [];
  for (let item of form.elements) {
    if (item.name !== "csrfmiddlewaretoken" && item.type !== "text") {
      idsToRemove.push(item.id);
    }
  }

  idsToRemove.forEach((id) => {
    if (id) {
      document.querySelectorAll("#" + id).forEach((el) => {
        el.remove();
      });
    }
  });
}
