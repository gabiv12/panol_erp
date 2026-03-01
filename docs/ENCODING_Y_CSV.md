# Encoding (acentos rotos) + Export CSV Auditoría

## 1) Arreglar acentos/encoding

Si ves textos como `dÃ­a`, `prÃ³ximo`, `SÃ¡enz`, etc., es un problema típico de **UTF-8 interpretado como Latin-1**.

Comando (primero previsualiza, luego aplica):

```powershell
python manage.py fix_encoding
python manage.py fix_encoding --write
```

Notas:
- Solo toca archivos de texto: `.py .html .md .js .css .txt`.
- No toca `.venv`, `media`, `staticfiles`, backups ni carpetas `_patch_apply_*`.

## 2) Exportar CSV de Auditoría

En **Auditoría** aparece el botón **Exportar CSV**. Exporta lo mismo que el filtro actual.

Opciones:
- `limit` (por querystring) limita filas exportadas (default 5000, máximo 20000).

Ejemplo:

```text
/auditoria/export.csv?days=7&username=admin&limit=20000
```

El CSV sale con BOM para que Excel muestre bien los acentos.
