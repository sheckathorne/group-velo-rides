import { setAlertTimeout } from "./main";

document.addEventListener(
  "DOMContentLoaded",
  function () {
    setAlertTimeout();
    document.querySelectorAll(".join-club-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        setAlertTimeout();
      });
    });
  },
  false,
);
