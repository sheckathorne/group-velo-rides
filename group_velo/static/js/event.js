import Sqids from "sqids";

const VISIBILITY = {
  HIDE: "hide",
  SHOW: "show",
};

export function setPrivacyListener(el, conditionalFields) {
  el.addEventListener("change", (e) => {
    const select = e.target;
    togglePrivacyDisplay(select, conditionalFields);
  });
}

export function getUrlVars() {
  var vars = {},
    hash;
  var hashes = window.location.href
    .slice(window.location.href.indexOf("?") + 1)
    .split("&");
  for (var i = 0; i < hashes.length; i++) {
    hash = hashes[i].split("=");
    vars[hash[0]] = hash[1];
  }
  return vars;
}

function toggleElementDisplay(id, action) {
  const element = getElementById(id);
  element.style.display = action === VISIBILITY.HIDE ? "none" : "block";
}

export function toggleElementArrayDisplay(arr, action) {
  arr.forEach((item) => {
    toggleElementDisplay(item.id, action);
  });
}

export function toggleElementArrayItemDisplay(arr, fieldName, action) {
  const id = arr.find((item) => item.name === fieldName).id;
  toggleElementDisplay(id, action);
}

export function swapRouteButtonWithInput(name, url, buttonId, newId) {
  const defaultButton = getElementById("routeChoiceButton");
  defaultButton.textContent = "Change Route";

  const button = getElementById(buttonId);
  const parentDiv = button.parentNode;
  const existingInput = getElementById(newId);
  if (existingInput) {
    existingInput.remove();
  }

  const newElement = document.createElement("a");
  newElement.id = newId;
  newElement.href = url;
  newElement.target = "_blank";
  newElement.textContent = name;

  const classStr =
    "w-full underline text-blue-600 hover:text-blue-800 dark:hover:text-blue-500 visited:text-purple-600 dark:visited:text-purple-400 textinput border-gray-300 appearance-none dark:bg-gray-700 rounded focus:outline-none bg-white dark:border-gray-500 dark:text-blue-300 leading-normal shadow block border py-2 px-4 w-full mb-2";
  const classArr = classStr.split(" ");
  newElement.classList.add(...classArr);

  parentDiv.insertBefore(newElement, button);
}

export function routeSelectClick(_e, url, id, name) {
  // save the value of the selected route to the hidden input
  const targetInput = document.getElementById("route_id");
  const sqids = new Sqids({
    alphabet: "GY2rgEpWaCj6tNT1ioIPXLxzF8uHn704A9hDbekqfOsBSwRKVUMQmvd3lyJc5Z",
    minLength: 16,
  });

  const route_id = sqids.decode(id)[0];

  targetInput.value = route_id;

  // change the select button to a disabled text field with the contents of the selected route
  swapRouteButtonWithInput(
    name,
    url,
    "routeChoiceButton",
    "selected_route_text",
  );
}

export function togglePrivacyDisplay(select, conditionalFields) {
  if (select.value === "5") {
    toggleElementArrayItemDisplay(conditionalFields, "club", VISIBILITY.SHOW);
  } else {
    toggleElementArrayItemDisplay(conditionalFields, "club", VISIBILITY.HIDE);
  }
}

export function setFrequencyListener(el, conditionalFields) {
  el.addEventListener("change", (e) => {
    const select = e.target;
    hideShowFrequency(select, conditionalFields);
  });
}

export function hideShowFrequency(select, conditionalFields) {
  if (["7", "14"].includes(select.value)) {
    toggleElementArrayItemDisplay(
      conditionalFields,
      "weekdays",
      VISIBILITY.SHOW,
    );
  } else {
    toggleElementArrayItemDisplay(
      conditionalFields,
      "weekdays",
      VISIBILITY.HIDE,
    );
  }
}

export function extractSlugFromQuerystring(query) {
  return query && query.club ? query.club : "";
}

export function extractRideDateFromQuerystring(query) {
  const year = query && query.year ? parseInt(query.year) : 0;
  const month = query && query.month ? parseInt(query.month) : 0;
  const day = query && query.day ? parseInt(query.day) : 0;

  return year > 0 && month > 0 && month < 13 && day > 0 && day < 32
    ? `${year.toString()}-${addZeroToDate(month)}-${addZeroToDate(day)}`
    : null;
}

