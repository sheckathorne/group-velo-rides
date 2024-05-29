import {
  toggleElementArrayDisplay,
  togglePrivacyDisplay,
  setFrequencyListener,
  getUrlVars,
  extractRideDateFromQuerystring,
  setPrivacyListener,
  preFillClub,
  preFillRideDates,
  routeSelectClick,
  getClassificationData,
  validateFormFields,
  setRules,
  createRules,
} from "./event";

const VISIBILITY = {
  HIDE: "hide",
  SHOW: "show",
};

const conditionalFields = [
  { name: "club", id: "div_id_club" },
  { name: "weekdays", id: "div_id_weekdays" },
];

toggleElementArrayDisplay(conditionalFields, VISIBILITY.HIDE);

document.addEventListener("DOMContentLoaded", () => {
  const urlQuery = getUrlVars();
  // const slug = extractSlugFromQuerystring(urlQuery);
  const club_sqid = urlQuery && urlQuery.club_id ? urlQuery.club_id : "";
  const rideDate = extractRideDateFromQuerystring(urlQuery);

  const privacyElement = document.getElementById("event_create_privacy");
  const privacySelect = privacyElement.querySelector("select");
  setPrivacyListener(privacyElement, conditionalFields);

  const frequencyElement = document.getElementById("event_create_frequency");
  setFrequencyListener(frequencyElement, conditionalFields);

  togglePrivacyDisplay(privacySelect, conditionalFields);

  createRules();
  setRules();
  getClassificationData();
  validateFormFields();

  if (club_sqid) {
    preFillClub(club_sqid, conditionalFields);
  }

  if (rideDate) {
    preFillRideDates(rideDate);
  }
});

window.routeSelectClick = routeSelectClick;
