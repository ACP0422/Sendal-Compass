from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'pages/index.html')

def contacto(request):
    return render(request, 'pages/contacto.html')

def cotizador(request):
    return render(request, "pages/cotizador.html")

def valladolid(request):
    return render(request, 'pages/valladolid.html')

def tulum(request):
    return render(request, 'pages/tulum.html')

