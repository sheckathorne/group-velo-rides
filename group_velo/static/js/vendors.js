console.log("Vendors.js loaded, window.Iodine set:");
import "htmx.org";
import Alpine from "alpinejs";
import mask from "@alpinejs/mask";
Alpine.plugin(mask);
import Tooltip from "@ryangjchandler/alpine-tooltip";
import Iodine from "@caneara/iodine";
const instance = new Iodine();

Alpine.plugin(Tooltip);

window.Alpine = Alpine;
Alpine.start();

window.htmx = require("htmx.org");
