param(
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
Write-Host "== Patch: 2 matafuegos por unidad (La Termal ERP) =="

function Save-Utf8([string]$path, [string]$content) {
  $content | Set-Content -Encoding UTF8 $path
}

# 1) Copiar migraciÃ³n
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$patchRoot = Split-Path $scriptDir -Parent
$srcMig = Join-Path $patchRoot "flota\migrations\0009_colectivo_matafuego_2.py"
$dstMigDir = Join-Path $ProjectRoot "flota\migrations"
$dstMig = Join-Path $dstMigDir "0009_colectivo_matafuego_2.py"
New-Item -ItemType Directory -Force -Path $dstMigDir | Out-Null
if (!(Test-Path $dstMig)) {
  Copy-Item $srcMig $dstMig -Force
} else {
  # Si existe, evitamos copiar sobre sí mismo
  if ((Resolve-Path $srcMig).Path -ne (Resolve-Path $dstMig).Path) {
    Copy-Item $srcMig $dstMig -Force
  }
}
Write-Host "OK: migraciÃ³n copiada -> flota/migrations/0009_colectivo_matafuego_2.py"

# 2) Patch flota/models.py: agrega campo + propiedades (si no existen)
$models = Join-Path $ProjectRoot "flota\models.py"
if (!(Test-Path $models)) { throw "No existe: $models" }

$c = Get-Content $models -Raw

# Asegurar import timezone
if ($c -notmatch "from django\.utils import timezone") {
  $c = $c -replace "(from django\.db import models\r?\n)", ('$1' + "from django.utils import timezone`r`n")
}

# Agregar el campo si no existe
if ($c -notmatch "matafuego_vencimiento_2") {

  $field = @'
    matafuego_vencimiento_2 = models.DateField(
        null=True,
        blank=True,
        verbose_name="Vencimiento matafuego 2",
        help_text="Fecha de vencimiento del matafuego 2 de la unidad.",
    )

'@

  if ($c -match "(?s)(matafuego_vencimiento\s*=\s*models\.DateField\([^\)]*\)\s*\r?\n)") {
    $c = [regex]::Replace($c, "(?s)(matafuego_vencimiento\s*=\s*models\.DateField\([^\)]*\)\s*\r?\n)", '$1' + "`r`n" + $field, 1)
  } elseif ($c -match "(?s)(matafuego_ultimo_control\s*=\s*models\.DateField\([^\)]*\)\s*\r?\n)") {
    $c = [regex]::Replace($c, "(?s)(matafuego_ultimo_control\s*=\s*models\.DateField\([^\)]*\)\s*\r?\n)", '$1' + "`r`n" + $field, 1)
  } else {
    Write-Host "WARNING: No encontrÃ© matafuego_vencimiento/matafuego_ultimo_control en models.py; intento insertar antes de class Meta."
    $c = [regex]::Replace($c, "(?s)(\r?\n\s*class Meta:)", "`r`n" + $field + "`r`n    class Meta:", 1)
  }

  Write-Host "OK: campo matafuego_vencimiento_2 agregado en models.py"
} else {
  Write-Host "OK: models.py ya tiene matafuego_vencimiento_2"
}

# Agregar propiedades si no existen
if ($c -notmatch "def matafuego_proximo_vencimiento") {
  $props = @'

    @property
    def matafuego_proximo_vencimiento(self):
        # Devuelve el vencimiento mÃ¡s prÃ³ximo entre matafuego 1 y 2 (o None).
        fechas = [d for d in [getattr(self, "matafuego_vencimiento", None), getattr(self, "matafuego_vencimiento_2", None)] if d]
        return min(fechas) if fechas else None

    @property
    def matafuego_dias_restantes(self):
        # DÃ­as restantes al prÃ³ximo vencimiento (negativo si estÃ¡ vencido).
        vto = self.matafuego_proximo_vencimiento
        if not vto:
            return None
        return (vto - timezone.localdate()).days

'@

  if ($c -match "(?s)(\r?\n\s*def __str__\s*\()") {
    $c = [regex]::Replace($c, "(?s)(\r?\n\s*def __str__\s*\()", $props + "`r`n    def __str__(", 1)
  } elseif ($c -match "(?s)(\r?\n\s*class Meta:)") {
    $c = [regex]::Replace($c, "(?s)(\r?\n\s*class Meta:)", $props + "`r`n    class Meta:", 1)
  } else {
    $c = $c + $props
  }
  Write-Host "OK: propiedades agregadas (matafuego_proximo_vencimiento / matafuego_dias_restantes)"
}

Save-Utf8 $models $c

# 3) Patch flota/forms.py para incluir el campo nuevo si usan fields explÃ­citos
$forms = Join-Path $ProjectRoot "flota\forms.py"
if (Test-Path $forms) {
  $fc = Get-Content $forms -Raw
  if ($fc -notmatch "matafuego_vencimiento_2") {
    if ($fc -match "fields\s*=\s*\[") {
      $fc = [regex]::Replace($fc, "fields\s*=\s*\[(?s)(.*?)\]", { param($m)
        $inner = $m.Groups[1].Value
        if ($inner -match "matafuego_vencimiento_2") { return $m.Value }
        if ($inner -match "matafuego_vencimiento") {
          $inner = $inner -replace "('matafuego_vencimiento'\s*,)", "`$1`r`n            'matafuego_vencimiento_2',"
        } else {
          $inner = $inner + "`r`n            'matafuego_vencimiento_2',"
        }
        return "fields = [" + $inner + "]"
      }, 1)
      Save-Utf8 $forms $fc
      Write-Host "OK: forms.py fields[] actualizado"
    } elseif ($fc -match "fields\s*=\s*\(") {
      $fc = [regex]::Replace($fc, "fields\s*=\s*\((?s)(.*?)\)", { param($m)
        $inner = $m.Groups[1].Value
        if ($inner -match "matafuego_vencimiento_2") { return $m.Value }
        if ($inner -match "matafuego_vencimiento") {
          $inner = $inner -replace "('matafuego_vencimiento'\s*,)", "`$1`r`n            'matafuego_vencimiento_2',"
        } else {
          $inner = $inner + "`r`n            'matafuego_vencimiento_2',"
        }
        return "fields = (" + $inner + ")"
      }, 1)
      Save-Utf8 $forms $fc
      Write-Host "OK: forms.py fields() actualizado"
    } else {
      Write-Host "INFO: forms.py no usa fields explÃ­citos; no hace falta cambiar."
    }
  } else {
    Write-Host "OK: forms.py ya menciona matafuego_vencimiento_2"
  }
}

# 4) Patch template colectivo_form.html: agrega bloque didÃ¡ctico con iconos
$tpl = Join-Path $ProjectRoot "flota\templates\flota\colectivo_form.html"
if (!(Test-Path $tpl)) {
  Write-Host "WARNING: No existe $tpl (omitido)."
} else {
  $tc = Get-Content $tpl -Raw

  if ($tc -notmatch "matafuego_vencimiento_2") {

    $insert = @'
<!-- Matafuegos (2) - didÃ¡ctico -->
<div class="ti-card p-4 mt-4">
  <div class="flex items-center justify-between gap-3">
    <div>
      <div class="text-sm font-semibold">Matafuegos</div>
      <div class="text-xs ti-subtitle">La unidad lleva 2 matafuegos. CargÃ¡ las fechas de vencimiento. El sistema usa el vencimiento mÃ¡s prÃ³ximo para alertas.</div>
    </div>
    {% with prox=form.instance.matafuego_proximo_vencimiento dias=form.instance.matafuego_dias_restantes %}
      <div class="text-right">
        <div class="text-xs ti-subtitle">PrÃ³ximo vencimiento</div>
        {% if prox %}
          <div class="text-sm font-semibold tabular-nums">{{ prox|date:"d/m/Y" }}</div>
          <div class="text-xs ti-subtitle">{% if dias < 0 %}Vencido{% elif dias <= 7 %}Por vencer{% else %}OK{% endif %}</div>
        {% else %}
          <div class="text-sm font-semibold">Pendiente</div>
        {% endif %}
      </div>
    {% endwith %}
  </div>

  <div class="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
    <!-- Matafuego 1 -->
    <div class="rounded-2xl border border-slate-200 dark:border-slate-800 p-3">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" class="h-6 w-6" aria-hidden="true">
            <path d="M9 3h6v3H9V3Z" stroke="currentColor" stroke-width="1.8"/>
            <path d="M10 6h4l1 2v13H9V8l1-2Z" stroke="currentColor" stroke-width="1.8"/>
            <path d="M15 9h3v2h-3" stroke="currentColor" stroke-width="1.8"/>
            <path d="M6 10c0-2 1-3 3-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold">Matafuego 1</div>
          <div class="text-xs ti-subtitle">Vencimiento</div>
        </div>
      </div>
      <div class="mt-3">
        {{ form.matafuego_vencimiento }}
        {% if form.matafuego_vencimiento.help_text %}<div class="mt-1 text-xs ti-subtitle">{{ form.matafuego_vencimiento.help_text }}</div>{% endif %}
        {% for e in form.matafuego_vencimiento.errors %}<div class="mt-1 text-xs text-red-500">{{ e }}</div>{% endfor %}
      </div>
    </div>

    <!-- Matafuego 2 -->
    <div class="rounded-2xl border border-slate-200 dark:border-slate-800 p-3">
      <div class="flex items-center gap-3">
        <div class="h-10 w-10 rounded-xl bg-slate-100 dark:bg-slate-900 flex items-center justify-center">
          <div class="relative">
            <svg viewBox="0 0 24 24" fill="none" class="h-6 w-6" aria-hidden="true">
              <path d="M9 3h6v3H9V3Z" stroke="currentColor" stroke-width="1.8"/>
              <path d="M10 6h4l1 2v13H9V8l1-2Z" stroke="currentColor" stroke-width="1.8"/>
              <path d="M15 9h3v2h-3" stroke="currentColor" stroke-width="1.8"/>
              <path d="M6 10c0-2 1-3 3-3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            <span class="absolute -right-2 -top-2 h-5 w-5 rounded-full bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-[10px] font-semibold flex items-center justify-center">2</span>
          </div>
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold">Matafuego 2</div>
          <div class="text-xs ti-subtitle">Vencimiento</div>
        </div>
      </div>
      <div class="mt-3">
        {{ form.matafuego_vencimiento_2 }}
        {% if form.matafuego_vencimiento_2.help_text %}<div class="mt-1 text-xs ti-subtitle">{{ form.matafuego_vencimiento_2.help_text }}</div>{% endif %}
        {% for e in form.matafuego_vencimiento_2.errors %}<div class="mt-1 text-xs text-red-500">{{ e }}</div>{% endfor %}
      </div>
    </div>
  </div>

  <div class="mt-3 text-xs ti-subtitle">
    Consejo: si no tenÃ©s la fecha exacta ahora, podÃ©s dejarla vacÃ­a y completarla despuÃ©s. Lo importante es cargarla antes del vencimiento.
  </div>
</div>
'@

    if ($tc -match "form\.matafuego_vencimiento") {
      $tc = [regex]::Replace($tc, "(?s)(\{\{\s*form\.matafuego_vencimiento\s*\}\})", '$1' + "`r`n" + $insert, 1)
      Save-Utf8 $tpl $tc
      Write-Host "OK: UI de matafuegos agregada en colectivo_form.html"
    } else {
      Write-Host "WARNING: No encontrÃ© 'form.matafuego_vencimiento' en el template. No inserto."
    }
  } else {
    Write-Host "OK: colectivo_form.html ya tiene matafuego_vencimiento_2"
  }
}

Write-Host ""
Write-Host "Siguiente:"
Write-Host " - python manage.py migrate"
Write-Host " - Reiniciar server y probar editar colectivo"

