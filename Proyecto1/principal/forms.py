from django import forms

class ContactForm(forms.Form):
    nombre   = forms.CharField(max_length=80)
    apellido = forms.CharField(max_length=120)
    email    = forms.EmailField()
    mensaje  = forms.CharField(widget=forms.Textarea, max_length=4000, required=False)
    # Honeypot: campo oculto; si llega con contenido, se ignora el envío
    website  = forms.CharField(required=False)  # <- no lo muestres al usuario
