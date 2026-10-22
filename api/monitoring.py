
from .views import *
from .serializers import *
from rest_framework import generics
from .pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated
from .permissions import Is_Farmer,Is_Vet
from rest_framework.response import Response
from datetime import timedelta, date



@login_required
def heat_sign_monitoring(request):
    return render(request, 'portals/farmer/heat.html', {})

class HeatSignMonitoringCreate(generics.CreateAPIView):
    queryset = HeatSignMonitoring.objects.all()
    serializer_class = HeatSignMonitoringSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class HeatSignMonitoringList(generics.ListAPIView):
    serializer_class = HeatSignMonitoringSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        #print(user)
        return HeatSignMonitoring.objects.filter(user=user).order_by('-id')
    

class HeatSignMonitoringUpdate(generics.UpdateAPIView):
    queryset = HeatSignMonitoring.objects.all()
    serializer_class = HeatSignMonitoringSerializer
    permission_classes = [Is_Farmer]


class HeatSignMonitoringDelete(generics.DestroyAPIView):
    queryset = HeatSignMonitoring.objects.all()
    serializer_class = HeatSignMonitoringSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()



@login_required
def pregnancy_monitoring(request):
    return render(request, 'portals/farmer/pregnancy.html', {})

class PregnancyMonitoringCreate(generics.CreateAPIView):
    queryset = PregnancyMonitoring.objects.all()
    serializer_class = PregnancyMonitoringSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PregnancyMonitoringList(generics.ListAPIView):
    serializer_class = PregnancyMonitoringSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        #print(user)
        return PregnancyMonitoring.objects.filter(user=user).order_by('-id')
    

class PregnancyMonitoringUpdate(generics.UpdateAPIView):
    queryset = PregnancyMonitoring.objects.all()
    serializer_class = PregnancyMonitoringSerializer
    permission_classes = [Is_Farmer]


class PregnancyMonitoringDelete(generics.DestroyAPIView):
    queryset = PregnancyMonitoring.objects.all()
    serializer_class = PregnancyMonitoringSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()



# feeds
@login_required
def feeds(request):
    return render(request, 'portals/farmer/feeds.html', {})


class FeedsCreate(generics.CreateAPIView):
    queryset = Feeds.objects.all()
    serializer_class = FeedsSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FeedsList(generics.ListAPIView):
    serializer_class = FeedsSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        #print(user)
        return Feeds.objects.filter(user=user).order_by('-id')
    

class FeedsUpdate(generics.UpdateAPIView):
    queryset = Feeds.objects.all()
    serializer_class = FeedsSerializer
    permission_classes = [Is_Farmer]


class FeedsDelete(generics.DestroyAPIView):
    queryset = Feeds.objects.all()
    serializer_class = FeedsSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()




def add_gestation(request):
    if request.method == 'POST':
        gestation_date=request.post.GET('reci')
        print(form.errors)
        if form.is_valid():
            form.save()
            return redirect('gestation')
    else:
        form = GestationForm()
    return render(request, 'add_gestation.html', {'form': form})

def gestation_detail(request):
    gestation_monitoring = GestationMonitoring.objects.latest('id')
    data = serialize('json', [gestation_monitoring])
    return JsonResponse(data, safe=False)
def gestation(request):
    return render(request, 'portals/farmer/gestation.html')