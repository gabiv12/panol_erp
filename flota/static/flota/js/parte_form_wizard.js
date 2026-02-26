(function () {
  const step1 = document.getElementById("step1");
  const step2 = document.getElementById("step2");
  if (!step1 || !step2) return;

  const tipoSel = document.getElementById("id_tipo");
  const mant = document.getElementById("mant_block");
  const aux = document.getElementById("aux_block");

  function toggleBlocks() {
    if (!tipoSel) return;
    const v = (tipoSel.value || "").toUpperCase();
    if (mant) mant.style.display = (v === "MANTENIMIENTO") ? "" : "none";
    if (aux) aux.style.display = (v === "AUXILIO") ? "" : "none";
  }

  function showStep(n) {
    if (n === 1) {
      step1.classList.remove("hidden");
      step2.classList.add("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      step1.classList.add("hidden");
      step2.classList.remove("hidden");
      toggleBlocks();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  document.addEventListener("click", function (ev) {
    const t = ev.target;
    if (t && t.matches("[data-next-step]")) showStep(2);
    if (t && t.matches("[data-prev-step]")) showStep(1);
  });

  if (tipoSel) tipoSel.addEventListener("change", toggleBlocks);
})();
