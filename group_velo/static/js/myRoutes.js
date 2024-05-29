import { addCaret } from "./main";

const getCellValue = (tr, idx) =>
  tr.children[idx + 1].innerText || tr.children[idx + 1].textContent;

const comparer = (idx, asc) => (a, b) =>
  ((v1, v2) =>
    v1 !== "" && v2 !== "" && !isNaN(v1) && !isNaN(v2)
      ? v1 - v2
      : v1.toString().localeCompare(v2))(
    getCellValue(asc ? a : b, idx),
    getCellValue(asc ? b : a, idx),
  );

document.querySelectorAll("th").forEach(function (th) {
  th.addEventListener("click", function () {
    const thChildren = Array.from(th.parentNode.children);
    if (thChildren.indexOf(th) !== 0) {
      const table = document.getElementById("my-routes-table");
      const tableBody = document.getElementById("my-routes-table-body");
      const tableHead = document.getElementById("my-routes-table-head");
      const allTh = tableHead.querySelectorAll("tr > th");

      Array.from(table.querySelectorAll("tbody > tr:nth-child(n)"))
        .sort(comparer(thChildren.indexOf(th), (this.asc = !this.asc)))
        .forEach((tr) => tableBody.appendChild(tr));

      const caretDirection = this.asc ? "up" : "down";
      addCaret(caretDirection, th, allTh);
    }
  });
});
