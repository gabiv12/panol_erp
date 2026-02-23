from django import forms
from django.contrib.auth.models import User


# ==========================================================
# Usuarios (Administración)
# ----------------------------------------------------------
# Objetivo:
# - Mantener un formulario simple (username, nombre, email, flags)
# - Corregir el alta de usuarios: ahora permite definir contraseña.
# - En edición, la contraseña es opcional (solo se cambia si se carga).
#
# Nota:
# - No se toca el modelo ni migraciones.
# - Todo lo visual se apoya en las clases "ti-*".
# ==========================================================


_TI_INPUT = (
    "w-full px-3 py-2 rounded-lg border border-slate-300 bg-white text-slate-900 "
    "placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/20 "
    "dark:bg-slate-950 dark:text-slate-100 dark:border-slate-700"
)

_TI_CHECK = "h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-900/20 dark:border-slate-700"


class UsuarioBaseForm(forms.ModelForm):
    """Campos comunes para crear/editar usuarios."""

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": _TI_INPUT, "autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"class": _TI_INPUT, "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"class": _TI_INPUT, "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"class": _TI_INPUT, "autocomplete": "email"}),
            "is_active": forms.CheckboxInput(attrs={"class": _TI_CHECK}),
            "is_staff": forms.CheckboxInput(attrs={"class": _TI_CHECK}),
        }


class UsuarioCreateForm(UsuarioBaseForm):
    """Alta de usuario con contraseña obligatoria."""

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": _TI_INPUT,
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": _TI_INPUT,
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UsuarioUpdateForm(UsuarioBaseForm):
    """Edición de usuario. La contraseña es opcional."""

    password1 = forms.CharField(
        label="Nueva contraseña (opcional)",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": _TI_INPUT,
                "autocomplete": "new-password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Repetir nueva contraseña",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": _TI_INPUT,
                "autocomplete": "new-password",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")

        # Si el usuario quiere cambiar la contraseña, debe completar ambas.
        if (p1 and not p2) or (p2 and not p1):
            self.add_error("password2", "Para cambiar la contraseña, completá ambos campos.")
            return cleaned

        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user
