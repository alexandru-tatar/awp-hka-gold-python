(function () {
document.addEventListener("click", function (e) {
var t = e.target.closest && e.target.closest("[data-dialog-open]");
if (!t) return;
var d = document.getElementById(t.getAttribute("data-dialog-open"));
if (d && d.showModal) d.showModal();
});
document.addEventListener("close", function (e) {
var d = e.target;
if (!d || d.tagName !== "DIALOG" || d.returnValue !== "confirm") return;
var f = document.getElementById(d.getAttribute("data-submit-form") || "");
if (f) f.requestSubmit ? f.requestSubmit() : f.submit();
}, true);
document.addEventListener("submit", function (e) {
var b = document.getElementById(e.target.getAttribute("data-busy") || "");
if (!b) return;
if (!b.hidden) return e.preventDefault();
b.hidden = false;
var h = b.querySelector("[tabindex]");
if (h) h.focus();
});
window.addEventListener("pageshow", function (e) {
if (e.persisted) document.querySelectorAll(".busy").forEach(function (b) { b.hidden = true; });
});
})();
