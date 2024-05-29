import {
  notificationSelectAll,
  getNotificationChecks,
  alterRequestPath,
  handleMarking,
} from "./main";

// add to the request url if "archive" or "move to inbox" is clicked
document.body.addEventListener("htmx:configRequest", function (evt) {
  let detail = evt.detail;
  const checked_ids = getNotificationChecks().toString();
  if (["mark-read-btn", "mark-unread-btn"].includes(detail.elt.id)) {
    handleMarking(detail, checked_ids);
  } else if (["archive-btn"].includes(detail.elt.id)) {
    alterRequestPath(detail, checked_ids, "archive_many");
  } else if (["move-to-inbox-btn"].includes(detail.elt.id)) {
    alterRequestPath(detail, checked_ids, "move_to_inbox");
  }
});

// abort the request if no checkboxes are selected
document.body.addEventListener("htmx:beforeRequest", function (evt) {
  const id = evt.detail.elt.id;
  if (
    [
      "mark-read-btn",
      "mark-unread-btn",
      "archive-btn",
      "move-to-inbox-btn",
    ].includes(id)
  ) {
    const checked_ids = getNotificationChecks().toString();
    if (!checked_ids || checked_ids.length === 0 || checked_ids == "") {
      evt.preventDefault();
    }
  }
});

const checkbox = document.getElementById("checkbox-all");
checkbox.addEventListener("change", () => {
  notificationSelectAll();
});
