// usuarios/static/usuarios/js/usuario_list.js
// Listado de usuarios (Administración)
// - Filtro client-side complementario (sin romper filtro server-side)
// - Mantiene todo el JS dentro de la app "usuarios"

(function () {
  function norm(s) {
    return (s || "").toString().trim().toLowerCase();
  }

  function init() {
    var input = document.getElementById("userSearch");
    var table = document.getElementById("usuariosTable");
    if (!input || !table) return;

    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody [data-user-row]"));
    if (!rows.length) return;

    input.addEventListener("input", function () {
      var q = norm(input.value);
      var visible = 0;

      rows.forEach(function (tr) {
        var hay = [
          tr.getAttribute("data-username"),
          tr.getAttribute("data-name"),
          tr.getAttribute("data-email"),
        ]
          .map(norm)
          .join(" ");

        var ok = !q || hay.indexOf(q) !== -1;
        tr.style.display = ok ? "" : "none";
        if (ok) visible++;
      });

      var counter = document.getElementById("usuariosCount");
      if (counter) counter.textContent = String(visible);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
