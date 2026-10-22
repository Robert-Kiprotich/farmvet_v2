from django.urls import path
from .import views


urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('ourshop/', views.ourshop, name='Ourshop'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),  
    path('team/', views.team, name='team'),
    path('events/', views.events, name='events'),
     path('trades-view/', views.trade_view, name='trades_view'),
]