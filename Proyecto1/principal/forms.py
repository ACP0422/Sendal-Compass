# principal/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext as _

# pip install email-validator dnspython
from email_validator import validate_email, EmailNotValidError


# --- Validadores reutilizables ---
ONLY_LETTERS_RE = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-]{2,60}$"
only_letters_validator = RegexValidator(
    regex=ONLY_LETTERS_RE,
    message=_("Usa solo letras, espacios y guiones."),
)

TEL_ALLOWED = RegexValidator(
    regex=r"^[0-9+\s\-()]{10,25}$",
    message=_("Ingresa un número válido (con o sin +)."),
)

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "tempmail.dev",
    "yopmail.com",
    "guerrillamail.com",
    "discard.email",
}
ROLE_PREFIXES = {"admin", "support", "info", "noreply", "no-reply"}


def _collapse_spaces(s: str) -> str:
    return " ".join((s or "").split()).strip()


def _clean_email_robust(raw: str) -> str:
    """Valida sintaxis + dominios IDN + MX/A y devuelve el email normalizado."""
    try:
        v = validate_email(
            (raw or "").strip(),
            allow_smtputf8=True,
            check_deliverability=True,
        )
    except EmailNotValidError as e:
        msg = str(e)
        if "The domain name" in msg and "does not exist" in msg:
            raise ValidationError(
                _("El dominio del correo no existe. Verifica tu dirección.")
            )
        if "There is no DNS record" in msg:
            raise ValidationError(
                _("El dominio del correo no tiene registros de correo válidos.")
            )
        # fallback genérico
        raise ValidationError(
            _("Escribe un correo válido (ejemplo: nombre@dominio.com).")
        )

    email_norm = v.email
    local = v.local_part or ""
    domain = (v.domain or "").lower()

    if domain in DISPOSABLE_DOMAINS:
        raise ValidationError(_("Usa un correo personal o empresarial (no temporal)."))
    if local.lower() in ROLE_PREFIXES:
        raise ValidationError(_("Usa un correo personal (no cuentas genéricas)."))

    return email_norm


# =========================
#   FORMULARIO DE CONTACTO
#   (NO MODIFICAR)
# =========================
class ContactForm(forms.Form):
    nombre = forms.CharField(
        min_length=2,
        max_length=60,
        strip=True,
        validators=[only_letters_validator],
        error_messages={
            "required": _("Escribe tu nombre."),
            "min_length": _("El nombre es muy corto."),
            "max_length": _("El nombre es muy largo."),
        },
    )
    apellido = forms.CharField(
        min_length=2,
        max_length=60,
        strip=True,
        validators=[only_letters_validator],
        error_messages={
            "required": _("Escribe tu apellido."),
            "min_length": _("El apellido es muy corto."),
            "max_length": _("El apellido es muy largo."),
        },
    )
    email = forms.EmailField(
        max_length=120,
        error_messages={
            "required": _("Escribe tu correo."),
            "invalid": _("Escribe un correo válido."),
            "max_length": _("El correo es demasiado largo."),
        },
    )
    mensaje = forms.CharField(
        required=False,
        strip=True,
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    # Honeypot (campo oculto en el HTML)
    website = forms.CharField(required=False)

    # --------- Limpiadores ---------
    def clean_website(self):
        v = (self.cleaned_data.get("website") or "").strip()
        if v:
            raise ValidationError(_("Solicitud no válida."))
        return v

    def clean_nombre(self):
        return _collapse_spaces(self.cleaned_data.get("nombre"))

    def clean_apellido(self):
        return _collapse_spaces(self.cleaned_data.get("apellido"))

    def clean_mensaje(self):
        return _collapse_spaces(self.cleaned_data.get("mensaje"))

    def clean_email(self):
        raw = (self.cleaned_data.get("email") or "").strip()
        try:
            v = validate_email(
                raw,
                allow_smtputf8=True,
                check_deliverability=True,
            )
        except EmailNotValidError as e:
            msg = str(e)
            # Mensajes personalizados en español
            if "The domain name" in msg and "does not exist" in msg:
                raise ValidationError(
                    _("El dominio del correo no existe. Verifica tu dirección.")
                )
            if "address is not valid" in msg:
                raise ValidationError(
                    _("Escribe un correo válido (ejemplo: nombre@dominio.com).")
                )
            if "There is no DNS record" in msg:
                raise ValidationError(
                    _("El dominio del correo no tiene registros de correo válidos.")
                )
            # fallback
            raise ValidationError(_("Correo no válido. Verifica tu dirección."))

        # E-mail normalizado
        email_norm = v.email
        local = v.local_part or ""
        domain = (v.domain or "").lower()

        # Dominios desechables
        if domain in DISPOSABLE_DOMAINS:
            raise ValidationError(
                _("Usa un correo personal o empresarial (no temporal).")
            )

        # Correos genéricos no deseados
        if local.lower() in ROLE_PREFIXES:
            raise ValidationError(_("Usa un correo personal (no cuentas genéricas)."))

        return email_norm


# =========================
#   FORMULARIO DEL INDEX
# =========================
# forms.py (reemplaza SOLAMENTE esta clase)
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext as _

# Reutiliza los mismos helpers/sets que ya tienes arriba en el archivo:
# - only_letters_validator
# - DISPOSABLE_DOMAINS
# - ROLE_PREFIXES
from email_validator import validate_email, EmailNotValidError

# Si no lo tienes definido aún:
ONLY_LETTERS_RE = r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s\-]{2,60}$"
only_letters_validator = RegexValidator(
    regex=ONLY_LETTERS_RE,
    message=_("Usa solo letras, espacios y guiones."),
)

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "tempmail.dev",
    "yopmail.com",
    "guerrillamail.com",
    "discard.email",
}
ROLE_PREFIXES = {"admin", "support", "info", "noreply", "no-reply"}