function addZeroToDate(val) {
  return val < 10 ? "0" + val.toString() : val.toString();
}

export function preFillClub(club_sqid, conditionalFields) {
  const sqids = new Sqids({
    alphabet: "GY2rgEpWaCj6tNT1ioIPXLxzF8uHn704A9hDbekqfOsBSwRKVUMQmvd3lyJc5Z",
    minLength: 16,
  });

  const privacySelect = getElementById("event_create_privacy").querySelector(
    "select",
  );
  privacySelect.value = "5";

  const clubSelect = getElementById("div_id_club").querySelector("select");
  const club_id = sqids.decode(club_sqid)[0];

  clubSelect.value = club_id;

  toggleElementArrayItemDisplay(conditionalFields, "club", VISIBILITY.SHOW);
}

export function preFillRideDates(rideDate) {
  const frequencySelect = getElementById(
    "event_create_frequency",
  ).querySelector("select");

  const startDate = document.getElementById("event_create_start_date");
  const endDate = document.getElementById("event_create_end_date");

  frequencySelect.value = "0";
  startDate.value = rideDate;
  endDate.value = rideDate;
}

function getClubIdFromSlug(slug) {
  return slug.slice(slug.lastIndexOf("-") + 1);
}

export function clearFilter() {
  const url = window.location.href.split("?")[0];
  window.location.href = url;
}

export function resizeRideMapFrames() {
  frames = document.querySelectorAll("iframe");
  if (frames) {
    let newWidth = 1;
    frames.forEach((frame, i) => {
      if (i == 0) {
        newWidth = frame.parentElement.offsetWidth;
        newWidth =
          newWidth === 0 ? Math.max(newWidth, window.innerWidth) : newWidth;
      }

      if (frame.src.includes("strava")) {
        frame.style.width = newWidth.toString() + "px";
        frame.style.height = "400px";
      }

      if (frame.src.includes("ridewithgps")) {
        frame.style["max-width"] = newWidth.toString() + "px";
        frame.style.height = "400px";
      }
    });
  }
}

function getElementById(id) {
  return document.getElementById(id);
}

function setAttributes(element, attributes) {
  for (const key in attributes) {
    if (attributes.hasOwnProperty(key)) {
      element.setAttribute(key, attributes[key]);
    }
  }
}

function validateAndSetField(field, rules, failingValue) {
  const r = JSON.parse(rules);
  const fieldIsBlank = field.value == "";
  const fieldFailsValidation = !Iodine.assert(field.value, r).valid;
  if (fieldIsBlank || fieldFailsValidation) {
    field.value = failingValue;
  } else {
    return;
  }
}

function setPaceRangeAttributes(lowerElement, upperElement, response) {
  if (response.lower_pace_range !== "0" && response.upper_pace_range !== "0") {
    const lowerRules = `["numeric", "min:${response.lower_pace_range}", "max:${
      response.upper_pace_range - 0.1
    }"]`;
    const upperRules = `["numeric", "min:${
      response.lower_pace_range - -0.1
    }", "max:${response.upper_pace_range}"]`;

    setAttributes(lowerElement, {
      "data-rules": lowerRules,
      "strict-rules": response.strict_ride_classification,
    });
    validateAndSetField(lowerElement, lowerRules, response.lower_pace_range);

    setAttributes(upperElement, {
      "data-rules": upperRules,
      "strict-rules": response.strict_ride_classification,
    });
    validateAndSetField(upperElement, upperRules, response.upper_pace_range);
  } else {
    setAttributes(lowerElement, {
      "data-rules": "[]",
      "strict-rules": false,
    });
    setAttributes(upperElement, {
      "data-rules": "[]",
      "strict-rules": false,
    });
  }
}

