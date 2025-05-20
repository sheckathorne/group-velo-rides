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
      "You may specify pre-defined upper and lower pace limits for ride surface and group classification pairs. For example - a ride on a &quot;Road&quot; surface with a pace classification of &quot;A&quot;, or a ride on a &quot;Gravel&quot; surface with a pace classification of &quot;B&quot;. When selected, these pace limits cannot be violated during event creation.",
  },
];

document.addEventListener("DOMContentLoaded", () => {
  createRules();
  setRules();

  document
    .getElementById("div_id_privacy_level")
    .querySelector(".asteriskField")
    ?.remove();

  tooltips.forEach((item) => {
    const tooltipHTML = `
      <div id="${item.elementId}_tooltip" x-data x-tooltip.raw='${item.tooltipText}' class="relative group">
        <div class="cursor-help text-gray-500 dark:text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 16v-4"></path>
            <path d="M12 8h.01"></path>
          </svg>
        </div>
      </div>
    `;

    const rootElement = document.getElementById(item.elementId);
    const firstDiv = rootElement.querySelector("div");
    firstDiv.insertAdjacentHTML("beforeend", tooltipHTML);
  });
});
