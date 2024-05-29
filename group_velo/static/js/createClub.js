import { setRules, createRules } from "./club";

const tooltips = [
  {
    elementId: "active_check_row",
    tooltipText:
      "Inactive clubs are only visible to the club creator. No activities can take place for a deactivated club.",
  },
  {
    elementId: "private_attendence_row",
    tooltipText:
      "If attendence is private, only ride leaders can see the ride roster.",
  },
  {
    elementId: "private_waitlist_row",
    tooltipText:
      "If waitlists are private, only ride leaders can see the waitlist roster.",
  },
  {
    elementId: "allow_ride_discussion_row",
    tooltipText:
      "If discussion is allowed, there is a discussion page for each ride.",
  },
  {
    elementId: "strict_ride_classification_row",
    tooltipText:
      'You may specify pre-defined upper and lower pace limits for ride surface and group classification pairs. For example - a ride on a "Road" surface with a pace classification of "A", or a ride on a "Gravel" surface with a pace classification of "B". When selected, these pace limits cannot be violated during event creation.',
  },
];

document.addEventListener("DOMContentLoaded", () => {
  createRules();
  setRules();

  tooltips.forEach((item) => {
    const rootElement = document.getElementById(item.elementId);
    rootElement.setAttribute("x-data", `{ tooltip: '${item.tooltipText}' }`);

    const hoverElement = rootElement.querySelector("label");
    hoverElement.setAttribute("x-tooltip.placement.top-end", "tooltip");
  });
});