def _collapse_spaces(s: str) -> str:
    return " ".join((s or "").split()).strip()


class CotizaHomeForm(forms.Form):
    nombre = forms.CharField(
        max_length=60,
        required=True,
        label=_("Nombre"),
        validators=[only_letters_validator],
        error_messages={
            "required": _("Escribe tu nombre."),
            "max_length": _("El nombre es muy largo."),
        },
    )
    apellido = forms.CharField(
        max_length=60,
        required=True,
        label=_("Apellido"),
        validators=[only_letters_validator],
        error_messages={
            "required": _("Escribe tu apellido."),
            "max_length": _("El apellido es muy largo."),
        },
    )
    email = forms.EmailField(
        max_length=120,
        required=True,
        label=_("Correo electrónico"),
        error_messages={
            "required": _("Escribe tu correo."),
            "invalid": _("Escribe un correo válido."),
            "max_length": _("El correo es demasiado largo."),
        },
    )
    telefono = forms.CharField(
        required=True,
        label=_("Número de contacto"),
        help_text=_("Incluye lada; 10–15 dígitos en total (con o sin +)."),
        error_messages={"required": _("Escribe tu número.")},
    )
    tipo = forms.CharField(
        max_length=80,
        required=True,
        label=_("Tipo de propiedad"),
        validators=[only_letters_validator],
        error_messages={"required": _("Escribe el tipo de propiedad.")},
    )
    ubicacion = forms.CharField(
        max_length=80,
        required=True,
        label=_("Ubicación"),
        validators=[only_letters_validator],
        error_messages={"required": _("Escribe la ubicación.")},
    )

    # Honeypot
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    # --- Normalizaciones ligeras ---
    def clean_website(self):
        if (self.cleaned_data.get("website") or "").strip():
            raise ValidationError(_("Solicitud no válida."))
        return ""

    def clean_nombre(self):
        return _collapse_spaces(self.cleaned_data.get("nombre"))

    def clean_apellido(self):
        return _collapse_spaces(self.cleaned_data.get("apellido"))

    def clean_tipo(self):
        return _collapse_spaces(self.cleaned_data.get("tipo"))

    def clean_ubicacion(self):
        return _collapse_spaces(self.cleaned_data.get("ubicacion"))

    # --- Teléfono: 10–15 dígitos reales, con/sin '+' ---
    def clean_telefono(self):
        s = (self.cleaned_data.get("telefono") or "").strip()
        digits = sum(ch.isdigit() for ch in s)
        if digits < 10 or digits > 15:
            raise ValidationError(
                _("Ingresa un teléfono válido (10–15 dígitos, con o sin +).")
            )
        return s

    # --- Email: sintaxis + deliverability + dominios desechables/roles ---
    def clean_email(self):
        raw = (self.cleaned_data.get("email") or "").strip()
        try:
            v = validate_email(raw, allow_smtputf8=True, check_deliverability=True)
        except EmailNotValidError as e:
            msg = str(e)
            if "domain name" in msg and "does not exist" in msg:
                raise ValidationError(
                    _("El dominio del correo no existe. Verifica tu dirección.")
                )
            if "There is no DNS record" in msg:
                raise ValidationError(
                    _("El dominio no tiene registros de correo válidos (MX/AAAA).")
                )
            # fallback genérico
            raise ValidationError(
                _("Escribe un correo válido, por ejemplo nombre@dominio.com.")
            )

        email_norm = v.email
        local = (v.local_part or "").lower()
        domain = (v.domain or "").lower()

        if domain in DISPOSABLE_DOMAINS:
            raise ValidationError(
                _("Usa un correo personal o empresarial (no temporal).")
            )
        if local in ROLE_PREFIXES:
            raise ValidationError(_("Usa un correo personal (no cuentas genéricas)."))

        return email_norm
