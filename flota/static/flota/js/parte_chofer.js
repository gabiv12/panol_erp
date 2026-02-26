(function () {
  const step1 = document.getElementById("step1");
  const step2 = document.getElementById("step2");
  if (!step1 || !step2) return;

  function showStep(n) {
    if (n === 1) {
      step1.classList.remove("hidden");
      step2.classList.add("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      step1.classList.add("hidden");
      step2.classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  document.addEventListener("click", function (ev) {
    const t = ev.target;
    if (t && t.matches("[data-next-step]")) showStep(2);
    if (t && t.matches("[data-prev-step]")) showStep(1);
  });
})();
