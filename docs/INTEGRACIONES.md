Integraciones futuras (plan)

Google Drive / reportes:
- En offline-first, el sistema puede:
  1) Generar reportes (PDF/CSV) localmente.
  2) Enviar por email al gerente (SMTP) o subir a Drive (API) cuando haya conexión.

Requisitos para implementar:
- Credenciales y política:
  - Cuenta de Google Workspace o cuenta específica de empresa.
  - Carpeta Drive destino.
  - SMTP (Gmail/Workspace o servidor propio).

Diseño recomendado:
- Módulo nuevo: integraciones
  - Configuración: destinatarios, frecuencia, carpeta Drive.
  - Jobs: generar y subir/enviar.
- Evitar dependencias pesadas. Usar:
  - google-api-python-client (Drive) o subir por WebDAV si aplica.
  - smtplib para SMTP.

Seguridad:
- Nunca hardcodear credenciales.
- Usar variables de entorno o archivo local fuera del repo.
