# Entrega rápida (Operación)

## 1) Horarios fijos (diagrama base)
El diagrama operativo se carga desde `seed/diagrama_template.csv`.

Generar 60 días (recomendado) desde una fecha:

```powershell
python manage.py seed_horarios_fijos --fecha 2026-02-27 --days 60
```

- No borra: completa faltantes. Usar `--force` para completar aunque ya existan salidas (sigue sin borrar).
- Si falta algún interno del template, usa el primer colectivo como fallback.

## 2) Manual y pruebas manuales
- Manual: `docs/MANUAL_USUARIO.md`
- Capturas: `docs/_img/`
- Plan de pruebas manuales: `docs/PLAN_PRUEBAS_MANUALES.md`
