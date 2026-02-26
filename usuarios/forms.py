from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.permissions import ROLE_CHOICES, ROLE_ADMIN, role_group_name

User = get_user_model()


class UsuarioForm(forms.ModelForm):
    """Alta/edición de usuario operativo.

    Incluye un selector de **Rol** (grupo) para definir qué módulos ve el usuario.

    Nota:
    - El rol se persiste como **Group** de Django.
    - Permisos reales se inicializan con: `python manage.py init_roles`.
    """

    role = forms.ChoiceField(
        label="Rol",
        choices=ROLE_CHOICES,
        required=True,
        help_text="Define qué módulos ve el usuario (menú y permisos).",
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(render_value=True),
        required=False,
        help_text="Dejá vacío si no querés cambiarla.",
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        widget=forms.PasswordInput(render_value=True),
        required=False,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
        ]
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "off"}),
            "first_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "off"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # UI class
        for _, field in self.fields.items():
            w = field.widget
            cls = (w.attrs.get("class") or "").strip()
            if "ti-input" not in cls and not isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = (cls + " ti-input").strip()

        # Rol inicial (por grupo)
        inst = getattr(self, "instance", None)
        if inst and getattr(inst, "pk", None):
            # detectar rol por grupo
            role = None
            user_groups = set(inst.groups.values_list("name", flat=True))
            for value, _label in ROLE_CHOICES:
                if role_group_name(value) in user_groups:
                    role = value
                    break
            self.initial.setdefault("role", role or ROLE_ADMIN)
        else:
            self.initial.setdefault("role", ROLE_ADMIN)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1") or ""
        p2 = cleaned.get("password2") or ""
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            if len(p1) < 4:
                self.add_error("password1", "La contraseña debe tener al menos 4 caracteres.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        p1 = self.cleaned_data.get("password1") or ""
        if p1:
            obj.set_password(p1)

        if commit:
            obj.save()

            # Aplicar rol -> grupo
            role = self.cleaned_data.get("role")
            if role:
                group_name = role_group_name(role)
                g, _ = Group.objects.get_or_create(name=group_name)
                obj.groups.clear()
                obj.groups.add(g)

        return obj
