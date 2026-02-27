from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

from core.permissions import (
    ROLE_CHOICES,
    ROLE_ADMIN,
    role_group_name,
    set_role_group,
    MODULE_CHOICES,
    set_module_groups,
    user_modules,
)

User = get_user_model()


class UsuarioForm(forms.ModelForm):
    role = forms.ChoiceField(
        label="Rol",
        choices=ROLE_CHOICES,
        required=True,
        help_text="Perfil principal del usuario (grupos/roles base).",
    )

    modules = forms.MultipleChoiceField(
        label="Módulos (accesos adicionales)",
        choices=MODULE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Accesos extra además del rol.",
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

        for _, field in self.fields.items():
            w = field.widget
            cls = (w.attrs.get("class") or "").strip()
            if "ti-input" not in cls and not isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = (cls + " ti-input").strip()

        inst = getattr(self, "instance", None)
        if inst and getattr(inst, "pk", None):
            role = None
            user_groups = set(inst.groups.values_list("name", flat=True))
            for value, _label in ROLE_CHOICES:
                if role_group_name(value) in user_groups:
                    role = value
                    break
            self.initial.setdefault("role", role or ROLE_ADMIN)
            self.initial.setdefault("modules", user_modules(inst))
        else:
            self.initial.setdefault("role", ROLE_ADMIN)
            self.initial.setdefault("modules", [])

    def clean(self):
        cleaned = super().clean()
        p1 = (cleaned.get("password1") or "").strip()
        p2 = (cleaned.get("password2") or "").strip()
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            if len(p1) < 4:
                self.add_error("password1", "La contraseña debe tener al menos 4 caracteres.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        p1 = (self.cleaned_data.get("password1") or "").strip()
        if p1:
            obj.set_password(p1)

        if commit:
            obj.save()

            role = self.cleaned_data.get("role") or ROLE_ADMIN
            set_role_group(obj, role)

            modules = self.cleaned_data.get("modules") or []
            set_module_groups(obj, list(modules))

            # Robustez: aseguramos que el password queda persistido incluso si
            # alguna lógica posterior toca el objeto (tests de login).
            if p1:
                obj.set_password(p1)
                obj.save(update_fields=["password"])

        return obj


class UsuarioCreateForm(UsuarioForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].required = True
        self.fields["password2"].required = True
        self.fields["password1"].help_text = "Obligatoria. Mínimo 4 caracteres."


class UsuarioUpdateForm(UsuarioForm):
    pass
