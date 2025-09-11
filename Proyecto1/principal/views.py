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

def hacienda(request):
    return render(request, 'pages/hacienda.html')

def predio1(request):
    return render(request, 'pages/predio1.html')

def predio2(request):
    return render(request, 'pages/predio2.html')

def komchen(request):
    return render(request, 'pages/komchen.html')

def cotizadorKomchen(request):
    return render(request, 'pages/cotizador-komchen.html')

