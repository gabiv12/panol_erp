/* static/js/pages/login.js
   Login - UX específico
   - Autofocus en usuario
   - Toggle password se maneja desde app.js (data-toggle-password)
*/
document.addEventListener("DOMContentLoaded", function () {
  const userInput = document.getElementById("id_username") || document.getElementById("username");
  if (userInput) userInput.focus();
});
