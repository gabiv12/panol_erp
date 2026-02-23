(function () {
  function qs(id) { return document.getElementById(id); }

  function openSidebar() {
    const sidebar = qs("sidebar");
    const overlay = qs("sidebarOverlay");
    if (!sidebar || !overlay) return;

    sidebar.classList.remove("-translate-x-full");
    overlay.classList.remove("hidden");
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    const sidebar = qs("sidebar");
    const overlay = qs("sidebarOverlay");
    if (!sidebar || !overlay) return;

    sidebar.classList.add("-translate-x-full");
    overlay.classList.add("hidden");
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  document.addEventListener("DOMContentLoaded", () => {
    const openBtn = qs("sidebarOpen");
    const closeBtn = qs("sidebarClose");
    const overlay = qs("sidebarOverlay");

    if (openBtn) openBtn.addEventListener("click", openSidebar);
    if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
    if (overlay) overlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeSidebar();
    });
  });
})();