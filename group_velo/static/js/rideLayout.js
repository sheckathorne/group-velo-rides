import { clearFilter, resizeRideMapFrames } from "./event";

document.addEventListener(
  "DOMContentLoaded",
  function () {
    resizeRideMapFrames();
    document.querySelectorAll(".clearFilterButton").forEach((btn) => {
      btn.addEventListener("click", clearFilter);
    });
  },
  false,
);
