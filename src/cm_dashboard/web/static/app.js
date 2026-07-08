document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-chart-bar]").forEach((bar) => {
    const value = Number(bar.getAttribute("data-value") || "0");
    const max = Number(bar.getAttribute("data-max") || "0");
    const width = max > 0 ? Math.max(2, Math.round((value / max) * 100)) : 0;
    bar.style.width = `${width}%`;
  });
});
