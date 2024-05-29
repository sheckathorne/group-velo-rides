import {
  togglePrivacyDisplay,
  setPrivacyListener,
  swapRouteButtonWithInput,
  routeSelectClick,
  getClassificationData,
  handleSelectChange,
} from "./event";

const conditionalFields = [{ name: "club", id: "div_id_club" }];

document.addEventListener(
  "DOMContentLoaded",
  () => {
    const privacyElement = document.getElementById(
      "event_occurence_create_privacy",
    );
    const privacySelect = privacyElement.querySelector("select");
    setPrivacyListener(privacyElement);

    const routeName = document.getElementById("route_name").value;
    const routeUrl = document.getElementById("route_url").value;

    togglePrivacyDisplay(privacySelect, conditionalFields);
    getClassificationData();
    handleSelectChange();

    swapRouteButtonWithInput(
      routeName,
      routeUrl,
      "routeChoiceButton",
      "selected_route_text",
    );
  },
  false,
);

window.routeSelectClick = routeSelectClick;
