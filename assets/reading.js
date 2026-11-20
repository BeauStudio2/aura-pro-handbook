function revealReadingTarget() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  if (!id) return;
  const target = document.getElementById(id);
  if (!target) return;
  let node = target;
  while (node) {
    if (node.tagName === "DETAILS") node.open = true;
    node = node.parentElement;
  }
  requestAnimationFrame(() => target.scrollIntoView({block: "start"}));
}
window.addEventListener("hashchange", revealReadingTarget);
window.addEventListener("pageshow", revealReadingTarget);
revealReadingTarget();
let readingPrintState = [];
window.addEventListener("beforeprint", () => {
  readingPrintState = [...document.querySelectorAll("details.reference-fold")].map(el => [el, el.open]);
  for (const [el] of readingPrintState) el.open = true;
});
window.addEventListener("afterprint", () => {
  for (const [el, wasOpen] of readingPrintState) el.open = wasOpen;
  readingPrintState = [];
});

document.addEventListener("click", event => {
  const link = event.target.closest?.("a[href]");
  if (!link) return;
  const destination = new URL(link.href, location.href);
  if (destination.origin === location.origin && destination.pathname === location.pathname && destination.hash) {
    requestAnimationFrame(revealReadingTarget);
  }
});
