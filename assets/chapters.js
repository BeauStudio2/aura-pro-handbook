const directory = document.querySelector(".directory");
const filter = document.querySelector(".chapter-filter");
const query = document.querySelector("#chapter-query");
const status = document.querySelector("#chapter-status");

function normalize(text) {
  return text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();
}

function filterChapters() {
  const terms = normalize(query.value).split(/\s+/).filter(Boolean);
  const chaptersFound = new Set();
  const sectionsFound = new Set();
  for (const group of directory.querySelectorAll(".chapter-group")) {
    const groupTitle = group.querySelector("h3").textContent;
    let visible = 0;
    for (const item of group.querySelectorAll(":scope > ul > li")) {
      const chapterLink = item.querySelector(":scope > a");
      const label = chapterLink.textContent;
      const description = item.querySelector(":scope > p").textContent;
      const chapterText = normalize([groupTitle, label, description].join(" "));
      const chapterMatches = terms.every(term => chapterText.includes(term));
      const sections = item.querySelector(".section-hits");
      let sectionMatches = 0;
      if (sections) {
        for (const section of sections.children) {
          const sectionLink = section.querySelector("a");
          const localText = normalize([sectionLink.textContent,
            section.querySelector("p").textContent, section.dataset.keywords].join(" "));
          const hasSectionTerm = terms.some(term => localText.includes(term));
          section.hidden = !hasSectionTerm || !terms.every(term =>
            localText.includes(term) || chapterText.includes(term));
          if (!section.hidden) {
            sectionMatches++;
            sectionsFound.add(sectionLink.href);
          }
        }
        sections.hidden = sectionMatches === 0;
      }
      item.hidden = !chapterMatches && sectionMatches === 0;
      if (!item.hidden) {
        visible++;
        chaptersFound.add(chapterLink.href.split("#")[0]);
        if (chapterLink.hash) sectionsFound.add(chapterLink.href);
      }
    }
    group.hidden = visible === 0;
  }
  const chapters = `${chaptersFound.size} ${chaptersFound.size === 1 ? "chapter" : "chapters"}`;
  const sections = `${sectionsFound.size} matching ${sectionsFound.size === 1 ? "section" : "sections"}`;
  status.textContent = terms.length ? `${chapters} · ${sections}` : "";
  if (terms.length && !chaptersFound.size) {
    status.textContent += ". Try a different topic or clear the search.";
  }
}

filter.hidden = false;
query.addEventListener("input", filterChapters);
window.addEventListener("pageshow", filterChapters);
for (const link of document.querySelectorAll('a[href="#chapters"]')) {
  link.addEventListener("click", () => {
    query.value = "";
    filterChapters();
  });
}
