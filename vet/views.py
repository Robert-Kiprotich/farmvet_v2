from django.shortcuts import render
from api.models import LivestockTrade

def index(request):
    return render(request, 'vet/index.html')


def about(request):
    return render(request, 'vet/about.html')    

def services(request):
    return render(request, 'vet/services.html')

def ourshop(request):
    return render(request, 'vet/Ourshop.html') 

def blog(request):
    return render(request, 'vet/blog.html')   

def contact(request):
    return render(request, 'vet/contact.html')  

def team(request):
    return render(request, 'vet/team.html')   

def events(request):
    return render(request, 'vet/events.html')

def trade_view(request):
    trades_list = LivestockTrade.objects.all()
    return render(
        request,
        'vet/trades_view.html',{'trades_list': trades_list}
       
    )  