function listenAfterHtmx() {
  document.addEventListener("htmx:afterRequest", function (event) {
    const lowerPaceRangeElement = getElementById(
      "event_create_lower_pace_range",
    );
    const upperPaceRangeElement = getElementById(
      "event_create_upper_pace_range",
    );

    if (
      event.detail.successful &&
      event.detail.xhr.responseURL.includes("ride_classification_limits")
    ) {
      const response = JSON.parse(event.detail.xhr.response);
      setPaceRangeAttributes(
        lowerPaceRangeElement,
        upperPaceRangeElement,
        response,
      );
    }
  });
}

export function handleSelectChange() {
  const clubSelectElement =
    getElementById("event_create_club").querySelector("select");
  const surfaceSelectElement = getElementById(
    "event_occurence_create_surface_type",
  ).querySelector("select");
  const classificationSelectElement = getElementById(
    "event_create_group_classification",
  ).querySelector("select");
  const lowerPaceRangeElement = getElementById("event_create_lower_pace_range");
  const upperPaceRangeElement = getElementById("event_create_upper_pace_range");
  const dataContainer = getElementById("group-classification-data");

  const clubId = clubSelectElement.value;
  const surfaceType = surfaceSelectElement.value;
  const groupClassification = classificationSelectElement.value;

  if (clubId && surfaceType && groupClassification) {
    setAttributes(dataContainer, {
      "hx-vals": `{"club_id": ${clubId}, "surface_type": "${surfaceType}", "group_classification": "${groupClassification}"}`,
    });
    dataContainer.dispatchEvent(new Event("getClassification"));
  }

  lowerPaceRangeElement.dispatchEvent(new Event("input"));
  upperPaceRangeElement.dispatchEvent(new Event("input"));
}

export function getClassificationData() {
  const clubSelectElement =
    getElementById("event_create_club").querySelector("select");
  const surfaceSelectElement = getElementById(
    "event_occurence_create_surface_type",
  ).querySelector("select");
  const classificationSelectElement = getElementById(
    "event_create_group_classification",
  ).querySelector("select");

  clubSelectElement.addEventListener("change", handleSelectChange);
  surfaceSelectElement.addEventListener("change", handleSelectChange);
  classificationSelectElement.addEventListener("change", handleSelectChange);

  listenAfterHtmx();
}

export function validateFormFields() {
  const lowerPaceRangeElement = getElementById("event_create_lower_pace_range");
  const upperPaceRangeElement = getElementById("event_create_upper_pace_range");

  lowerPaceRangeElement.dispatchEvent(new Event("input"));
  upperPaceRangeElement.dispatchEvent(new Event("input"));
}

export function setRules() {
  const startDateElement = getElementById("event_create_start_date");
  const endDateElement = getElementById("event_create_end_date");

  startDateElement.addEventListener("change", () => {
    endDateElement.setAttribute(
      "data-rules",
      `["oneYearFrom:${startDateElement.valueAsNumber}", "endAfterStart:${startDateElement.valueAsNumber}"]`,
    );
  });

  endDateElement.addEventListener("change", () => {
    startDateElement.setAttribute(
      "data-rules",
      `["startBeforeEnd:${endDateElement.valueAsNumber}"]`,
    );
  });
}

export function createRules() {
  Iodine.rule("oneYearFrom", function (value, startDate) {
    if (!isNaN(startDate)) {
      const dayDiff = Math.floor(
        (Date.parse(value) - startDate) / (1000 * 60 * 60 * 24),
      );
      return dayDiff <= 366;
    }
    return true;
  });
  Iodine.setErrorMessage(
    "oneYearFrom",
    "End date cannot be more than one year from start date",
  );

  Iodine.rule("startBeforeEnd", function (value, endDate) {
    if (!isNaN(endDate)) {
      return Date.parse(value) <= endDate;
    }
    return true;
  });
  Iodine.setErrorMessage(
    "startBeforeEnd",
    "Start date should be less than or equal to end date",
  );

  Iodine.rule("endAfterStart", function (value, startDate) {
    if (!isNaN(startDate)) {
      return Date.parse(value) >= startDate;
    }
    return true;
  });
  Iodine.setErrorMessage(
    "endAfterStart",
    "End date should be greater than or equal to start date",
  );
}
