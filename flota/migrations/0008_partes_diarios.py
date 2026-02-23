from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('flota', '0007_colectivo_mantenimiento_matafuego_limpieza'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ParteDiario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_evento', models.DateTimeField(default=django.utils.timezone.now)),
                ('tipo', models.CharField(choices=[('CHECKLIST', 'Checklist'), ('INCIDENCIA', 'Incidencia'), ('MANTENIMIENTO', 'Mantenimiento'), ('AUXILIO', 'Auxilio')], default='INCIDENCIA', max_length=20)),
                ('severidad', models.CharField(choices=[('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Alta'), ('CRITICA', 'Crítica')], default='MEDIA', max_length=10)),
                ('estado', models.CharField(choices=[('ABIERTO', 'Abierto'), ('EN_PROCESO', 'En proceso'), ('RESUELTO', 'Resuelto')], default='ABIERTO', max_length=15)),
                ('odometro_km', models.PositiveIntegerField(blank=True, null=True)),
                ('accion_mantenimiento', models.CharField(blank=True, choices=[('ACEITE', 'Cambio de aceite'), ('FILTROS', 'Cambio de filtros'), ('LIMPIEZA', 'Limpieza'), ('MATAFUEGO', 'Control matafuego'), ('OTRO', 'Otro')], default='', max_length=20)),
                ('km_mantenimiento', models.PositiveIntegerField(blank=True, null=True)),
                ('matafuego_vto_nuevo', models.DateField(blank=True, null=True)),
                ('auxilio_inicio', models.DateTimeField(blank=True, null=True)),
                ('auxilio_fin', models.DateTimeField(blank=True, null=True)),
                ('descripcion', models.TextField()),
                ('observaciones', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('colectivo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='partes_diarios', to='flota.colectivo')),
                ('reportado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partes_diarios_reportados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-fecha_evento', '-id'],
            },
        ),
        migrations.CreateModel(
            name='ParteDiarioAdjunto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to='partes_diarios/%Y/%m/%d/')),
                ('descripcion', models.CharField(blank=True, default='', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjuntos', to='flota.partediario')),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='partediario',
            index=models.Index(fields=['colectivo', 'fecha_evento'], name='idx_parte_colectivo_fecha'),
        ),
        migrations.AddIndex(
            model_name='partediario',
            index=models.Index(fields=['tipo', 'estado'], name='idx_parte_tipo_estado'),
        ),
    ]