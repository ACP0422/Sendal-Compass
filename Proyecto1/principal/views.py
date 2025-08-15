from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'pages/index.html')

def contact(request):
    return render(request, 'pages/contact.html')

def valladolid(request):
    return render(request, 'pages/valladolid.html')

def tulum(request):
    return render(request, 'pages/tulum.html')