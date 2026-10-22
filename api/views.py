import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import io
import math
 
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect
from users.models import *

import requests
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test,login_required
from rest_framework.decorators import api_view, permission_classes
from .models import *
from django.views import View
from django.utils import timezone
from django.core.serializers import serialize
from django.http import FileResponse
from fpdf import FPDF
from django.db.models import Q, F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.views import View
import json
from asgiref.sync import sync_to_async
import base64
from django.shortcuts import get_object_or_404
from django.urls import reverse, NoReverseMatch
from .monitoring import *
from io import BytesIO
from .serializers import *
from rest_framework import generics,parsers
from .pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated
from .permissions import *
from rest_framework.response import Response
from django.db.models import OuterRef, Subquery
from datetime import timedelta,time,datetime
from rest_framework.exceptions import ValidationError
from django.core.exceptions import MultipleObjectsReturned
import logging
from django.db import transaction
from rest_framework import generics,status
from django.http import FileResponse, Http404
from django.http import FileResponse, HttpResponseNotFound
import cv2
import numpy as np
from django.conf import settings
from django.templatetags.static import static
from django.utils.timezone import now
from  .credentials import *
from .token import *
from rest_framework.pagination import PageNumberPagination
from django.db.models import Exists, OuterRef, Value, BooleanField
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import re
from urllib.parse import unquote
from rest_framework import viewsets
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework import parsers

from decimal import Decimal, InvalidOperation
from datetime import timedelta
from urllib.parse import urlencode
import base64

import requests
from django.core import signing
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response




logger = logging.getLogger(__name__)
def is_admin_user(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_admin", False):
        return True
    role = getattr(getattr(user, "role", None), "role_name", "") or ""
    return "admin" in role.lower()


def has_lesson_access(user, lesson_id):
    """Admins always have access; everyone else needs a LessonPurchase."""
    if is_admin_user(user):
        return True
    return LessonPurchase.objects.filter(user=user, lesson_id=lesson_id).exists()
# ── JSON helpers (added by convert_to_json.py) ─────────────────────────────
from functools import wraps

# Never send these model fields to the browser.
SENSITIVE_FIELDS = {
    "password", "last_login", "is_superuser", "is_staff",
    "groups", "user_permissions",
}


def safe_values(queryset, exclude=()):
    """queryset -> list of dicts, skipping password-ish and `exclude` fields."""
    skip = SENSITIVE_FIELDS | set(exclude)
    names = [f.name for f in queryset.model._meta.concrete_fields if f.name not in skip]
    return list(queryset.values(*names))


def json_login_required(view_func):
    """Like @login_required, but answers 401 JSON instead of redirecting to a login page."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def vet_check(user):
    if not user.is_authenticated:
        return False  
    return getattr(user, 'is_vet_officer', False)
def agrovet_check(user):
    if not user.is_authenticated:
        return False  
    return getattr(user, 'is_agrovet', False)

def farmer_check(user):
    if not user.is_authenticated:
        return False  
    return getattr(user, 'is_farmer', False)
def official_check(user):
    if not user.is_authenticated:
        return False
    return user.is_official
def cooperative_check(user):
    if not user.is_authenticated:
        return False
    return user.is_cooperative

def slaughterhouse_check(user):
    if not user.is_authenticated:
        return False
    return user.is_slaughterhouse


def csrf_failure(request, reason=""):
    return JsonResponse({"error": "CSRF verification failed", "reason": reason}, status=403)


@user_passes_test(vet_check, login_url='vet-login')
def portal_vet(request):
    return JsonResponse({
        "all_vets": safe_values(Vet_Officer.objects.all()),
        "role": "vet",
    })


@user_passes_test(cooperative_check, login_url='cooperative-login')
def cooperative(request):
    return JsonResponse({
        "all_coops": safe_values(DairyCooperative.objects.all()),
        "role": "cooperative",
    })


@user_passes_test(official_check, login_url='official-login')
def portal_official(request):
    return JsonResponse({
        "all_officers": safe_values(Official.objects.all()),
        "role": "officer",
    })


    
@user_passes_test(slaughterhouse_check, login_url='slaughterhouse-login')
def portal_slaughterhouse(request):
    return JsonResponse({
        "all_animals": safe_values(SlaughterHouse.objects.all()),
        "role": "slaughterhouse",
    })


      

@user_passes_test(farmer_check, login_url='farmer-login')
def vet_list(request):
    return JsonResponse({"all_vets": safe_values(Vet_Officer.objects.all())})


@user_passes_test(vet_check, login_url='vet-login')
def vet_list_vet(request):
    return JsonResponse({"all_vets": safe_values(Vet_Officer.objects.all())})


    

@user_passes_test(farmer_check, login_url='farmer-login')
def portal_farmer(request):
    return JsonResponse({
        "all_vets": safe_values(Vet_Officer.objects.all()),
        "role": "farmer",
    })


@user_passes_test(agrovet_check, login_url='agrovet-login')
def agrovet(request):
    return JsonResponse({
        "all_vets": safe_values(Agrovet.objects.all()),
        "role": "agrovet",
    })
class IsAdminOnly(IsAuthenticated):
    """Admins only, for reads as well (salary data is sensitive)."""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and IsAdminUserCustom._check_admin(request.user)


class IsAdminUserCustom(IsAuthenticated):
    """Allow read to any authenticated user; write only to admins."""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return self._check_admin(request.user)

    @staticmethod
    def _check_admin(user):
        if getattr(user, 'is_admin', False):
            return True
        try:
            return 'admin' in (user.role.role_name or '').lower()
        except Exception:
            return False

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('role')
    serializer_class = UserBasicSerializer
    permission_classes = [IsAdminUserCustom]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'firstname', 'lastname', 'email']
    filterset_fields = ['role', 'is_active']
    ordering_fields = ['username', 'date_joined']
    ordering = ['-date_joined']

    def create(self, request, *args, **kwargs):
        from users.models import Roles

        data = request.data
        try:
            user = User(
                username=str(data.get('username', '')).lower(),
                firstname=data.get('firstname', ''),
                lastname=data.get('lastname', ''),
                email=data.get('email', ''),
                phone=data.get('phone') or '',
                address=data.get('address') or 'N/A',
                can_login=True,
                is_admin=False,
                offdays={},
            )
            user.set_password(data.get('password') or str(data.get('username', '')).lower())
            role_id = data.get('role')
            if role_id:
                user.role = Roles.objects.get(pk=role_id)
            user.save()

            from users.models import ActivityLog
            ActivityLog.log('user_created', user=request.user, entity='User', entity_id=user.id,
                            detail=f'Created user {user.username}', request=request)
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        from users.models import Roles
        partial = kwargs.pop('partial', False)
        user = self.get_object()
        data = request.data
        for field in ('firstname', 'lastname', 'email', 'phone', 'address'):
            if field in data:
                setattr(user, field, data[field])
        if 'role' in data:
            user.role = Roles.objects.get(pk=data['role'])
        if 'is_active' in data:
            user.is_active = data['is_active']
        if data.get('password'):
            user.set_password(data['password'])
        user.save()
        from users.models import ActivityLog
        ActivityLog.log('user_updated', user=request.user, entity='User', entity_id=user.id,
                        detail=f'Updated user {user.username}', request=request)
        return Response(self.get_serializer(user).data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        from users.models import ActivityLog
        ActivityLog.log('user_deleted', user=request.user, entity='User', entity_id=user.id,
                        detail=f'Deleted user {user.username}', request=request)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            return Response(self.get_serializer(request.user).data)
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def _is_admin(self, user):
        return IsAdminUserCustom._check_admin(user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reset_password(self, request, pk=None):
        if not self._is_admin(request.user):
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object()
        new_password = request.data.get('password') or user.username
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successfully'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_status(self, request, pk=None):
        if not self._is_admin(request.user):
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({'is_active': user.is_active, 'message': f'User {"enabled" if user.is_active else "disabled"}'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def form_data(self, request):
        from users.models import Roles
        roles = Roles.objects.all().values('id', 'role_name', 'role_description')
        return Response({'roles': list(roles)})
class SurgicalRecordCreate(generics.CreateAPIView):
    queryset = SurgicalRecord.objects.all()
    serializer_class = SurgicalRecordSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SurgicalRecordList(generics.ListAPIView):
    serializer_class = SurgicalRecordSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return SurgicalRecord.objects.filter(user=user)
        
        elif user.is_farmer:
            
            return SurgicalRecord.objects.filter(assigned_to=user)

        return SurgicalRecord.objects.none()

    
class SurgicalRecordUpdate(generics.UpdateAPIView):
    queryset = SurgicalRecord.objects.all()
    serializer_class = SurgicalRecordSerializer
    permission_classes = [Is_Vet]

class SurgicalRecordDelete(generics.DestroyAPIView):
    queryset = SurgicalRecord.objects.all()
    serializer_class = SurgicalRecordSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def receipt_filter(request):
    try:
        user = request.user

        if getattr(user, 'is_vet_officer', False):
            queryset = VeterinaryBilling.objects.filter(user=user)
            user_type = "vet_officer"
        elif getattr(user, 'is_official', False):
            queryset = VeterinaryBilling.objects.filter(assigned_to=user)
            user_type = "official"
        else:
            return Response(
                {"error": "You do not have access to these records."},
                status=403
            )

        records = queryset.annotate(
            assigned_to_username=F("assigned_to__username"),
            user_username=F("user__username")
        ).values(
            "id",
            "agreed_date",
            "billing_category",
            "total_amount_billed",
            "total_paid",
            "balance",
            "farmer_name",
            "assigned_to_username",
            "user_username"
        )

        totals = queryset.aggregate(
            total_billed=Sum('total_amount_billed'),
            total_paid_sum=Sum('total_paid'),
            total_balance=Sum('balance')
        )

        return Response({
            "user_type": user_type,
            "records": list(records),
            "sum_total_billed": totals['total_billed'] or 0,
            "sum_total_paid": totals['total_paid_sum'] or 0,
            "sum_balance": totals['total_balance'] or 0,
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )

class VeterinaryBillingCreate(generics.CreateAPIView):
    queryset = VeterinaryBilling.objects.all()
    serializer_class = VeterinaryBillingSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        # Add any custom behavior here if needed
        serializer.save(user=self.request.user)

class VeterinaryBillingList(generics.ListAPIView):
    serializer_class = VeterinaryBillingSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination  # Assuming you have a custom pagination class

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return VeterinaryBilling.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return VeterinaryBilling.objects.filter(assigned_to=user).order_by('-id')

        return VeterinaryBilling.objects.none()
class VeterinaryBillingUpdate(generics.UpdateAPIView):
    queryset = VeterinaryBilling.objects.all()
    serializer_class = VeterinaryBillingSerializer
    permission_classes = [Is_Vet]

class VeterinaryBillingDelete(generics.DestroyAPIView):
    queryset = VeterinaryBilling.objects.all()
    serializer_class = VeterinaryBillingSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Deworming Views
class DewormingCreate(generics.CreateAPIView):
    queryset = Deworming.objects.all()
    serializer_class = DewormingSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DewormingList(generics.ListAPIView):
    serializer_class = DewormingSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
            user = self.request.user

            if user.is_vet_officer:
            
                return Deworming.objects.filter(user=user).order_by('-id')
            
            elif user.is_farmer:
                
                return Deworming.objects.filter(assigned_to=user).order_by('-id')

            return Deworming.objects.none()
class DewormingUpdate(generics.UpdateAPIView):
    queryset = Deworming.objects.all()
    serializer_class = DewormingSerializer
    permission_classes = [Is_Vet]

class DewormingDelete(generics.DestroyAPIView):
    queryset = Deworming.objects.all()
    serializer_class = DewormingSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# ArtificialInsemination Views


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def ai_record_filter(request):
    try:
        user = request.user

        # 🧑‍⚕️ If vet officer: show records they assigned
        if getattr(user, 'is_vet_officer', False):
            records = ArtificialInsemination.objects.filter(
                assigned_by=user
            ).annotate(
                assigned_to_username=F("assigned_to_official__username")
            ).values(
                "id", "insemination_date", "species", "assigned_to_username"
            )
            return Response({
                "user_type": "vet_officer",
                "records": list(records),
            })

        # 🏛️ If official: show records assigned to them
        elif getattr(user, 'is_official', False):
            records = ArtificialInsemination.objects.filter(
                assigned_to_official=user
            ).annotate(
                assigned_by_username=F("assigned_by__username")
            ).values(
                "id", "insemination_date", "species", "assigned_by_username"
            )
            return Response({
                "user_type": "official",
                "records": list(records),
            })

        return Response({"error": "You do not have access to these records."}, status=403)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

class ArtificialInseminationCreate(generics.CreateAPIView):
    queryset = ArtificialInsemination.objects.all()
    serializer_class = ArtificialInseminationSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
            user = self.request.user
            logger.info(f"Received Data: {self.request.data}")  # Log request data
            serializer.save(user=user)


class ArtificialInseminationList(generics.ListAPIView):
    serializer_class = ArtificialInseminationSerializer
    permission_classes = [Is_Vet | Is_Official | Is_Farmer | Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return ArtificialInsemination.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return ArtificialInsemination.objects.filter(assigned_to_official=user).order_by('-id')

        if user.is_farmer:
            return ArtificialInsemination.objects.filter(assigned_to=user).order_by('-id')
        
        if user.is_cooperative:
            return ArtificialInsemination.objects.filter(assigned_to_cooperative=user).order_by('-id')


        return ArtificialInsemination.objects.none()
class ArtificialInseminationUpdate(generics.UpdateAPIView):
    queryset = ArtificialInsemination.objects.all()
    serializer_class = ArtificialInseminationSerializer
    permission_classes = [Is_Vet]

class ArtificialInseminationDelete(generics.DestroyAPIView):
    queryset = ArtificialInsemination.objects.all()
    serializer_class = ArtificialInseminationSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# PregnancyDiagnosis Views


class PregnancyDiagnosisCreate(generics.CreateAPIView):
    queryset = PregnancyDiagnosis.objects.all()
    serializer_class = PregnancyDiagnosisSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PregnancyDiagnosisList(generics.ListAPIView):
    serializer_class = PregnancyDiagnosisSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return PregnancyDiagnosis.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return PregnancyDiagnosis.objects.filter(assigned_to=user).order_by('-id')

        return PregnancyDiagnosis.objects.none()
    
class PregnancyDiagnosisUpdate(generics.UpdateAPIView):
    queryset = PregnancyDiagnosis.objects.all()
    serializer_class = PregnancyDiagnosisSerializer
    permission_classes = [Is_Vet]

class PregnancyDiagnosisDelete(generics.DestroyAPIView):
    queryset = PregnancyDiagnosis.objects.all()
    serializer_class = PregnancyDiagnosisSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# FarmConsultation Views


class FarmConsultationCreate(generics.CreateAPIView):
    queryset = FarmConsultation.objects.all()
    serializer_class = FarmConsultationSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FarmConsultationList(generics.ListAPIView):
    serializer_class = FarmConsultationSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return FarmConsultation.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return FarmConsultation.objects.filter(assigned_to=user).order_by('-id')

        return FarmConsultation.objects.none()
    
class FarmConsultationUpdate(generics.UpdateAPIView):
    queryset = FarmConsultation.objects.all()
    serializer_class = FarmConsultationSerializer
    permission_classes = [Is_Vet]

class FarmConsultationDelete(generics.DestroyAPIView):
    queryset = FarmConsultation.objects.all()
    serializer_class = FarmConsultationSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Referral Views
class ReferralCreate(generics.CreateAPIView):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReferralList(generics.ListAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return Referral.objects.filter(user=user)
        
        elif user.is_farmer:
            
            return Referral.objects.filter(assigned_to=user)

        return Referral.objects.none()
class ReferralUpdate(generics.UpdateAPIView):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [Is_Vet]

class ReferralDelete(generics.DestroyAPIView):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


# Define views

class CalfCreate(generics.CreateAPIView):
    queryset = Calf.objects.all()
    serializer_class = CalfSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
            registration_number = self.request.data.get('registration_number')
            user = self.request.user

            # Check if the employee exists
            if Calf.objects.filter(user=user, registration_number=registration_number).exists():
                raise ValidationError(f"Calf with Registration '{registration_number}' already exists!")

            serializer.save(user=user)

class CalfList(generics.ListAPIView):
    serializer_class = CalfSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return Calf.objects.filter(user=self.request.user).order_by('-id')
    

class CalfUpdate(generics.UpdateAPIView):
    queryset = Calf.objects.all()
    serializer_class = CalfSerializer
    permission_classes = [Is_Farmer]


class CalfDelete(generics.DestroyAPIView):
    queryset = Calf.objects.all()
    serializer_class = CalfSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class DeadAnimalCreate(generics.CreateAPIView):
    queryset = DeadAnimal.objects.all()
    serializer_class = DeadAnimalSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DeadAnimalList(generics.ListAPIView):
    serializer_class = DeadAnimalSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return DeadAnimal.objects.filter(user=self.request.user).order_by('-id')
    

class DeadAnimalUpdate(generics.UpdateAPIView):
    queryset = DeadAnimal.objects.all()
    serializer_class = DeadAnimalSerializer
    permission_classes = [Is_Farmer]


class DeadAnimalDelete(generics.DestroyAPIView):
    queryset = DeadAnimal.objects.all()
    serializer_class = DeadAnimalSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

###Culling

class CullingCreate(generics.CreateAPIView):
    queryset = Culling.objects.all()
    serializer_class = CullingSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CullingList(generics.ListAPIView):
    serializer_class = CullingSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return Culling.objects.filter(user=self.request.user).order_by('-id')
    

class CullingUpdate(generics.UpdateAPIView):
    queryset = Culling.objects.all()
    serializer_class = CullingSerializer
    permission_classes = [Is_Farmer]


class CullingDelete(generics.DestroyAPIView):
    queryset = Culling.objects.all()
    serializer_class = CullingSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# livestock inventory
class LivestockCreate(generics.CreateAPIView):
    queryset = Livestock.objects.all()
    serializer_class = LivestockSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LivestockList(generics.ListAPIView):
    serializer_class = LivestockSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return Livestock.objects.filter(user=self.request.user).order_by('-id')
    

class LivestockUpdate(generics.UpdateAPIView):
    queryset = Livestock.objects.all()
    serializer_class = LivestockSerializer
    permission_classes = [Is_Farmer]


class LivestockDelete(generics.DestroyAPIView):
    queryset = Livestock.objects.all()
    serializer_class = LivestockSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

##new animal
class NewAnimalCreate(generics.CreateAPIView):
    queryset = NewAnimal.objects.all()
    serializer_class = NewAnimalSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
            reg_no = self.request.data.get('reg_no')
            user = self.request.user

            # Check if the employee exists
            if NewAnimal.objects.filter(user=user, reg_no=reg_no).exists():
                raise ValidationError(f"Animal With with Registration '{reg_no}' already exists!")

            serializer.save(user=user)
class NewAnimalList(generics.ListAPIView):
    serializer_class = NewAnimalSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return NewAnimal.objects.filter(user=self.request.user).order_by('-id')
    

class NewAnimalUpdate(generics.UpdateAPIView):
    queryset = NewAnimal.objects.all()
    serializer_class = NewAnimalSerializer
    permission_classes = [Is_Farmer]


class NewAnimalDelete(generics.DestroyAPIView):
    queryset = NewAnimal.objects.all()
    serializer_class = NewAnimalSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

##############################

class AnimalSaleCreate(generics.CreateAPIView):
    queryset = AnimalSale.objects.all()
    serializer_class = AnimalSaleSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AnimalSaleList(generics.ListAPIView):
    serializer_class = AnimalSaleSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return AnimalSale.objects.filter(user=self.request.user).order_by('-id')
    

class AnimalSaleUpdate(generics.UpdateAPIView):
    queryset = AnimalSale.objects.all()
    serializer_class = AnimalSaleSerializer
    permission_classes = [Is_Farmer]


class AnimalSaleDelete(generics.DestroyAPIView):
    queryset = AnimalSale.objects.all()
    serializer_class = AnimalSaleSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class MineralsCreate(generics.CreateAPIView):
    queryset = Minerals.objects.all()
    serializer_class = MineralsSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class MineralsList(generics.ListAPIView):
    serializer_class = MineralsSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return Minerals.objects.filter(user=user).order_by('-id')

class MineralsUpdate(generics.UpdateAPIView):
    queryset = Minerals.objects.all()
    serializer_class = MineralsSerializer
    permission_classes = [Is_Farmer]

class MineralsDelete(generics.DestroyAPIView):
    queryset = Minerals.objects.all()
    serializer_class = MineralsSerializer
    permission_classes = [Is_Farmer]
    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()  
class VeterinaryBillsCreate(generics.CreateAPIView):
    queryset = VeterinaryBills.objects.all()
    serializer_class = VeterinaryBillsSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VeterinaryBillsList(generics.ListAPIView):
    serializer_class = VeterinaryBillsSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # If you have a custom pagination class

    def get_queryset(self):
        user = self.request.user
        return VeterinaryBills.objects.filter(user=user).order_by('-id')

class VeterinaryBillsUpdate(generics.UpdateAPIView):
    queryset = VeterinaryBills.objects.all()
    serializer_class = VeterinaryBillsSerializer
    permission_classes = [Is_Farmer]

class VeterinaryBillsDelete(generics.DestroyAPIView):
    queryset = VeterinaryBills.objects.all()
    serializer_class = VeterinaryBillsSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class DailyCheckCreate(generics.CreateAPIView):
    queryset = DailyCheck.objects.all()
    serializer_class = DailyCheckSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DailyCheckList(generics.ListAPIView):
    serializer_class = DailyCheckSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        return DailyCheck.objects.filter(user=self.request.user).order_by('-id')

class DailyCheckUpdate(generics.UpdateAPIView):
    queryset = DailyCheck.objects.all()
    serializer_class = DailyCheckSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return DailyCheck.objects.filter(user=self.request.user)

class DailyCheckDelete(generics.DestroyAPIView):
    queryset = DailyCheck.objects.all()
    serializer_class = DailyCheckSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return DailyCheck.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()

         
class OtherExpenseCreate(generics.CreateAPIView):
    queryset = OtherExpense.objects.all()
    serializer_class = OtherExpenseSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OtherExpenseList(generics.ListAPIView):
    serializer_class = OtherExpenseSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # Optional

    def get_queryset(self):
        return OtherExpense.objects.filter(user=self.request.user).order_by('-id')


class OtherExpenseUpdate(generics.UpdateAPIView):
    queryset = OtherExpense.objects.all()
    serializer_class = OtherExpenseSerializer
    permission_classes = [Is_Farmer]


class OtherExpenseDelete(generics.DestroyAPIView):
    queryset = OtherExpense.objects.all()
    serializer_class = OtherExpenseSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
@user_passes_test(farmer_check, login_url='farmer-login')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expenses(request):
    user = request.user

    vet_bills = VeterinaryBills.objects.filter(user=user).values('id', 'date_of_billing', 'amount')
    archaricides = Archaricides.objects.filter(user=user).values('id', 'date_of_purchase', 'cost')
    hygiene = DairyHygiene.objects.filter(user=user).values('id', 'date_of_purchase', 'cost')
    salaries = Salaries.objects.filter(user=user).values('id', 'payment_date', 'amount')
    feeds = Feeds.objects.filter(user=user).values('id', 'date_of_purchase', 'cost')
    equipment = DairyEquipment.objects.filter(user=user).values('id', 'date_of_purchase', 'cost')
    drugs = VeterinaryDrugs.objects.filter(user=user).values('id', 'date_of_purchase', 'cost')
    minerals = Minerals.objects.filter(user=user).values('id', 'date_of_purchase', 'cost')
    insurance = LivestockInsurance.objects.filter(user=user).values('id', 'payment_date', 'total')
    calving=CalvingRecord.objects.filter(user=user).values('id','date_of_calving','calf_sex')
    other=OtherExpense.objects.filter(user=user).values('id','date','cost')

    vet_bills_total = VeterinaryBills.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
    archaricides_total = Archaricides.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    hygiene_total = DairyHygiene.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    salaries_total = Salaries.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0
    feeds_total = Feeds.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    equipment_total = DairyEquipment.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    drugs_total = VeterinaryDrugs.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    minerals_total = Minerals.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    insurance_total = LivestockInsurance.objects.filter(user=user).aggregate(Sum('total'))['total__sum'] or 0
    other_total = OtherExpense.objects.filter(user=user).aggregate(Sum('cost'))['cost__sum'] or 0
    

    total_for_all_expenses = (
        vet_bills_total + archaricides_total + hygiene_total + salaries_total +
        feeds_total + equipment_total + drugs_total + minerals_total + insurance_total + other_total
    )

    return Response({
        'vet_bills': list(vet_bills),
        'archaricides': list(archaricides),
        'hygiene': list(hygiene),
        'salaries': list(salaries),
        'feeds': list(feeds),
        'equipment': list(equipment),
        'drugs': list(drugs),
        'minerals': list(minerals),
        'insurance': list(insurance),
        'other': list(other),
        'calving':calving,
        'total_for_all_expenses': total_for_all_expenses,
    })

class ArcharicidesCreate(generics.CreateAPIView):
    queryset = Archaricides.objects.all()
    serializer_class = ArcharicidesSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ArcharicidesList(generics.ListAPIView):
    serializer_class = ArcharicidesSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # If you have a custom pagination class

    def get_queryset(self):
        user = self.request.user
        return Archaricides.objects.filter(user=user).order_by('-id')

class ArcharicidesUpdate(generics.UpdateAPIView):
    queryset = Archaricides.objects.all()
    serializer_class = ArcharicidesSerializer
    permission_classes = [Is_Farmer]

class ArcharicidesDelete(generics.DestroyAPIView):
    queryset = Archaricides.objects.all()
    serializer_class = ArcharicidesSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
class DairyEquipmentCreate(generics.CreateAPIView):
    queryset = DairyEquipment.objects.all()
    serializer_class = DairyEquipmentSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DairyEquipmentList(generics.ListAPIView):
    serializer_class = DairyEquipmentSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # If you have a custom pagination class

    def get_queryset(self):
        user = self.request.user
        return DairyEquipment.objects.filter(user=user).order_by('-id')

class DairyEquipmentUpdate(generics.UpdateAPIView):
    queryset = DairyEquipment.objects.all()
    serializer_class = DairyEquipmentSerializer
    permission_classes = [Is_Farmer]

class DairyEquipmentDelete(generics.DestroyAPIView):
    queryset = DairyEquipment.objects.all()
    serializer_class = DairyEquipmentSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
class DairyHygieneCreate(generics.CreateAPIView):
    queryset = DairyHygiene.objects.all()
    serializer_class = DairyHygieneSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DairyHygieneList(generics.ListAPIView):
    serializer_class = DairyHygieneSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # If you have a custom pagination class

    def get_queryset(self):
        user = self.request.user
        return DairyHygiene.objects.filter(user=user).order_by('-id')

class DairyHygieneUpdate(generics.UpdateAPIView):
    queryset = DairyHygiene.objects.all()
    serializer_class = DairyHygieneSerializer
    permission_classes = [Is_Farmer]

class DairyHygieneDelete(generics.DestroyAPIView):
    queryset = DairyHygiene.objects.all()
    ##print(queryset)
    serializer_class = DairyHygieneSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class SalariesCreate(generics.CreateAPIView):
    queryset = Salaries.objects.all()
    #print(queryset)
    serializer_class = SalariesSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
            identification = self.request.data.get('identification')
            user = self.request.user

            # Check if the employee exists
            if Salaries.objects.filter(user=user, identification=identification).exists():
                raise ValidationError(f"Employee with ID '{identification}' already exists!")

            serializer.save(user=user)

class SalariesList(generics.ListAPIView):
    serializer_class = SalariesSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination
    

    def get_queryset(self):
        user = self.request.user
        return Salaries.objects.filter(user=user).order_by('-id')

class SalariesUpdate(generics.UpdateAPIView):
    queryset = Salaries.objects.all()
    serializer_class = SalariesSerializer
    permission_classes = [Is_Farmer]

class SalariesDelete(generics.DestroyAPIView):
    queryset = Salaries.objects.all()
    serializer_class = SalariesSerializer
    permission_classes = [Is_Farmer]           

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
class LivestockInsuranceCreate(generics.CreateAPIView):
    queryset = LivestockInsurance.objects.all()
    serializer_class = LivestockInsuranceSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LivestockInsuranceList(generics.ListAPIView):
    serializer_class = LivestockInsuranceSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # If you have a custom pagination class

    def get_queryset(self):
        user = self.request.user
        return LivestockInsurance.objects.filter(user=user).order_by('-id')

class LivestockInsuranceUpdate(generics.UpdateAPIView):
    queryset = LivestockInsurance.objects.all()
    serializer_class = LivestockInsuranceSerializer
    permission_classes = [Is_Farmer]

class LivestockInsuranceDelete(generics.DestroyAPIView):
    queryset = LivestockInsurance.objects.all()
    serializer_class = LivestockInsuranceSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
class VeterinaryDrugsCreate(generics.CreateAPIView):
    queryset = VeterinaryDrugs.objects.all()
    serializer_class = VeterinaryDrugsSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VeterinaryDrugsList(generics.ListAPIView):
    serializer_class = VeterinaryDrugsSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination  # If you have a custom pagination class

    def get_queryset(self):
        user = self.request.user
        return VeterinaryDrugs.objects.filter(user=user).order_by('-id')

class VeterinaryDrugsUpdate(generics.UpdateAPIView):
    queryset = VeterinaryDrugs.objects.all()
    serializer_class = VeterinaryDrugsSerializer
    permission_classes = [Is_Farmer]

class VeterinaryDrugsDelete(generics.DestroyAPIView):
    queryset = VeterinaryDrugs.objects.all()
    serializer_class = VeterinaryDrugsSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
         


class EmployeesCreate(generics.CreateAPIView):
    queryset = Employees.objects.all()
    serializer_class = EmployeesSerializer
    permission_classes = [Is_Farmer]  

    def perform_create(self, serializer):
            id_no = self.request.data.get('id_no')
            user = self.request.user

            # Check if the employee exists
            if Employees.objects.filter(user=user, id_no=id_no).exists():
                raise ValidationError(f"Employee with ID '{id_no}' already exists!")

            serializer.save(user=user)

class EmployeesList(generics.ListAPIView):
    serializer_class = EmployeesSerializer
    permission_classes = [Is_Farmer]  
    pagination_class = CustomPagination  

    def get_queryset(self):
        user = self.request.user
        params = dict()
        if self.request.GET.get('id_no',False):
            
            params['id_no'] = self.request.GET.get('id_no')
            print(params)
        return Employees.objects.filter(user=user,**params).order_by('-id')
class EmployeesUpdate(generics.UpdateAPIView):
    queryset = Employees.objects.all()
    serializer_class = EmployeesSerializer
    permission_classes = [Is_Farmer] 

class EmployeesDelete(generics.DestroyAPIView):
    queryset = Employees.objects.all()
    serializer_class = EmployeesSerializer
    permission_classes = [Is_Farmer] 

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class LactatingCowCreate(generics.CreateAPIView):
    queryset = LactatingCow.objects.all()
    serializer_class = LactatingCowSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
            cow_name = self.request.data.get('cow_name')
            #print()
            user = self.request.user

            if LactatingCow.objects.filter(user=user, cow_name=cow_name).exists():
                raise ValidationError(f"Cow with Name '{cow_name}' already exists!")

            serializer.save(user=user)

class LactatingCowList(generics.ListAPIView):
    serializer_class = LactatingCowSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        params = dict()
        if self.request.GET.get('cow_name',False):
            params['cow_name'] = self.request.GET.get('cow_name')
        return LactatingCow.objects.filter(user=user,**params).order_by('-id')

class LactatingCowUpdate(generics.UpdateAPIView):
    queryset = LactatingCow.objects.all()
    serializer_class = LactatingCowSerializer
    permission_classes = [Is_Farmer]

class LactatingCowDelete(generics.DestroyAPIView):
    queryset = LactatingCow.objects.all()
    serializer_class = LactatingCowSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
@user_passes_test(farmer_check, login_url='farmer-login')
def milk_record(request):
    return JsonResponse({
        "employees": safe_values(EmployeeRecord.objects.filter(user=request.user)),
        "cows": safe_values(LactatingCow.objects.filter(user=request.user)),
    })


class FilteredMilkRecordsView(View):
    def get(self, request):
        user = request.user
        cow_id = request.GET.get('cow_id')
        period = request.GET.get('period', 'all')
        date_from = request.GET.get('from')
        date_to = request.GET.get('to')

        # Base filters
        filters = {'user': user}
        if cow_id and cow_id != 'all':
            filters['cow_name_id'] = cow_id

        # Choose the correct model and date field
        if period == 'daily':
            model = DailyMilkRecord
            date_field = 'date'
        elif period == 'weekly' or period == 'two_weeks':
            model = WeeklyMilkRecord
            date_field = 'week_start_date'
        elif period == 'monthly' or period == 'yearly':
            model = MonthlyMilkRecord
            date_field = 'month'
        else:
            model = MilkRecord
            date_field = 'date'

        if date_from and date_to:
            filters[f'{date_field}__range'] = (date_from, date_to)

        records = model.objects.filter(**filters).values()
        return JsonResponse(list(records), safe=False)
class MilkRecordCreate(generics.CreateAPIView):
    queryset = MilkRecord.objects.all()
    serializer_class = MilkRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MilkRecordList(generics.ListAPIView):
    serializer_class = MilkRecordSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return MilkRecord.objects.filter(user=user).order_by('-id')

class MilkRecordUpdate(generics.UpdateAPIView):
    queryset = MilkRecord.objects.all()
    serializer_class = MilkRecordSerializer
    permission_classes =[Is_Farmer]

class MilkRecordDelete(generics.DestroyAPIView):
    queryset = MilkRecord.objects.all()
    serializer_class = MilkRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class DailyMilkRecordList(generics.ListAPIView):
    serializer_class = DailyMilkRecordSerializer
    permission_classes = [ Is_Farmer]

    def get_queryset(self):
        user = self.request.user

        # Get the latest id for each cow_name for the authenticated user
        subquery = DailyMilkRecord.objects.filter(
            user=user,
            cow_name=OuterRef('cow_name')
        ).order_by('-id').values('id')[:1]

        latest_records = DailyMilkRecord.objects.filter(
            id__in=Subquery(subquery)
        ).order_by('-date')

        return latest_records
    
class DailyMilkRecordDelete(generics.DestroyAPIView):
    queryset = MilkRecord.objects.all()
    serializer_class = DailyMilkRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
class WeeklyMilkRecordListView(generics.ListAPIView):
    serializer_class = WeeklyMilkRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        user = self.request.user

        # Get the MilkRecord instances created by the user
        milk_record_queryset = MilkRecord.objects.filter(user=user)

        # Get the WeeklyMilkRecord instances that are related to the MilkRecord instances created by the user
        return WeeklyMilkRecord.objects.filter(
            cow_name__in=Subquery(milk_record_queryset.values('cow_name'))
        ).order_by('-week_start_date')
class WeeklyMilkRecordDelete(generics.DestroyAPIView):
    queryset = MilkRecord.objects.all()
    serializer_class = WeeklyMilkRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
class MonthlyMilkRecordListView(generics.ListAPIView):
    serializer_class = MonthlyMilkRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        user = self.request.user
        return MonthlyMilkRecord.objects.filter(user=user).order_by('-month')
    

class MonthlyMilkRecordDelete(generics.DestroyAPIView):
    queryset = MilkRecord.objects.all()
    serializer_class = MonthlyMilkRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class SalesOfMilkCreate(generics.CreateAPIView):
    queryset = SalesOfMilk.objects.all()
    serializer_class = SalesOfMilkSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SalesOfMilkList(generics.ListAPIView):
    serializer_class = SalesOfMilkSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return SalesOfMilk.objects.filter(user=user).order_by('-id')
    


class SalesOfMilkUpdate(generics.UpdateAPIView):
    queryset = SalesOfMilk.objects.all()
    serializer_class = SalesOfMilkSerializer
    permission_classes = [Is_Farmer]

class SalesOfMilkDelete(generics.DestroyAPIView):
    queryset = SalesOfMilk.objects.all()
    serializer_class = SalesOfMilkSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class PaymentsCreate(generics.CreateAPIView):
    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class PaymentsList(generics.ListAPIView):
    serializer_class = PaymentsSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Payments.objects.filter(user=self.request.user).order_by('-id')
    
class PaymentsUpdate(generics.UpdateAPIView):
    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    permission_classes = [Is_Farmer]
    
class PaymentsDelete(generics.DestroyAPIView):
    queryset = Payments.objects.all()
    serializer_class = PaymentsSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class BuyerCreate(generics.CreateAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [Is_Farmer]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BuyerList(generics.ListAPIView):
    serializer_class = BuyerSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Buyer.objects.filter(user=self.request.user).order_by('-id')
    
@api_view(['GET'])
@permission_classes([Is_Farmer])
def get_buyers_by_category(request):
    category = request.GET.get('category')
    if category:
        buyers = Buyer.objects.filter(category=category, user=request.user)
    else:
        buyers = Buyer.objects.none()

    serializer = BuyerSerializer(buyers, many=True)
    return Response(serializer.data)

def buyers_by_category(request):
    category = request.GET.get('category')
    if category:
        buyers = Buyer.objects.filter(category=category)
        data = [{'id': b.id, 'name': b.name, 'category': b.category} for b in buyers]
    else:
        data = []
    return JsonResponse(data, safe=False)


class BuyerUpdate(generics.UpdateAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [Is_Farmer]


class BuyerDelete(generics.DestroyAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [Is_Farmer]


class LaboratoryRecordCreate(generics.CreateAPIView):
    queryset = LaboratoryRecord.objects.all()
    serializer_class = LaboratoryRecordSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LaboratoryRecordList(generics.ListAPIView):
    serializer_class = LaboratoryRecordSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return LaboratoryRecord.objects.filter(user=user)
        
        elif user.is_farmer:
            
            return LaboratoryRecord.objects.filter(assigned_to=user)

        return LaboratoryRecord.objects.none()
    
class LaboratoryRecordUpdate(generics.UpdateAPIView):
    queryset = LaboratoryRecord.objects.all()
    serializer_class = LaboratoryRecordSerializer
    permission_classes = [Is_Vet]

class LaboratoryRecordDelete(generics.DestroyAPIView):
    queryset = LaboratoryRecord.objects.all()
    serializer_class = LaboratoryRecordSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


    
    
class LivestockIncidentCreate(generics.CreateAPIView):
    queryset = LivestockIncident.objects.all()
    serializer_class = LivestockIncidentSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LivestockIncidentList(generics.ListAPIView):
    serializer_class = LivestockIncidentSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return LivestockIncident.objects.filter(user=user)
        
        elif user.is_farmer:
            
            return LivestockIncident.objects.filter(assigned_to=user)

        return LivestockIncident.objects.none()
class LivestockIncidentUpdate(generics.UpdateAPIView):
    queryset = LivestockIncident.objects.all()
    serializer_class = LivestockIncidentSerializer
    permission_classes = [Is_Vet]

class LivestockIncidentDelete(generics.DestroyAPIView):
    queryset = LivestockIncident.objects.all()
    serializer_class = LivestockIncidentSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class SampleCollectionCreate(generics.CreateAPIView):
    queryset = SampleCollection.objects.all()
    serializer_class = SampleCollectionSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SampleCollectionList(generics.ListAPIView):
    serializer_class = SampleCollectionSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return SampleCollection.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return SampleCollection.objects.filter(assigned_to=user).order_by('-id')

        return SampleCollection.objects.none()
    
class SampleCollectionUpdate(generics.UpdateAPIView):
    queryset = SampleCollection.objects.all()
    serializer_class = SampleCollectionSerializer
    permission_classes = [Is_Vet]

class SampleCollectionDelete(generics.DestroyAPIView):
    queryset = SampleCollection.objects.all()
    serializer_class = SampleCollectionSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
class SampleProcessingCreate(generics.CreateAPIView):
    queryset = SampleProcessing.objects.all()
    serializer_class = SampleProcessingSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SampleProcessingList(generics.ListAPIView):
    serializer_class = SampleProcessingSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return SampleProcessing.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return SampleProcessing.objects.filter(assigned_to=user).order_by('-id')

        return SampleProcessing.objects.none()
    
class SampleProcessingUpdate(generics.UpdateAPIView):
    queryset = SampleProcessing.objects.all()
    serializer_class = SampleProcessingSerializer
    permission_classes = [Is_Vet]

class SampleProcessingDelete(generics.DestroyAPIView):
    queryset = SampleProcessing.objects.all()
    serializer_class = SampleProcessingSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class PostMortemRecordCreate(generics.CreateAPIView):
    queryset = PostMortemRecord.objects.all()
    serializer_class = PostMortemRecordSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PostMortemRecordList(generics.ListAPIView):
    serializer_class = PostMortemRecordSerializer
    permission_classes = [Is_Vet|Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return PostMortemRecord.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return PostMortemRecord.objects.filter(assigned_to=user)

        return PostMortemRecord.objects.none()
    
class PostMortemRecordgUpdate(generics.UpdateAPIView):
    queryset = PostMortemRecord.objects.all()
    serializer_class = PostMortemRecordSerializer
    permission_classes = [Is_Vet]

class PostMortemRecordDelete(generics.DestroyAPIView):
    queryset = PostMortemRecord.objects.all()
    serializer_class = PostMortemRecordSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def vaccination_record_filter(request):
    try:
        user = request.user

        # 🧑‍⚕️ If vet officer: show records they assigned
        if getattr(user, 'is_vet_officer', False):
            records = VaccinationRecord.objects.filter(
                assigned_by=user
            ).annotate(
                assigned_to_username=F("assigned_to_official__username")
            ).values(
                "id",
                "date_of_vaccination",
                "species_targeted",
                "vaccination_of",
                "number_of_animals_vaccinated",
                "assigned_to_username"
            )

            return Response({
                "user_type": "vet_officer",
                "records": list(records),
            })

        # 🏛️ If official: show records assigned to them
        elif getattr(user, 'is_official', False):
            records = VaccinationRecord.objects.filter(
                assigned_to_official=user
            ).annotate(
                assigned_by_username=F("assigned_by__username")
            ).values(
                "id",
                "date_of_vaccination",
                "species_targeted",
                "vaccination_of",
                "number_of_animals_vaccinated",
                "assigned_by_username"
            )

            return Response({
                "user_type": "official",
                "records": list(records),
            })

        return Response(
            {"error": "You do not have access to these records."},
            status=403
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )
CERT_DIR = "vaccination_certificates"   # sub-folder inside MEDIA_ROOT
 
 
#
# Constants
CERT_DIR = "vaccination_certificates"
GOLD = colors.HexColor("#CFB53B")
DARK_GOLD = colors.HexColor("#8B6914")
NAVY = colors.HexColor("#1a237e")


# ──────────────────────────────────────────────────────────────────────────────
#  Helper functions (modified to be async-friendly)
# ──────────────────────────────────────────────────────────────────────────────

def save_certificate_to_media(record, pdf_bytes: bytes) -> str:
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

    path = (
        f"{CERT_DIR}/{record.pk}_certificate_{timestamp}.pdf"
    )

    saved_path = default_storage.save(path, ContentFile(pdf_bytes))
    return saved_path


def certificate_url(saved_path: str) -> str:
    return default_storage.url(saved_path)

# ──────────────────────────────────────────────────────────────────────────────
#  Drawing primitives (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

def _decorative_border(c, x, y, w, h):
    c.setStrokeColor(colors.black); c.setLineWidth(6)
    c.rect(x, y, w, h, fill=0, stroke=1)
    c.setStrokeColor(GOLD); c.setLineWidth(4)
    c.rect(x + 5, y + 5, w - 10, h - 10, fill=0, stroke=1)
    c.setStrokeColor(colors.white); c.setLineWidth(1.5)
    c.rect(x + 10, y + 10, w - 20, h - 20, fill=0, stroke=1)
    for (cx, cy) in [(x, y + h), (x + w, y + h), (x, y), (x + w, y)]:
        c.setFillColor(GOLD); c.circle(cx, cy, 4, fill=1, stroke=0)


def _logo_circle(c, cx, cy, r=20):
    c.setFillColor(colors.white); c.setStrokeColor(DARK_GOLD); c.setLineWidth(1.5)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(DARK_GOLD); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(cx, cy + 4, "VET")
    c.drawCentredString(cx, cy - 4, "PROF")


def _gold_seal(c, cx, cy, r=26):
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    for i in range(16):
        a = math.radians(i * 22.5)
        c.line(cx + (r - 4) * math.cos(a), cy + (r - 4) * math.sin(a),
               cx + (r + 6) * math.cos(a), cy + (r + 6) * math.sin(a))
    c.setFillColor(GOLD); c.setStrokeColor(DARK_GOLD); c.setLineWidth(1.5)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(DARK_GOLD); c.circle(cx, cy, r * 0.7, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 5)
    c.drawCentredString(cx, cy + 4, "VET PRO")
    c.drawCentredString(cx, cy - 2, "SERVICES")


def _table_row(c, x, y, col_w, values, row_h=14, header=False):
    n = len(values)
    tw = col_w * n
    c.setFillColor(NAVY if header else colors.HexColor("#f5f5f5"))
    c.rect(x, y - row_h, tw, row_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.rect(x, y - row_h, tw, row_h, fill=0, stroke=1)
    for i in range(1, n):
        c.line(x + i * col_w, y, x + i * col_w, y - row_h)
    c.setFont("Helvetica-Bold" if header else "Helvetica", 9)
    c.setFillColor(colors.white if header else colors.black)
    for i, val in enumerate(values):
        c.drawString(x + i * col_w + 3, y - row_h + 5, str(val or "")[:20])


# ──────────────────────────────────────────────────────────────────────────────
#  Main PDF builder (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def generate_vaccination_certificate(record) -> bytes:
    """
    Build a Veterinary Professional Services Vaccination Certificate PDF
    styled to match the reference design (gold/navy/black border, seal, tables).
    Returns raw PDF bytes.
    """
    MRG = 18
    TOP_PAD = 24      # <<< CHANGE ME: extra blank space above the business name. Increase to push title down.
    BOTTOM_PAD = 26   # <<< CHANGE ME: extra blank space below content, controls how close the footer sits to the bottom border. Increase to push footer further up; decrease to move it closer to the bottom edge.
    ROW = 18
    TBL = 18
    TBL_H = 16
    FS  = 11
    LBL = ("Helvetica-Bold", FS)
    VAL = ("Helvetica",      FS)

    page_w = A4[0]

    content_h = 0
    content_h += TOP_PAD        # <<< added: top margin above business name
    content_h += 20
    content_h += 16
    content_h += 28
    content_h += 38 - 28
    content_h += 12
    content_h += ROW
    content_h += ROW * 3
    content_h += ROW + 4
    content_h += 8
    content_h += TBL_H
    content_h += TBL
    content_h += 16
    content_h += ROW + 4
    content_h += 8
    content_h += TBL_H
    content_h += TBL
    content_h += ROW
    content_h += ROW * 4.5  # <-- INCREASED: Allocated extra canvas room so the stamp spacing doesn't clip the footer
    content_h += ROW
    content_h += ROW
    content_h += ROW
    content_h += ROW
    content_h += 2
    content_h += BOTTOM_PAD     # <<< added: bottom margin/space before footer

    page_h = content_h + 2 * MRG

    IL = MRG + 14
    IR = page_w - MRG - 14

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))

    _decorative_border(c, MRG, MRG, page_w - 2 * MRG, page_h - 2 * MRG)
    _logo_circle(c, MRG + 28, page_h - MRG - 28)
    _gold_seal(c,  page_w - MRG - 32, page_h - MRG - 30)

    ty = page_h - MRG - TOP_PAD - 20   # <<< changed: subtract TOP_PAD so business name starts lower
    business_name = (record.user.business_name or "VETERINARY PROFESSIONAL SERVICES").upper()
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(page_w / 2, ty,      business_name)
    sub_y = ty - 16
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    c.drawCentredString(page_w * 0.25, sub_y, f"Name: {record.user.first_name} {record.user.last_name}")
    c.drawCentredString(page_w / 2, sub_y, f"KVB No: {record.user.registration_number or ''}")
    c.drawCentredString(page_w * 0.75, sub_y, f"Contact: {record.user.phone_number or ''}")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(NAVY)
    c.drawCentredString(page_w / 2, ty - 28, "VACCINATION CERTIFICATE")

    ry = ty - 38
    c.setStrokeColor(GOLD); c.setLineWidth(1)
    c.line(MRG + 10, ry, page_w - MRG - 10, ry)

    def lv(x, y, label, value, lw=90):
        c.setFont(*LBL); c.setFillColor(colors.black); c.drawString(x, y, label)
        c.setFont(*VAL); c.drawString(x + lw, y, str(value or ""))
        c.setStrokeColor(colors.grey); c.setLineWidth(0.4); c.setDash(1, 2)
        c.line(x + lw, y - 3, x + lw + 150, y - 3)
        c.setDash()

    def sh(y, text):
        c.setFont("Helvetica-Bold", 11); c.setFillColor(NAVY)
        c.drawString(IL, y, text);       c.setFillColor(colors.black)

    y = ry - 12
    sh(y, "Owner Details:")
    y -= ROW
    half = (IR - IL) / 2
    lv(IL,        y, "Name:",        record.name_of_owner, lw=48)
    lv(IL + half, y, "Location:",    record.location,      lw=62)
    y -= ROW
    lv(IL,        y, "Village:",     record.village,       lw=48)
    lv(IL + half, y, "Contact No.:", record.contact,       lw=72)
    y -= ROW
    lv(IL,        y, "Sub-County:",  record.sub_county,    lw=68)
    lv(IL + half, y, "Ward:",        record.ward,          lw=42)

    y -= ROW + 4
    sh(y, "Animal Details:")
    y -= 8
    col_w = (IR - IL) / 7
    _table_row(c, IL, y, col_w,
               ["Animal Species", "Breed", "Reg. no.", "Age", "Sex", "Colour", "No. of Animal"],
               row_h=TBL_H, header=True)
    y -= TBL_H
    species = (record.other_species if record.species_targeted == "OTHER"
               and record.other_species else record.species_targeted)
    _table_row(c, IL, y, col_w, [
        species, record.breed_of_animal, record.reg_no,
        record.age_of_animal, record.sex_of_animal,
        record.color_of_animal, str(record.number_of_animals_vaccinated),
    ], row_h=TBL)
    y -= TBL + 16

    lv(IL, y, "Name:", record.name_of_animal or "", lw=48)
    c.setFont(*LBL); c.drawString(IL + 230, y, "Other Description:")
    c.setFont(*VAL); c.drawString(IL + 340, y, str(record.other_description or ""))

    y -= ROW + 4
    sh(y, "Vaccine Details:")
    y -= 8
    vcol = (IR - IL) / 6
    _table_row(c, IL, y, vcol,
               ["Vaccine", "Vaccinate against", "Batch No.",
                "Manufacturer", "Dosage", "Route of Admin."],
               row_h=TBL_H, header=True)
    y -= TBL_H
    disease = (record.other_disease if record.vaccination_of == "OTHER"
               and record.other_disease else record.vaccination_of)
    _table_row(c, IL, y, vcol,
               [record.vaccines_used, disease, record.batch_number, record.manufacturer,
                record.dosage, record.route_administration],
               row_h=TBL)
    y -= TBL + ROW

    # Row 1: Dates
    lv(IL,       y, "Date of Vaccination:",      str(record.date_of_vaccination),      lw=130)
    lv(IL + 255, y, "Next Date of Vaccination:", str(record.next_date_of_vaccination), lw=150)

    # Row 2: Expiry Left, Details Left
    y -= ROW
    lv(IL,       y, "Expiry Date of Vaccine:",   str(record.expiry_date),              lw=130)

    y -= ROW
    lv(IL,       y, "Vaccination Details:",      str(record.vaccination_type),         lw=130)

    y -= ROW
    lv(IL,       y, "Vaccination Status:",       str(record.nature_of_vaccination_program), lw=130)

    # Row 3: Dedicated Signature & Stamp area dropped down to provide stamp clearance block
    y -= (ROW * 2.5) # <--- Drop down significantly to leave blank space for physical ink stamp placement
    lv(IL + 255, y, "Signature and Stamp:",      str(record.signature),                lw=150)

    # >>> CHANGED: footer is now anchored near the bottom margin instead of
    # following directly after the signature row. Adjust FOOTER_GAP below
    # to move it closer to / further from the bottom border.
    FOOTER_GAP = 10   # <<< CHANGE ME: distance between bottom inner border and footer text
    footer_y = MRG + FOOTER_GAP
    c.setFont("Helvetica-Oblique", 8); c.setFillColor(colors.grey)
    c.drawCentredString(page_w / 2, footer_y,
                        f"This certificate is issued by {business_name}")

    c.save()
    buf.seek(0)
    return buf.read()
# ──────────────────────────────────────────────────────────────────────────────
#  ASYNC API View - Modified for background certificate generation
# ──────────────────────────────────────────────────────────────────────────────

class VaccinationRecordCreate(generics.CreateAPIView):
    """
    POST  /api/vaccination-records/
 
    1. Saves the VaccinationRecord to the DB.
    2. QUEUES PDF certificate generation (async).
    3. Returns IMMEDIATE response with task status.
    4. Certificate generation happens in background.
    """
    queryset           = VaccinationRecord.objects.all()
    serializer_class   = VaccinationRecordSerializer
    permission_classes = [Is_Vet]
 
    async def generate_certificate_background(self, record_id):
        """
        Background async task to generate and save certificate
        This runs independently without blocking the response
        """
        try:
            logger.info(f"Starting async certificate generation for record {record_id}")
            
            # Mark that generation is in progress (optional - add this field to model)
            await sync_to_async(VaccinationRecord.objects.filter(pk=record_id).update)(
                # certificate_generating=True  # Add this field if you want status tracking
            )
            
            # Get the record (async DB operation)
            record = await sync_to_async(VaccinationRecord.objects.get)(pk=record_id)
            
            # Generate PDF (CPU intensive - run in thread pool)
            # asyncio.to_thread prevents blocking the event loop
            pdf_bytes = await asyncio.to_thread(generate_vaccination_certificate, record)
            
            # Save to media (I/O operation - run in thread pool)
            saved_path = await asyncio.to_thread(save_certificate_to_media, record, pdf_bytes)
            
            # Update record with certificate path (async DB operation)
            await sync_to_async(VaccinationRecord.objects.filter(pk=record_id).update)(
                certificate_file=saved_path
                # certificate_generating=False
            )
            
            logger.info(f"Certificate generated successfully for record {record_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate certificate for record {record_id}: {str(e)}", exc_info=True)
            # Update record with error status
            await sync_to_async(VaccinationRecord.objects.filter(pk=record_id).update)(
                # certificate_error=str(e),  # Add this field if you want error tracking
                # certificate_generating=False
            )
        finally:
            # Clean up database connection to prevent leakage
            close_old_connections()
    
    def create(self, request, *args, **kwargs):
        """
        Synchronous entry point - creates record and starts async background task
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
 
        # 1. Persist record (synchronous - fast)
        record = serializer.save(user=request.user)
        
        # 2. Start async certificate generation in background
        try:
            # Get or create an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Start background task WITHOUT awaiting it
            asyncio.create_task(self.generate_certificate_background(record.pk))
            logger.info(f"Queued async certificate generation for record {record.pk}")
            
        except Exception as e:
            logger.error(f"Failed to queue certificate generation: {e}")
            # Fallback: generate synchronously
            logger.info(f"Falling back to synchronous generation for record {record.pk}")
            pdf_bytes = generate_vaccination_certificate(record)
            saved_path = save_certificate_to_media(record, pdf_bytes)
            VaccinationRecord.objects.filter(pk=record.pk).update(
                certificate_file=saved_path
            )
        
        # 3. Return IMMEDIATE response (doesn't wait for PDF generation)
        return Response(
            {
                "detail": "Vaccination record created. Certificate generation in progress.",
                "record_id": record.pk,
                "certificate_status": "generating",
                "status_check_endpoint": f"/api/vaccination-records/{record.pk}/status/",
                "message": "The certificate will be available shortly. Poll the status endpoint.",
            },
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────────────────────────────────────
#  Optional: Status Check Endpoint
# ──────────────────────────────────────────────────────────────────────────────

class CertificateStatusView(generics.RetrieveAPIView):
    """
    GET /api/vaccination-records/{id}/status/
    Check if certificate has been generated
    """
    queryset = VaccinationRecord.objects.all()
    permission_classes = [Is_Vet]
    
    def retrieve(self, request, *args, **kwargs):
        record = self.get_object()
        
        if record.certificate_file:
            # Certificate is ready
            return Response({
                "status": "completed",
                "record_id": record.pk,
                "certificate_url": certificate_url(record.certificate_file),
                "certificate_path": record.certificate_file,
                "ready": True,
            })
        else:
            # Certificate still generating
            return Response({
                "status": "generating",
                "record_id": record.pk,
                "ready": False,
                "message": "Certificate is being generated. Please check back soon.",
            })
 
class VaccinationRecordList(generics.ListAPIView):
    serializer_class = VaccinationRecordSerializer
    permission_classes = [Is_Vet|Is_Farmer | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
           
            return VaccinationRecord.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
           
            return VaccinationRecord.objects.filter(assigned_to_official=user).order_by('-id')
        
        
        if user.is_farmer:
            
            return VaccinationRecord.objects.filter(assigned_to=user).order_by('-id')

        return VaccinationRecord.objects.none()
    
class VaccinationRecordUpdate(generics.UpdateAPIView):
    queryset = VaccinationRecord.objects.all()
    serializer_class = VaccinationRecordSerializer
    permission_classes = [Is_Vet]

class VaccinationRecordDelete(generics.DestroyAPIView):
    queryset = VaccinationRecord.objects.all()
    serializer_class = VaccinationRecordSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
            
            
            
class ClinicalRecordCreate(generics.CreateAPIView):
    queryset = ClinicalRecord.objects.all()
    serializer_class = ClinicalRecordSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ClinicalRecordList(generics.ListAPIView):
    serializer_class = ClinicalRecordSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        
        if user.is_vet_officer:
            # Vet officers can view records they have created
            return ClinicalRecord.objects.filter(user=user).order_by('-id')

        elif user.is_farmer:
            # Farmers can view records assigned to them
            return ClinicalRecord.objects.filter(assigned_to=user).order_by('-id')

        return ClinicalRecord.objects.none()


class ClinicalRecordUpdate(generics.UpdateAPIView):
    queryset = ClinicalRecord.objects.all()
    serializer_class = ClinicalRecordSerializer
    permission_classes = [Is_Vet]

    

class ClinicalRecordDelete(generics.DestroyAPIView):
    queryset = ClinicalRecord.objects.all()
    serializer_class = ClinicalRecordSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


#############Shop############################


class ClientCreate(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class ClientList(generics.ListAPIView):
    serializer_class = ClientSerializer
    permission_classes = [Is_Vet]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return Client.objects.filter(user=self.request.user).order_by('-id')
class ClientUpdate(generics.UpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [Is_Vet]


class ClientDelete(generics.DestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
            

# Class-based view for creating a Diary record
class DiaryCreate(generics.CreateAPIView):
    queryset = Diary.objects.all()
    serializer_class = DiarySerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DiaryList(generics.ListAPIView):
    serializer_class = DiarySerializer
    permission_classes = [Is_Vet ]
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        ###print(user)
        return Diary.objects.filter(user=self.request.user).order_by('-id')

    


class DiaryUpdate(generics.UpdateAPIView):
    queryset = Diary.objects.all()
    serializer_class = DiarySerializer
    permission_classes = [Is_Vet]


class DiaryDelete(generics.DestroyAPIView):
    queryset = Diary.objects.all()
    serializer_class = DiarySerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class DiseaseReportCreate(generics.CreateAPIView):
    queryset = DiseaseReport.objects.all()
    serializer_class = DiseaseReportSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DiseaseReportList(generics.ListAPIView):
    serializer_class = DiseaseReportSerializer
    permission_classes = [Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return DiseaseReport.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return DiseaseReport.objects.filter(assigned_to_official=user).order_by('-id')

    
        return DiseaseReport.objects.none()

class DiseaseReportUpdate(generics.UpdateAPIView):
    queryset = DiseaseReport.objects.all()
    serializer_class = DiseaseReportSerializer
    permission_classes = [Is_Vet]

class DiseaseReportDelete(generics.DestroyAPIView):
    queryset = DiseaseReport.objects.all()
    serializer_class = DiseaseReportSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            


class SlaughterhouseCreate(generics.CreateAPIView):
    queryset = Slaughterhouse.objects.all()
    serializer_class = SlaughterhouseSerializer
    permission_classes = [Is_Vet | Is_Farmer | Is_Official]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SlaughterhouseList(generics.ListAPIView):
    serializer_class = SlaughterhouseSerializer
    permission_classes = [Is_Vet | Is_Farmer | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return Slaughterhouse.objects.filter(assigned_to_vet=user).order_by('-id')
        
        if user.is_official:
            return Slaughterhouse.objects.filter(assigned_to_official=user).order_by('-id')
        
        if user.is_farmer:
            return Slaughterhouse.objects.filter(user=user).order_by('-id')

        return Slaughterhouse.objects.none()

class SlaughterhouseUpdate(generics.UpdateAPIView):
    queryset = Slaughterhouse.objects.all()
    serializer_class = SlaughterhouseSerializer
    permission_classes = [Is_Vet]

class SlaughterhouseDelete(generics.DestroyAPIView):
    queryset = Slaughterhouse.objects.all()
    serializer_class = SlaughterhouseSerializer
    permission_classes = [Is_Vet]


# Employee Views
class EmployeeCreate(generics.CreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmployeeList(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return Employee.objects.filter(assigned_to_vet=user).order_by('-id')
        
        # if user.is_official:
        #     return Employee.objects.filter(assigned_to_official=user).order_by('-id')
        
        if user.is_farmer:
            return Employee.objects.filter(user=user).order_by('-id')

        return Employee.objects.none()

class EmployeeUpdate(generics.UpdateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [Is_Vet]

class EmployeeDelete(generics.DestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [Is_Vet]


# Butcher Views
class ButcherCreate(generics.CreateAPIView):
    queryset = Butcher.objects.all()
    serializer_class = ButcherSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ButcherList(generics.ListAPIView):
    serializer_class = ButcherSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return Butcher.objects.filter(user=user).order_by('-id').order_by('-id')
        
        elif user.is_farmer:
            return Butcher.objects.filter(user=user).order_by('-id').order_by('-id')

        return Butcher.objects.none()

class ButcherUpdate(generics.UpdateAPIView):
    queryset = Butcher.objects.all()
    serializer_class = ButcherSerializer
    permission_classes = [Is_Vet]

class ButcherDelete(generics.DestroyAPIView):
    queryset = Butcher.objects.all()
    serializer_class = ButcherSerializer
    permission_classes = [Is_Vet]


# Invoice Views

class InvoiceCreate(generics.CreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InvoiceList(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            
            return Invoice.objects.filter(user=user).order_by('-id')
        
        elif user.is_farmer:
            
            return Invoice.objects.filter(assigned_to=user).order_by('-id')

        return Invoice.objects.none()

class InvoiceUpdate(generics.UpdateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [Is_Vet]

class InvoiceDelete(generics.DestroyAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [Is_Vet]
    
   
@json_login_required
def score(request):
    return JsonResponse({"scores": safe_values(Attempt.objects.filter(user=request.user))})


 
@csrf_exempt
def start_quiz(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({'message': 'user_id is required'}, status=400)

        try:
            user = get_object_or_404(User, id=user_id)
            questions = get_random_questions_for_user(user)
            if not questions:
                return JsonResponse({'message': 'No questions available for your category'}, status=400)

            return JsonResponse({
                'questions': [{
                    'id': q.id,
                    'text': q.text,
                    'options': {'A': q.option_a, 'B': q.option_b, 'C': q.option_c, 'D': q.option_d}
                } for q in questions]
            })
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def submit_quiz(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            print(data)

            # Extract the user_id and answers
            user_id = data.get('user_id')
            answers = data.get('answers', {})

            # Get the user object or return a 404 if not found
            user = get_object_or_404(User, id=user_id)

            # Get or create the UserRetake object
            user_retake, created = UserRetake.objects.get_or_create(user=user)

            # Check if the user has any retakes left
            if user_retake.retakes_left < 1:
                return JsonResponse({'message': 'No retakes left', 'score': 0, 'retakes_left': 0}, status=400)

            score = 0
            # Process each question and its answer
            for question_id, answer in answers.items():
                question = get_object_or_404(Question, id=question_id)
                if question.correct_answer == answer:
                    score += 10

            # Save the attempt to the database
            attempt = Attempt.objects.create(user=user, score=score, attempt_number=4 - user_retake.retakes_left)

            # Check the score and respond accordingly
            if score >= 80:
                return JsonResponse({'message': 'Passed', 'score': score, 'retakes_left': user_retake.retakes_left})
            else:
                user_retake.retakes_left -= 1
                user_retake.save()
                return JsonResponse({'message': 'Failed', 'score': score, 'retakes_left': user_retake.retakes_left})

        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format'}, status=400)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'No attempts left'}, status=405)
def quiz_page(request):
    moderator = Moderator.objects.first()
    data = None
    if moderator:
        data = safe_values(Moderator.objects.filter(pk=moderator.pk))[0]
    return JsonResponse({"moderator": data})


    
# class QuestionListView(generics.ListAPIView):
#     permission_classes = [Is_Vet]
    
#     def get(self, request):
#         questions = Question.objects.all()
#         first_name = request.user.first_name.replace('%', '').strip()
#         last_name = request.user.last_name.replace('%', '').strip()
#         failed_attempts = QuestionResult.objects.filter(user=request.user, passed='fail').count()

#         # Determine if the submit button should be disabled (blurry)
#         disable_submit = failed_attempts >= 2

#         combined_name = f"{first_name} {last_name}"
#         context = {
#             'questions': questions,
#             'combined_name': combined_name,
#             'failed_attempts': failed_attempts,
#             'disable_submit': disable_submit  # Pass the flag to the template
#         }
#         return render(request, 'portals/reports/quiz.html', context)
    
    
class TutorialCreate(generics.CreateAPIView):
    queryset = Tutorial.objects.all()
    serializer_class = TutorialSerializer
    permission_classes = [Is_Vet | Is_Admin]


class TutorialList(generics.ListAPIView):

    serializer_class = TutorialSerializer
    permission_classes = [Is_Vet | Is_Admin]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        qs = Tutorial.objects.all()
        if is_admin_user(user):
            qs = qs.annotate(has_paid=Value(True, output_field=BooleanField()))
        else:
            purchases = LessonPurchase.objects.filter(lesson=OuterRef('pk'), user=user)
            qs = qs.annotate(has_paid=Exists(purchases))
        return qs.order_by('-created_at')
class TutorialUpdate(generics.UpdateAPIView):
    queryset = Tutorial.objects.all()
    serializer_class = TutorialSerializer
    permission_classes = [Is_Vet]

class TutorialDelete(generics.DestroyAPIView):
    queryset = Tutorial.objects.all()
    serializer_class = TutorialSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        instance.delete()

class SectionCreate(generics.CreateAPIView):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [Is_Vet]
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]

class SectionList(View):

    def get(self, request, lesson_id):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)

        ctx = {"request": request}
        admin = is_admin_user(request.user)
        tutorial = get_object_or_404(Tutorial, id=lesson_id)

        payment_date = None
        if not admin:
            purchase = LessonPurchase.objects.filter(user=request.user, lesson_id=lesson_id).first()
            payment_date = purchase.purchased_at if purchase else None

        has_access = admin or payment_date is not None
        contact_hours_value = get_contact_hours_value(tutorial.contact_hours)
        unlock_time = None if admin else get_unlock_time(payment_date, contact_hours_value)

        sections = Section.objects.filter(lesson_id=lesson_id).order_by("-id") if has_access \
            else Section.objects.none()

        comments = (
            Comment.objects.filter(section__in=sections)
            .select_related("author")
            .order_by("-created_at")[:5]
        )

        return JsonResponse({
            "lesson_id": lesson_id,
            "is_admin": admin,
            "tutorial": TutorialSerializer(tutorial, context=ctx).data,
            "sections": SectionSerializer(sections, many=True, context=ctx).data,
            "comments": CommentSerializer(comments, many=True, context=ctx).data,
            "payment_date": payment_date,
            "unlock_time": unlock_time,
            "contact_hours": contact_hours_value,
        })
def get_contact_hours_value(raw_contact_hours):
    """Extract numeric hours from strings like '6 hours', '6.5', '6'."""
    try:
        raw_hours = re.findall(r"[-+]?\d*\.?\d+", str(raw_contact_hours))
        return float(raw_hours[0]) if raw_hours else 0.0
    except (ValueError, TypeError, IndexError):
        return 0.0


def get_unlock_time(payment_date, contact_hours_value):
    """Exam unlocks at payment_date + contact_hours. None if unpaid."""
    if not payment_date:
        return None
    return payment_date + timedelta(hours=contact_hours_value)




class ExamAccessCheck(View):

    def get(self, request, lesson_id):
        if not request.user.is_authenticated:
            return JsonResponse({"locked": True, "reason": "not_authenticated"}, status=401)
            
        try:
            if not is_admin_user(request.user):
                purchase = LessonPurchase.objects.filter(user=request.user, lesson_id=lesson_id).first()
                if not purchase:
                    return JsonResponse({"locked": True, "reason": "payment_required"})

                tutorial = get_object_or_404(Tutorial, id=lesson_id)
                unlock_time = get_unlock_time(
                    purchase.purchased_at, get_contact_hours_value(tutorial.contact_hours)
                )
                if unlock_time is None or now() < unlock_time:
                    return JsonResponse({
                        "locked": True,
                        "reason": "time_locked",
                        "unlock_time": unlock_time.isoformat() if unlock_time else None,
                    })

            section = (
                Section.objects.filter(lesson_id=lesson_id, questions__isnull=False)
                .distinct().order_by("-id").first()
                or Section.objects.filter(lesson_id=lesson_id).order_by("-id").first()
            )
            if not section:
                return JsonResponse({"locked": True, "reason": "no_sections"}, status=404)

            return JsonResponse({
                "locked": False,
                "section_id": section.id,
                "exam_url": reverse("api:questions-list", kwargs={"section_id": section.id}),
            })
            try:
                exam_url = reverse('questions-list', kwargs={'section_id': section.id})
            except NoReverseMatch as e:
                return JsonResponse({"locked": True, "reason": "config_error", "detail": str(e)}, status=500)

            return JsonResponse({"locked": False, "exam_url": exam_url})

        except Exception as e:
            return JsonResponse({"locked": True, "reason": "server_error", "detail": str(e)}, status=500)
def download_file(request, section_id):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    try:
        section = Section.objects.get(id=section_id)
        if not has_lesson_access(request.user, section.lesson_id):
            return JsonResponse({"detail": "Payment required."}, status=403)
        file_path = section.file.path  
        
        # Verify that the file is in the 'media/uploads/' directory
        if os.path.exists(file_path) and 'media/uploads/' in file_path:
            # Serve the file as a downloadable response
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        else:
            raise Http404("File not found in the uploads directory")
    except Section.DoesNotExist:
        raise Http404("Section not found")
      
class CommentCreateView(generics.CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        section_id = self.kwargs.get('section_id')
        section = Section.objects.get(id=section_id)
        serializer.save(author=self.request.user, section=section)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        section_id = self.kwargs.get('section_id')
        if response.status_code == status.HTTP_201_CREATED:
            return redirect('comment-list', section_id=section_id)
        return response
        
class CommentListView(View):

    def get(self, request, section_id):
        get_object_or_404(Section, id=section_id)
        comments = Comment.objects.filter(section__id=section_id).order_by('-created_at')
        return JsonResponse({
            "section_id": section_id,
            "comments": CommentSerializer(comments, many=True, context={"request": request}).data,
        })


#cpd qustions 
class QuizView(View):

       def get(self, request, section_id):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)

        ctx = {"request": request}
        section = get_object_or_404(Section, id=section_id)

        # Same payment check the other CPD views use
        if not has_lesson_access(request.user, section.lesson_id):
            return JsonResponse({"detail": "Payment required."}, status=403)

        questions = CpdQuestions.objects.filter(section=section)
        first_name = (request.user.firstname or "").replace('%', '').strip()
        last_name = (request.user.lastname or "").replace('%', '').strip()
        failed_attempts = QuizResult.objects.filter(
            user=request.user, section=section, passed='fail'
        ).count()

        return JsonResponse({
            "section": SectionSerializer(section, context=ctx).data,
            "questions": CpdQuestionsSerializer(questions, many=True, context=ctx).data,
            "combined_name": f"{first_name} {last_name}".strip(),
            "failed_attempts": failed_attempts,
            "disable_submit": failed_attempts >= 2,
        })


class QuizSubmit(View):

    def post(self, request, section_id):
        section = get_object_or_404(Section, id=section_id)
        tutorial = section.lesson

        questions = CpdQuestions.objects.filter(section=section)
        total_questions = questions.count()

        if total_questions == 0:
            return JsonResponse({"error": "No questions available in this section"}, status=400)

        failed_attempts = QuizResult.objects.filter(
            user=request.user, section=section, passed='fail'
        ).count()

        if failed_attempts >= 2:
            return JsonResponse({
                "error": "You have already failed this quiz twice and can no longer retake it."
            }, status=403)

        correct_count = 0
        for question in questions:
            question_id = str(question.id)
            selected_choice_id = request.POST.get(f'answers[{question_id}]')

            correct_choice = CpdChoices.objects.filter(
                question_id=question.id, is_correct=True
            ).first()
            if correct_choice and str(correct_choice.id) == selected_choice_id:
                correct_count += 1

        score = (correct_count / total_questions) * 100
        passed_status = 'pass' if score >= 80 else 'fail'

        result = QuizResult.objects.create(
            user=request.user,
            section=section,
            score=score,
            passed=passed_status,
            failed_attempts=failed_attempts,
        )

        return JsonResponse({
            "result_id": result.id,
            "score": score,
            "passed": passed_status,
            "retake": passed_status == 'fail',
            "failed_attempts": failed_attempts,
            "section_id": section.id,
            "first_name": request.user.firstname,
"last_name": request.user.lastname,
            "tutorial_id": tutorial.id if tutorial else None,
        })


class QuestionCreateAPIView(generics.CreateAPIView):
    queryset = CpdQuestions.objects.all()
    serializer_class = CpdQuestionsSerializer
    permission_classes = [Is_Vet]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Question created successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# ───────────────────────── permissions / helpers ─────────────────────────

class AdminOnly(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_admin_user(request.user)


class AdminOrVet(IsAuthenticated):
    def has_permission(self, request, view):
        u = request.user
        return super().has_permission(request, view) and (
            is_admin_user(u) or getattr(u, "is_vet_officer", False)
        )


def _name(u):
    if not u:
        return "—"
    return f"{getattr(u, 'firstname', '')} {getattr(u, 'lastname', '')}".strip() or u.username


def _meeting_row(m, admin, paid, enabled, blocked):
    is_blocked = m.id in blocked
    can_join = admin or (not is_blocked and bool(m.access_enabled) and m.id in enabled)
    row = {
        "id": m.id,
        "meeting_id": m.meeting_id,
        "topic": m.topic,
        "facilitator": m.facilitator,
        "price": m.price,
        "start_time": m.start_time,
        "access_enabled": m.access_enabled,
        "user_has_paid": m.id in paid,
        "is_blocked": is_blocked,
        "can_join": can_join,
        "join_url": m.join_url if can_join else None,   # the paid-for link is never sent otherwise
    }
    if admin:
        row.update({
            "kvb_reg_no": m.kvb_reg_no or "",
            "activity_points": m.activity_points,
            "paid_count": getattr(m, "paid_count", 0),
        })
    return row


def _clean_meeting_fields(data, partial=False):
    """Validate the editable fields. Returns (dict, error)."""
    out = {}
    if "facilitator" in data:
        out["facilitator"] = (data.get("facilitator") or "").strip()[:100]
    if "kvb_reg_no" in data:
        out["kvb_reg_no"] = (data.get("kvb_reg_no") or "").strip()[:100] or None
    if "price" in data:
        try:
            price = Decimal(str(data.get("price") or 0))
        except InvalidOperation:
            return None, "Price must be a number."
        if price < 0 or price > Decimal("9999.99"):
            return None, "Price must be between 0 and 9999.99."
        out["price"] = price
    if "activity_points" in data:
        raw = data.get("activity_points")
        if raw in (None, ""):
            out["activity_points"] = None
        else:
            try:
                out["activity_points"] = int(float(raw))
            except (TypeError, ValueError):
                return None, "Activity points must be a whole number."
    if "access_enabled" in data:
        v = data.get("access_enabled")
        out["access_enabled"] = v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes", "on")
    return out, None


# ───────────────────────── list + create ─────────────────────────

@api_view(["GET", "POST"])
@permission_classes([AdminOrVet])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def zoom_meetings(request):
    admin = is_admin_user(request.user)

    if request.method == "POST":
        if not admin:
            return Response({"error": "Admin only"}, status=403)
        d = request.data
        topic = (d.get("topic") or "").strip()
        start_time = d.get("start_time")
        if not topic or not start_time:
            return Response({"error": "Topic and start time are required."}, status=400)
        fields, err = _clean_meeting_fields(d)
        if err:
            return Response({"error": err}, status=400)

        token = get_valid_access_token(request.user)
        if not token:
            return Response({"error": "zoom_not_connected"}, status=409)

        try:
            r = requests.post(
                "https://api.zoom.us/v2/users/me/meetings",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"topic": topic, "type": 2, "start_time": start_time,
                      "duration": 30, "timezone": "Africa/Nairobi"},
                timeout=30,
            )
        except requests.RequestException as e:
            return Response({"error": f"Unable to reach Zoom: {e}"}, status=502)

        if r.status_code != 201:
            try:
                msg = r.json().get("message", r.text)
            except Exception:
                msg = r.text
            return Response({"error": f"Zoom error: {msg}"}, status=502)

        z = r.json()
        m = ZoomMeeting.objects.create(
            user=request.user,
            meeting_id=str(z["id"]),
            topic=z["topic"],
            start_time=z["start_time"],
            join_url=z["join_url"],
            facilitator=fields.get("facilitator") or _name(request.user),
            price=fields.get("price", Decimal("0")),
            kvb_reg_no=fields.get("kvb_reg_no"),
            activity_points=fields.get("activity_points"),
            access_enabled=True,
        )
        return Response(_meeting_row(m, True, set(), set(), set()), status=201)

    # ---- list ----
    qs = ZoomMeeting.objects.all().order_by("-start_time", "-pk")
    if admin:
        qs = qs.annotate(paid_count=Count("meeting_payments",
                                          filter=Q(meeting_payments__status="Completed")))
    done = Payment.objects.filter(user=request.user, status="Completed", zoom_meeting__isnull=False)
    paid = set(done.values_list("zoom_meeting_id", flat=True))
    enabled = set(done.filter(user_access_enabled=True).values_list("zoom_meeting_id", flat=True))
    blocked = set(request.user.blocked_zoom_meetings.values_list("id", flat=True))

    return Response({
        "is_admin": admin,
        "meetings": [_meeting_row(m, admin, paid, enabled, blocked) for m in qs],
    })


# ───────────────────────── edit / delete ─────────────────────────

@api_view(["PATCH", "DELETE"])
@permission_classes([AdminOnly])
def zoom_meeting_detail(request, pk):
    m = get_object_or_404(ZoomMeeting, pk=pk)

    if request.method == "DELETE":
        if Payment.objects.filter(zoom_meeting=m, status="Completed").exists():
            return Response(
                {"error": "This meeting has completed payments. Turn access off instead of deleting it."},
                status=400)
        m.delete()
        return Response(status=204)

    # topic / start_time are NOT editable here: they live in Zoom and would go out of sync.
    fields, err = _clean_meeting_fields(request.data)
    if err:
        return Response({"error": err}, status=400)
    for k, v in fields.items():
        setattr(m, k, v)
    m.save()
    return Response({"ok": True, "access_enabled": m.access_enabled})


# ───────────────────────── payments / block ─────────────────────────

@api_view(["GET"])
@permission_classes([AdminOnly])
def zoom_meeting_payments(request, pk):
    m = get_object_or_404(ZoomMeeting, pk=pk)
    blocked = set(m.blocked_users.values_list("id", flat=True))
    rows = Payment.objects.filter(zoom_meeting=m).select_related("user").order_by("-created_at")
    return Response({"payments": [{
        "id": p.id,
        "user_id": p.user_id,
        "user_name": _name(p.user),
        "phone_number": p.phone_number,
        "amount": p.amount,
        "status": p.status,
        "mpesa_receipt": p.mpesa_receipt or "",
        "user_access_enabled": p.user_access_enabled,
        "is_blocked": p.user_id in blocked,
        "created_at": p.created_at,
    } for p in rows]})


@api_view(["POST"])
@permission_classes([AdminOnly])
def zoom_payment_access(request, pk):
    p = get_object_or_404(Payment, pk=pk, zoom_meeting__isnull=False)
    v = request.data.get("enabled")
    p.user_access_enabled = v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes")
    p.save(update_fields=["user_access_enabled"])
    return Response({"ok": True, "user_access_enabled": p.user_access_enabled})


@api_view(["POST"])
@permission_classes([AdminOnly])
def zoom_meeting_block(request, pk):
    m = get_object_or_404(ZoomMeeting, pk=pk)
    user = get_object_or_404(User, pk=request.data.get("user"))
    v = request.data.get("blocked")
    if v if isinstance(v, bool) else str(v).lower() in ("1", "true", "yes"):
        m.blocked_users.add(user)
    else:
        m.blocked_users.remove(user)
    return Response({"ok": True})


# ───────────────────────── attendance ─────────────────────────

@api_view(["GET"])
@permission_classes([AdminOrVet])
def zoom_attendance(request, meeting_id):
    """meeting_id is Zoom's meeting id (same as the old URL)."""
    m = ZoomMeeting.objects.filter(meeting_id=meeting_id).first()
    if not m:
        return Response({"error": "Meeting not found"}, status=404)

    admin = is_admin_user(request.user)
    qs = ZoomAttendance.objects.filter(meeting=m)
    if not admin:
        reg = getattr(request.user, "registration_number", None)
        if not reg:
            return Response({"meeting": {"id": m.id, "topic": m.topic}, "attendance": []})
        qs = qs.filter(kvb_number=reg)

    return Response({
        "meeting": {"id": m.id, "topic": m.topic, "start_time": m.start_time},
        "attendance": [{
            "id": a.id, "user_name": a.user_name, "kvb_number": a.kvb_number or "",
            "duration": a.duration, "points": a.points, "join_time": a.join_time,
        } for a in qs.order_by("user_name")],
    })


@api_view(["POST"])
@permission_classes([AdminOnly])
@parser_classes([MultiPartParser, FormParser])
def zoom_attendance_upload(request, pk):
    m = get_object_or_404(ZoomMeeting, pk=pk)
    f = request.FILES.get("file")
    if not f:
        return Response({"error": "Choose an Excel file."}, status=400)
    if not f.name.lower().endswith((".xlsx", ".xlsm")):
        return Response({"error": "Upload an .xlsx file."}, status=400)

    try:
        ws = load_workbook(f, data_only=True).active
    except Exception as e:
        return Response({"error": f"Could not read the Excel file: {e}"}, status=400)

    headers = [str(c.value).strip().lower() if c.value is not None else "" for c in ws[1]]
    need = ["user_name", "kvb_number", "duration", "points"]
    missing = [h for h in need if h not in headers]
    if missing:
        return Response({"error": "Missing columns: " + ", ".join(missing)}, status=400)
    col = {h: i for i, h in enumerate(headers)}

    created = updated = 0
    errors = []
    for n, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue
        try:
            name = str(row[col["user_name"]] or "").strip()
            kvb = str(row[col["kvb_number"]] or "").strip()
            if not name or not kvb:
                raise ValueError("user_name and kvb_number are required")
            duration = int(float(row[col["duration"]]))
            points = float(row[col["points"]])
            _, was_new = ZoomAttendance.objects.update_or_create(
                meeting=m, kvb_number=kvb,
                defaults={"user_name": name, "duration": duration, "points": points},
            )
            created += was_new
            updated += not was_new
        except Exception as e:
            errors.append(f"Row {n}: {e}")

    return Response({"created": created, "updated": updated, "errors": errors[:10],
                     "error_count": len(errors)})


# ───────────────────────── Zoom OAuth (no session needed) ─────────────────────────

@api_view(["GET"])
@permission_classes([AdminOnly])
def zoom_auth_url(request):
    """React asks for the URL, then sends the browser to Zoom. `state` carries who is connecting."""
    state = signing.dumps({"uid": request.user.pk}, salt="zoom-oauth")
    qs = urlencode({"response_type": "code", "client_id": ZOOM_CLIENT_ID,
                    "redirect_uri": ZOOM_REDIRECT_URI, "state": state})
    return Response({"url": f"https://zoom.us/oauth/authorize?{qs}"})


def zoom_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No code provided"}, status=400)
    try:
        uid = signing.loads(request.GET.get("state", ""), salt="zoom-oauth", max_age=600)["uid"]
        user = User.objects.get(pk=uid)
    except (signing.BadSignature, User.DoesNotExist, KeyError):
        return JsonResponse({"error": "Invalid or expired connection request. Try again."}, status=400)

    auth = base64.b64encode(f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        "https://zoom.us/oauth/token",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": ZOOM_REDIRECT_URI},
        timeout=30,
    )
    t = r.json()
    if "access_token" not in t:
        return JsonResponse({"error": t}, status=400)

    ZoomToken.objects.update_or_create(user=user, defaults={
        "access_token": t["access_token"],
        "refresh_token": t["refresh_token"],
        "expires_at": timezone.now() + timedelta(seconds=t["expires_in"]),
    })
    # ADJUST: where the React page lives (set FRONTEND_URL in settings, e.g. "https://app.example.com")
    return redirect(f"{getattr(settings, 'FRONTEND_URL', '')}/zoom?connected=1")


# ───────────────────────── urls.py ─────────────────────────
"""
from . import zoom_api as z

urlpatterns += [
    path("zoom/meetings/", z.zoom_meetings),                                   # GET list, POST create
    path("zoom/meetings/<int:pk>/", z.zoom_meeting_detail),                    # PATCH, DELETE
    path("zoom/meetings/<int:pk>/payments/", z.zoom_meeting_payments),
    path("zoom/meetings/<int:pk>/block/", z.zoom_meeting_block),
    path("zoom/meetings/<int:pk>/attendance-upload/", z.zoom_attendance_upload),
    path("zoom/payments/<int:pk>/access/", z.zoom_payment_access),
    path("zoom/attendance/<str:meeting_id>/", z.zoom_attendance),
    path("zoom/auth-url/", z.zoom_auth_url),
    path("zoom/callback/", z.zoom_callback),     # keep whatever path is registered in Zoom (ZOOM_REDIRECT_URI)
]
"""

def clean_text(text):
    if not text:
        return ""

    text = unquote(str(text))      # converts %20 → space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fit_text_scale(text, font, max_width, thickness, start_scale=1.0, min_scale=0.4, step=0.05):
    """Shrink font_scale until the text fits within max_width (in pixels)."""
    scale = start_scale
    while scale > min_scale:
        size = cv2.getTextSize(text, font, scale, thickness)[0]
        if size[0] <= max_width:
            return scale, size
        scale -= step
    return min_scale, cv2.getTextSize(text, font, min_scale, thickness)[0]


def draw_centered_text(img, text, y, font, color, thickness, max_width, start_scale=1.0, min_scale=0.4):
    """Draw text horizontally centered on the canvas at height y, auto-shrinking to fit."""
    canvas_width = img.shape[1]
    scale, size = fit_text_scale(text, font, max_width, thickness, start_scale, min_scale)
    x = (canvas_width - size[0]) // 2
    cv2.putText(img, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)
    return size


def generate_certificate(request, first_name, last_name):

    first_name = clean_text(first_name)
    last_name = clean_text(last_name)

    template_path = os.path.join(settings.STATIC_ROOT, "portals", "assets", "img", "certificate_1.png")
    template = cv2.imread(template_path)

    if template is None:
        return HttpResponse("Certificate template not found", status=500)

    tutorial_id = request.POST.get("tutorial_id") or request.GET.get("tutorial_id")
    if not tutorial_id:
        return HttpResponse("tutorial_id is required", status=400)

    tutorial = get_object_or_404(Tutorial, id=tutorial_id)

    registration_number = request.user.registration_number or ""
    date = now()
    date_string = date.strftime('%d/%m/%Y')

    cpd_number = tutorial.cpd_number or ""
    points = str(tutorial.points) if tutorial.points is not None else ""
    lesson = tutorial.theme or ""

    font = cv2.FONT_HERSHEY_COMPLEX
    font_scale = 2
    font_color = (0, 0, 255)
    thickness = 3

    canvas_width = template.shape[1]
    y_coordinate = 680
    spacing = 50

    first_name_size = cv2.getTextSize(first_name, font, font_scale, thickness)[0]
    last_name_size = cv2.getTextSize(last_name, font, font_scale, thickness)[0]
    total_name_width = first_name_size[0] + spacing + last_name_size[0]

    if total_name_width <= canvas_width:
        first_name_coords = ((canvas_width - total_name_width) // 2, y_coordinate)
        last_name_coords = (first_name_coords[0] + first_name_size[0] + spacing, y_coordinate)
    else:
        first_name_coords = (100, y_coordinate)
        last_name_coords = (first_name_coords[0] + first_name_size[0] + spacing, y_coordinate)

    date_coords = (800, 930)
    signature_coords = (1200, 950)
    kvb_no_coords = (993, 760)

    # ── New fields ────────────────────────────────────────────────────────
    # "...by The Kenya Veterinary Board as ____"  -> cpd_number
    cpd_number_coords = (860, 884)
    # "...with ____ Points on"                    -> points
    points_coords = (1372, 880)
    # "THEME: ____"                                -> lesson
    lesson_coords = (600, 1016)

    cv2.putText(template, first_name, first_name_coords, font, font_scale, font_color, thickness, cv2.LINE_AA)
    cv2.putText(template, last_name, last_name_coords, font, font_scale, font_color, thickness, cv2.LINE_AA)

    cv2.putText(template, date_string, date_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.putText(template, registration_number, kvb_no_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.putText(template, cpd_number, cpd_number_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(template, points, points_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(template, lesson, lesson_coords, font, 0.8, (0, 0, 0), 2, cv2.LINE_AA)

    success, buffer = cv2.imencode(".jpg", template)
    if not success:
        return HttpResponse("Error generating certificate", status=500)

    response = HttpResponse(buffer.tobytes(), content_type="image/jpeg")
    response["Content-Disposition"] = f'attachment; filename="{first_name}_certificate.jpg"'

    return response


def get_certificate(request, first_name, last_name):

    first_name = clean_text(first_name)
    last_name = clean_text(last_name)

    template_path = os.path.join(settings.STATIC_ROOT, "portals", "assets", "img", "certificate_2.png")
    template = cv2.imread(template_path)

    if template is None:
        return HttpResponse("Certificate template not found", status=500)

    meeting_id = request.POST.get("meeting_id") or request.GET.get("meeting_id")
    if not meeting_id:
        return HttpResponse("meeting_id is required", status=400)

    meeting = get_object_or_404(ZoomMeeting, id=meeting_id)

    registration_number = request.user.registration_number or ""
    date = now()
    date_string = date.strftime('%d/%m/%Y')

    kvb_reg_no = meeting.kvb_reg_no or ""
    activity_points = str(meeting.activity_points) if meeting.activity_points is not None else ""
    topic = meeting.topic or ""

    font = cv2.FONT_HERSHEY_COMPLEX
    font_scale = 2
    font_color = (0, 0, 255)
    thickness = 3

    canvas_width = template.shape[1]
    y_coordinate = 680
    spacing = 50

    first_name_size = cv2.getTextSize(first_name, font, font_scale, thickness)[0]
    last_name_size = cv2.getTextSize(last_name, font, font_scale, thickness)[0]
    total_name_width = first_name_size[0] + spacing + last_name_size[0]

    if total_name_width <= canvas_width:
        first_name_coords = ((canvas_width - total_name_width) // 2, y_coordinate)
        last_name_coords = (first_name_coords[0] + first_name_size[0] + spacing, y_coordinate)
    else:
        first_name_coords = (100, y_coordinate)
        last_name_coords = (first_name_coords[0] + first_name_size[0] + spacing, y_coordinate)

    date_coords = (400, 950)
    signature_coords = (1200, 950)
    kvb_no_coords = (910, 760)

    # ── New fields ────────────────────────────────────────────────────────
    # "...by The Kenya Veterinary Board as ____"  -> kvb_reg_no
    kvb_reg_no_line_coords = (860, 884)
    # "...with ____ Points on"                    -> activity_points
    activity_points_coords = (1372, 880)
    # "THEME: ____"                                -> topic
    topic_coords = (600, 1016)

    cv2.putText(template, first_name, first_name_coords, font, font_scale, font_color, thickness, cv2.LINE_AA)
    cv2.putText(template, last_name, last_name_coords, font, font_scale, font_color, thickness, cv2.LINE_AA)

    cv2.putText(template, date_string, date_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.putText(template, registration_number, kvb_no_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.putText(template, kvb_reg_no, kvb_reg_no_line_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(template, activity_points, activity_points_coords, font, 1, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(template, topic, topic_coords, font, 0.8, (0, 0, 0), 2, cv2.LINE_AA)

    success, buffer = cv2.imencode(".jpg", template)
    if not success:
        return HttpResponse("Error generating certificate", status=500)

    response = HttpResponse(buffer.tobytes(), content_type="image/jpeg")
    response["Content-Disposition"] = f'attachment; filename="{first_name}_certificate.jpg"'

    return response

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "is_admin", False))

ADMIN = [IsAuthenticated, IsSystemAdmin]





class TutorialSectionsView(generics.ListCreateAPIView):
    permission_classes = ADMIN
    serializer_class = AdminSectionSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Section.objects.filter(lesson_id=self.kwargs["tutorial_id"]).order_by("id")

    def perform_create(self, serializer):
        serializer.save(lesson=get_object_or_404(Tutorial, pk=self.kwargs["tutorial_id"]))


class SectionDetailView(generics.DestroyAPIView):
    permission_classes = ADMIN
    queryset = Section.objects.all()


class SectionQuestionsView(generics.ListCreateAPIView):
    permission_classes = ADMIN
    serializer_class = AdminQuestionSerializer
    parser_classes = [JSONParser]

    def get_queryset(self):
        return (CpdQuestions.objects.filter(section_id=self.kwargs["section_id"])
                .prefetch_related("choices").order_by("id"))

    def perform_create(self, serializer):
        section = get_object_or_404(Section, pk=self.kwargs["section_id"])
        serializer.save(user=self.request.user, section=section)


class QuestionDetailView(generics.DestroyAPIView):
    permission_classes = ADMIN
    queryset = CpdQuestions.objects.all()
class QuizResultList(generics.ListAPIView):
    serializer_class = QuizResultSerializer
    permission_classes = [Is_Vet]
    
    def get_queryset(self):
        user=self.request.user
        return QuizResult.objects.filter(user=user).order_by('-id')
    

# Create View
class LivestockExaminationCreate(generics.CreateAPIView):
    queryset = LivestockExaminationRecord.objects.all()
    serializer_class = LivestockExaminationRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
# List View
class LivestockExaminationList(generics.ListAPIView):
    serializer_class = LivestockExaminationRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return LivestockExaminationRecord.objects.filter(user=user).order_by('-id')

# Update View
class LivestockExaminationUpdate(generics.UpdateAPIView):
    queryset = LivestockExaminationRecord.objects.all()
    serializer_class = LivestockExaminationRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet]

# Delete View
class LivestockExaminationDelete(generics.DestroyAPIView):
    queryset = LivestockExaminationRecord.objects.all()
    serializer_class = LivestockExaminationRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            

# Create View
class CalvingRecordCreate(generics.CreateAPIView):
    queryset = CalvingRecord.objects.all()
    serializer_class = CalvingRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
# List View
class CalvingRecordList(generics.ListAPIView):
    serializer_class = CalvingRecordSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return CalvingRecord.objects.filter(user=user).order_by('-id')

# Update View
class CalvingRecordUpdate(generics.UpdateAPIView):
    queryset = CalvingRecord.objects.all()
    serializer_class = CalvingRecordSerializer
    permission_classes = [Is_Farmer]

# Delete View
class CalvingRecordDelete(generics.DestroyAPIView):
    queryset = CalvingRecord.objects.all()
    serializer_class = CalvingRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
    

# Create View
class AssessmentRecordCreate(generics.CreateAPIView):
    queryset = AssessmentRecord.objects.all()
    serializer_class = AssessmentRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet ]  

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

# List View
class AssessmentRecordList(generics.ListAPIView):
    serializer_class = AssessmentRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet |Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return AssessmentRecord.objects.filter(user=user).order_by('-id')
        if user.is_farmer:
                return AssessmentRecord.objects.filter(assigned_to=user).order_by('-id')

        return AssessmentRecord.objects.none()
# Update View
class AssessmentRecordUpdate(generics.UpdateAPIView):
    queryset = AssessmentRecord.objects.all()
    serializer_class = AssessmentRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet]

# Delete View
class AssessmentRecordDelete(generics.DestroyAPIView):
    queryset = AssessmentRecord.objects.all()
    serializer_class = AssessmentRecordSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
        

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def daily_kill_filter(request):
    try:
        user = request.user

        # 🧑‍⚕️ If vet officer: show records they assigned
        if getattr(user, 'is_vet_officer', False):
            records = DailyKill.objects.filter(
                assigned_by=user
            ).annotate(
                assigned_to_username=F("assigned_to_official__username")
            ).values(
                "id", "date", "livestock_category", "total_kills_per_day", "assigned_to_username"
            )
            return Response({
                "user_type": "vet_officer",
                "records": list(records),
            })

        # 🏛️ If official: show records assigned to them
        elif getattr(user, 'is_official', False):
            records = DailyKill.objects.filter(
                assigned_to_official=user
            ).annotate(
                assigned_by_username=F("assigned_by__username")
            ).values(
                "id", "date", "livestock_category", "total_kills_per_day", "assigned_by_username"
            )
            return Response({
                "user_type": "official",
                "records": list(records),
            })

        return Response({"error": "You do not have access to these records."}, status=403)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def ai_filter(request):
    try:
        user = request.user

        # 🧑‍⚕️ If vet officer: show records they assigned
        if getattr(user, 'is_vet_officer', False):
            records = ArtificialInsemination.objects.filter(
                assigned_by=user
            ).annotate(
                assigned_to_username=F("assigned_to_official__username")
            ).values(
                "id",
                "insemination_date",
                "species",
                "assigned_to_username"
            )

            return Response({
                "user_type": "vet_officer",
                "records": list(records),
            })

        # 🏛️ If official: show records assigned to them
        elif getattr(user, 'is_official', False):
            records = ArtificialInsemination.objects.filter(
                assigned_to_official=user
            ).annotate(
                assigned_by_username=F("assigned_by__username")
            ).values(
                "id",
                "insemination_date",
                "species",
                "assigned_by_username"
            )

            return Response({
                "user_type": "official",
                "records": list(records),
            })

        return Response(
            {"error": "You do not have access to these records."},
            status=403
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )
class DailyKillCreate(generics.CreateAPIView):
    queryset = DailyKill.objects.all()
    serializer_class = DailyKillSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        assigned_to_official = self.request.data.get("assigned_to_official")

        if assigned_to_official:
            serializer.save(user=user, assigned_by=user)  # Assign `assigned_by` if an official is assigned
        else:
            serializer.save(user=user)

class DailyKillList(generics.ListAPIView):
    serializer_class = DailyKillSerializer
    permission_classes = [Is_Vet | Is_Official|Is_SlaughterHouse]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        user_filter = self.request.query_params.get("user", None)  # Get user filter from query params

        if user_filter and user_filter.lower() == "all":
            return DailyKill.objects.all().order_by('-id')  # Retrieve all records

        if user.is_vet_officer:
            return DailyKill.objects.filter(user=user).order_by('-id')
        
        if user.is_farmer:
            return DailyKill.objects.filter(assigned_to_farmer=user).order_by('-id')


        if user.is_official:
            return DailyKill.objects.filter(assigned_to_official=user).order_by('-id')

        return DailyKill.objects.none()
class DailyKillUpdate(generics.UpdateAPIView):
    queryset = DailyKill.objects.all()
    serializer_class = DailyKillSerializer
    permission_classes = [Is_Vet]

class DailyKillDelete(generics.DestroyAPIView):
    queryset = DailyKill.objects.all()
    serializer_class = DailyKillSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
        

class MovementPermitCreate(generics.CreateAPIView):
    queryset = MovementPermit.objects.all()
    serializer_class = MovementPermitSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [Is_Vet]
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class MovementPermitList(generics.ListAPIView):
    serializer_class = MovementPermitSerializer
    permission_classes = [Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return MovementPermit.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return MovementPermit.objects.filter(assigned_to_official=user).order_by('-id')

        return MovementPermit.objects.none()

    def stream_file(self, request, permit_id):
        # Get the movement permit object based on the ID
        try:
            permit = MovementPermit.objects.get(id=permit_id)
        except MovementPermit.DoesNotExist:
            return HttpResponseNotFound("Movement Permit not found.")

        # Assuming `uploaded_report` is the file field on MovementPermit model
        file_path = permit.uploaded_permit.path

        # Check if the file exists
        if not os.path.exists(file_path):
            return HttpResponseNotFound("File not found.")

        # Open the file and stream it
        file = open(file_path, 'rb')
        response = FileResponse(file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{permit.uploaded_permit.name}"'
        return response

class MovementPermitUpdate(generics.UpdateAPIView):
    queryset = MovementPermit.objects.all()
    serializer_class = MovementPermitSerializer
    permission_classes = [Is_Vet]

class MovementPermitDelete(generics.DestroyAPIView):
    queryset = MovementPermit.objects.all()
    serializer_class = MovementPermitSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# No Objection Views


class NoObjectionCreate(generics.CreateAPIView):
    queryset = NoObjection.objects.all()
    serializer_class = NoObjectionSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
class NoObjectionList(generics.ListAPIView):
    serializer_class = NoObjectionSerializer
    permission_classes = [Is_Vet |Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return NoObjection.objects.filter(user=user)
        if user.is_official:
            return NoObjection.objects.filter(assigned_to_official=user)

        return NoObjection.objects.none()
class NoObjectionUpdate(generics.UpdateAPIView):
    queryset = NoObjection.objects.all()
    serializer_class = NoObjectionSerializer
    permission_classes = [Is_Vet|Is_Official]

class NoObjectionDelete(generics.DestroyAPIView):
    queryset = NoObjection.objects.all()
    serializer_class = NoObjectionSerializer
    permission_classes = [Is_Vet|Is_Official]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Monthly Report Views


class MonthlyReportCreate(generics.CreateAPIView):
    queryset = MonthlyReport.objects.all()
    serializer_class = MonthlyReportSerializer
    permission_classes = [Is_Vet |Is_Official]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class MonthlyReportList(generics.ListAPIView):
    serializer_class = MonthlyReportSerializer
    permission_classes = [Is_Vet |Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return MonthlyReport.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return MonthlyReport.objects.filter(assigned_to_official=user).order_by('-id')

        return MonthlyReport.objects.none()
class MonthlyReportUpdate(generics.UpdateAPIView):
    queryset = MonthlyReport.objects.all()
    serializer_class = MonthlyReportSerializer
    permission_classes = [Is_Vet |Is_Official]

class MonthlyReportDelete(generics.DestroyAPIView):
    queryset = MonthlyReport.objects.all()
    serializer_class = MonthlyReportSerializer
    permission_classes = [Is_Vet |Is_Official]

    def perform_destroy(self, instance):
        instance.delete()

        
class QuarterlyReportCreate(generics.CreateAPIView):
    queryset = QuarterlyReport.objects.all()
    serializer_class = QuarterlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class QuarterlyReportList(generics.ListAPIView):
    serializer_class = QuarterlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return  QuarterlyReport.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return QuarterlyReport.objects.filter(assigned_to_official=user).order_by('-id')

        return QuarterlyReport.objects.none()
class QuarterlyReportUpdate(generics.UpdateAPIView):
    queryset = QuarterlyReport.objects.all()
    serializer_class = QuarterlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]

class QuarterlyReportDelete(generics.DestroyAPIView):
    queryset = QuarterlyReport.objects.all()
    serializer_class = QuarterlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Yearly Report Views


# Yearly Report Views
class YearlyReportCreate(generics.CreateAPIView):
    queryset = YearlyReport.objects.all()
    serializer_class = YearlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class YearlyReportList(generics.ListAPIView):
    serializer_class = YearlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return YearlyReport.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return YearlyReport.objects.filter(assigned_to_official=user).order_by('-id')

        return YearlyReport.objects.none()
class YearlyReportUpdate(generics.UpdateAPIView):
    queryset = YearlyReport.objects.all()
    serializer_class = YearlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]

class YearlyReportDelete(generics.DestroyAPIView):
    queryset = YearlyReport.objects.all()
    serializer_class = YearlyReportSerializer
    permission_classes = [Is_Vet | Is_Official]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
 
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def prac_record_filter(request):
    try:
        user = request.user

        # 🧑‍⚕️ Vet officer: show records they assigned
        if getattr(user, 'is_vet_officer', False):
            records = Practitioner.objects.filter(
                assigned_by=user
            ).annotate(
                assigned_to_username=F("assigned_to_official__username")
            ).values(
                "id", "reg_date", "subcounty", "vet_category", "assigned_to_username"
            )
            return Response({
                "user_type": "vet_officer",
                "records": list(records),
            })

        # 🏛️ Government official: show records assigned to them
        elif getattr(user, 'is_official', False):
            records = Practitioner.objects.filter(
                assigned_to_official=user
            ).annotate(
                assigned_by_username=F("assigned_by__username")
            ).values(
                "id", "reg_date", "subcounty", "vet_category", "assigned_by_username"
            )
            return Response({
                "user_type": "official",
                "records": list(records),
            })

        return Response({"error": "You do not have access to these records."}, status=403)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
        


class PractitionerCreate(generics.CreateAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class PractitionerList(generics.ListAPIView):
    serializer_class = PractitionerSerializer
    permission_classes = [Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return Practitioner.objects.filter(user=user).order_by('-county')
        if user.is_official:
            return Practitioner.objects.filter(assigned_to_official=user)

        return Practitioner.objects.none()

class PractitionerUpdate(generics.UpdateAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [Is_Farmer | Is_Vet]

class PractitionerDelete(generics.DestroyAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
        

class UterineIrrigationCreate(generics.CreateAPIView):
    queryset = UterineIrrigationRecord.objects.all()
    serializer_class = UterineIrrigationRecordSerializer
    permission_classes = [Is_Vet | Is_Farmer]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)  


class UterineIrrigationList(generics.ListAPIView):
    serializer_class = UterineIrrigationRecordSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        
        if  user.is_vet_officer:
            return UterineIrrigationRecord.objects.filter(user=user).order_by('-id')
        if  user.is_farmer:
            return UterineIrrigationRecord.objects.filter(assigned_to=user).order_by('-id')

        return UterineIrrigationRecord.objects.none()


class UterineIrrigationUpdate(generics.UpdateAPIView):
    queryset = UterineIrrigationRecord.objects.all()
    serializer_class = UterineIrrigationRecordSerializer
    permission_classes = [Is_Vet | Is_Farmer]


class UterineIrrigationDelete(generics.DestroyAPIView):
    queryset = UterineIrrigationRecord.objects.all()
    serializer_class = UterineIrrigationRecordSerializer
    permission_classes = [Is_Vet | Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
        
        


class EmergencyCareCreate(generics.CreateAPIView):
    queryset = EmergencyCare.objects.all()
    serializer_class = EmergencyCareSerializer
    permission_classes = [Is_Vet | Is_Farmer]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class EmergencyCareList(generics.ListAPIView):
    serializer_class = EmergencyCareSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return EmergencyCare.objects.filter(user=user).order_by('-id')
        if user.is_farmer:
            return EmergencyCare.objects.filter(assigned_to=user).order_by('-id')

        return EmergencyCare.objects.none()

class EmergencyCareUpdate(generics.UpdateAPIView):
    queryset = EmergencyCare.objects.all()
    serializer_class = EmergencyCareSerializer
    permission_classes = [Is_Vet | Is_Farmer]

class EmergencyCareDelete(generics.DestroyAPIView):
    queryset = EmergencyCare.objects.all()
    serializer_class = EmergencyCareSerializer
    permission_classes = [Is_Vet | Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
        

# PriceList Views


class PriceListCreate(generics.CreateAPIView):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    permission_classes = [Is_Agrovet | Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class PriceListList(generics.ListAPIView):
    serializer_class = PriceListSerializer
    permission_classes = [Is_Agrovet | Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return PriceList.objects.filter(user=user).order_by('-id')

class PriceListUpdate(generics.UpdateAPIView):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    permission_classes = [Is_Agrovet | Is_Vet]

class PriceListDelete(generics.DestroyAPIView):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    permission_classes = [Is_Agrovet | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Supplier Views


class SupplierCreate(generics.CreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [Is_Farmer | Is_Vet |Is_Coop]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class SupplierList(generics.ListAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [Is_Farmer | Is_Vet |Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_cooperative:
            return Supplier.objects.filter(user=user)

        if user.is_official:
            return Supplier.objects.all()           

class SupplierUpdate(generics.UpdateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [Is_Farmer | Is_Vet]

class SupplierDelete(generics.DestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Client Views


class CustomerCreate(generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class CustomerList(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [Is_Farmer | Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return Customer.objects.filter(user=user).order_by('-id')

class CustomerUpdate(generics.UpdateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [Is_Farmer | Is_Vet]

class CustomerDelete(generics.DestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Creditor Views


class CreditorCreate(generics.CreateAPIView):
    queryset = Creditor.objects.all()
    serializer_class = CreditorSerializer
    permission_classes = [Is_Farmer | Is_Vet|Is_Agrovet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class CreditorList(generics.ListAPIView):
    serializer_class = CreditorSerializer
    permission_classes = [Is_Farmer | Is_Vet | Is_Agrovet]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return Creditor.objects.filter(user=user).order_by('-id')

class CreditorUpdate(generics.UpdateAPIView):
    queryset = Creditor.objects.all()
    serializer_class = CreditorSerializer
    permission_classes = [Is_Farmer | Is_Vet|Is_Agrovet]

class CreditorDelete(generics.DestroyAPIView):
    queryset = Creditor.objects.all()
    serializer_class = CreditorSerializer
    permission_classes = [Is_Farmer | Is_Vet | Is_Agrovet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# Debtor Views


class DebtorCreate(generics.CreateAPIView):
    queryset = Debtor.objects.all()
    serializer_class = DebtorSerializer
    permission_classes = [Is_Farmer | Is_Vet | Is_Agrovet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class DebtorList(generics.ListAPIView):
    serializer_class = DebtorSerializer
    permission_classes = [Is_Farmer | Is_Vet | Is_Agrovet]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return Debtor.objects.filter(user=user).order_by('-id')

class DebtorUpdate(generics.UpdateAPIView):
    queryset = Debtor.objects.all()
    serializer_class = DebtorSerializer
    permission_classes = [Is_Farmer | Is_Vet|Is_Agrovet]

class DebtorDelete(generics.DestroyAPIView):
    queryset = Debtor.objects.all()
    serializer_class = DebtorSerializer
    permission_classes = [Is_Farmer | Is_Vet | Is_Agrovet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            


@csrf_exempt
def update_request_status(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        new_status = request.POST.get("status")

        if not request_id or not new_status:
            return JsonResponse({"success": False, "error": "Missing data"}, status=400)

        try:
            client_request = ClientRequest.objects.get(id=request_id)
            client_request.status = new_status
            client_request.save()
            return JsonResponse({"success": True, "status": new_status})

        except ClientRequest.DoesNotExist:
            return JsonResponse({"success": False, "error": "Request not found"}, status=404)

    elif request.method == "GET":
        requests = ClientRequest.objects.values("id", "status","judgement")
        return JsonResponse({"success": True, "requests": list(requests)})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


class ClientRequestCreate(generics.CreateAPIView):
    queryset = ClientRequest.objects.all()
    serializer_class = ClientRequestSerializer
    permission_classes = [Is_Farmer | Is_Vet]
    
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class ClientRequestList(generics.ListAPIView):
    serializer_class = ClientRequestSerializer
    permission_classes = [Is_Farmer | Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_farmer:
            return ClientRequest.objects.filter(user=user).order_by('-id')
       
        if user.is_vet_officer:
            return ClientRequest.objects.filter(assigned_to=user).order_by('-id')


class ClientRequestUpdate(generics.UpdateAPIView):
    queryset = ClientRequest.objects.all()
    serializer_class = ClientRequestSerializer
    permission_classes = [Is_Farmer | Is_Vet]

class ClientRequestDelete(generics.DestroyAPIView):
    queryset = ClientRequest.objects.all()
    serializer_class = ClientRequestSerializer
    permission_classes = [Is_Farmer | Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class VetJudgmentCreate(generics.CreateAPIView):
    serializer_class = VetJudgmentSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    queryset = VetJudgment.objects.all()
    
    def perform_create(self, serializer):
        user = self.request.user
        vet_judgment = serializer.save(user=user)  # Save VetJudgment first
        
        client_request_id = self.request.data.get("client_request_id")
        
        if client_request_id:
            try:
                client_request = ClientRequest.objects.get(id=client_request_id)
                print("Before updating judgment:", client_request.judgement)  # Print before update
                
                client_request.judgement = True
                client_request.save()
                #client_request.refresh_from_db()# Save updated ClientRequest
                
                print("After updating judgment:", client_request.judgement)  # Print after update
            except ClientRequest.DoesNotExist:
                raise serializers.ValidationError({"client_request_id": "ClientRequest not found."}) 
              
class VetJudgmentList(generics.ListAPIView):
    serializer_class = VetJudgmentSerializer
    permission_classes = [Is_Vet | Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return VetJudgment.objects.filter(user=user).order_by('-id')
       
        if user.is_farmer:
            return VetJudgment.objects.filter(assigned_to=user).order_by('-id')


class VetJudgmentUpdate(generics.UpdateAPIView):
    queryset = VetJudgment.objects.all()
    serializer_class = VetJudgmentSerializer
    permission_classes = [Is_Vet]

class VetJudgmentDelete(generics.DestroyAPIView):
    queryset = VetJudgment.objects.all()
    serializer_class = VetJudgmentSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
  
def payment(request, lesson_id):
    lesson = get_object_or_404(Tutorial, id=lesson_id)
    return JsonResponse({
        "lesson_id": lesson.id,
        "lesson": lesson.lesson,
        "unit_price": lesson.unit_price,
    })


    
def payment_zoom(request, meeting_id):
    meeting = get_object_or_404(ZoomMeeting, id=meeting_id)
    return JsonResponse({
        "meeting_id": meeting.id,
        "topic": meeting.topic,
        "price": meeting.price,
    })


def format_phone_number(phone):
    if phone.startswith("0"):
        return "254" + phone[1:]
    return phone


@csrf_exempt
@user_passes_test(vet_check, login_url='vet-login')
def zoom_mpesa_payment(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Invalid request method"
        }, status=405)

    user = request.user

    meeting_id = request.POST.get("meeting_id")

    if not meeting_id:
        return JsonResponse({
            "error": "Missing meeting_id"
        }, status=400)

    try:

        zoom_meeting = ZoomMeeting.objects.get(
            id=meeting_id
        )

        amount = int(zoom_meeting.price)

    except ZoomMeeting.DoesNotExist:

        return JsonResponse({
            "error": "Meeting not found"
        }, status=404)

    phone_number = request.POST.get("phone_number")

    if not phone_number:
        return JsonResponse({
            "error": "Missing phone_number"
        }, status=400)

    phone_number = format_phone_number(phone_number)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()
    ).decode()

    access_token = get_mpesa_access_token()

    if not access_token:

        return JsonResponse({
            "error": "Failed to get access token"
        }, status=400)

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": TILL_NO,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "TransactionDesc": f"Payment for Meeting {meeting_id}",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:

        response = requests.post(
            MPESA_API_URL,
            json=payload,
            headers=headers
        )

        response_data = response.json()

    except Exception as e:

        return JsonResponse({
            "error": str(e)
        }, status=500)

    # =========================================
    # SAVE PAYMENT
    # =========================================

    if response_data.get("ResponseCode") == "0":

        Payment.objects.create(
            user=user,
            merchant_request_id=response_data["MerchantRequestID"],
            checkout_request_id=response_data["CheckoutRequestID"],
            amount=amount,
            phone_number=phone_number,
            zoom_meeting=zoom_meeting,
            status="Pending",
        )

    return JsonResponse({
        "payload": payload,
        "response": response_data
    }, safe=True)


@csrf_exempt
def initiate_mpesa_payment(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "Invalid request method"
        }, status=405)

    user = request.user

    lesson_id = request.POST.get("lesson_id")
    phone_number = request.POST.get("phone_number")

    if not lesson_id:
        return JsonResponse({
            "error": "Missing lesson_id"
        }, status=400)

    if not phone_number:
        return JsonResponse({
            "error": "Missing phone_number"
        }, status=400)

    try:
        lesson = Tutorial.objects.get(id=lesson_id)

    except Tutorial.DoesNotExist:
        return JsonResponse({
            "error": "Lesson not found"
        }, status=404)

    # Prevent duplicate purchases
    already_purchased = LessonPurchase.objects.filter(
        user=user,
        lesson=lesson
    ).exists()

    if already_purchased:
        return JsonResponse({
            "error": "You already purchased this lesson"
        }, status=400)

    amount = int(lesson.unit_price)

    phone_number = format_phone_number(phone_number)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()
    ).decode()

    access_token = get_mpesa_access_token()

    if not access_token:
        return JsonResponse({
            "error": "Failed to get access token"
        }, status=400)

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": TILL_NO,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": f"Lesson-{lesson.id}",
        "TransactionDesc": f"Payment for {lesson.lesson}",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:

        response = requests.post(
            MPESA_API_URL,
            json=payload,
            headers=headers
        )

        response_data = response.json()

        print("MPESA RESPONSE:", response_data)

    except Exception as e:

        return JsonResponse({
            "error": str(e)
        }, status=500)

    # Save payment only if request accepted
    if str(response_data.get("ResponseCode")) == "0":

        Payment.objects.create(
            user=user,
            merchant_request_id=response_data["MerchantRequestID"],
            checkout_request_id=response_data["CheckoutRequestID"],
            amount=amount,
            phone_number=phone_number,
            lesson=lesson,
            status="Pending",
        )

    return JsonResponse({
        "response": response_data
    }, status=200)


# =========================================
# MPESA CALLBACK
# =========================================

@csrf_exempt
def mpesa_callback(request):

    if request.method != "POST":

        return JsonResponse({
            "message": "Invalid request"
        }, status=200)

    try:

        raw_body = request.body.decode("utf-8")

        print("RAW CALLBACK:", raw_body)

        data = json.loads(raw_body)

        stk = data.get("Body", {}).get("stkCallback", {})

        result_code = str(stk.get("ResultCode"))

        checkout_id = stk.get("CheckoutRequestID")

        if not checkout_id:

            return JsonResponse({
                "message": "No checkout ID"
            }, status=200)

        payment = Payment.objects.filter(
            checkout_request_id=checkout_id
        ).first()

        if not payment:

            return JsonResponse({
                "message": "Payment not found"
            }, status=200)

        # =========================================
        # AVOID DUPLICATES
        # =========================================

        if payment.status == "Completed":

            return JsonResponse({
                "message": "Already processed"
            }, status=200)

        # =========================================
        # SUCCESS
        # =========================================

        if result_code == "0":

            metadata = stk.get(
                "CallbackMetadata",
                {}
            ).get("Item", [])

            amount = next(
                (
                    item.get("Value")
                    for item in metadata
                    if item.get("Name") == "Amount"
                ),
                None
            )

            receipt = next(
                (
                    item.get("Value")
                    for item in metadata
                    if item.get("Name") == "MpesaReceiptNumber"
                ),
                None
            )

            # =========================================
            # VERIFY AMOUNT
            # =========================================

            if float(amount) != float(payment.amount):

                payment.status = "Failed"
                payment.save()

                return JsonResponse({
                    "message": "Amount mismatch"
                }, status=200)

            payment.mpesa_receipt = receipt
            payment.status = "Completed"

            payment.save()

            # =========================================
            # LESSON ACCESS
            # =========================================

            if payment.lesson:

                LessonPurchase.objects.get_or_create(
                    user=payment.user,
                    lesson=payment.lesson,
                    payment=payment
                )

            # =========================================
            # ZOOM ACCESS
            # =========================================

            if payment.zoom_meeting:

                ZoomMeetingPurchase.objects.get_or_create(
                    user=payment.user,
                    zoom_meeting=payment.zoom_meeting,
                    payment=payment
                )

                payment.zoom_meeting.is_paid = True
                payment.zoom_meeting.save()

            return JsonResponse({
                "message": "Payment successful"
            }, status=200)

        # =========================================
        # FAILED
        # =========================================

        payment.status = "Failed"
        payment.save()

        return JsonResponse({
            "message": "Payment failed"
        }, status=200)

    except Exception as e:

        print("CALLBACK ERROR:", str(e))

        return JsonResponse({
            "message": "Callback error"
        }, status=200)

# =========================================
# CHECK PAYMENT STATUS
# =========================================

@csrf_exempt
@user_passes_test(vet_check, login_url='vet-login')
def check_mpesa_status(request):

    if request.method != "POST":

        return JsonResponse({
            "message": "Invalid request"
        }, status=400)

    checkout_request_id = request.POST.get(
        "checkout_request_id"
    )

    if not checkout_request_id:

        return JsonResponse({
            "error": "Missing checkout_request_id"
        }, status=400)

    payment = Payment.objects.filter(
        checkout_request_id=checkout_request_id,
        user=request.user
    ).first()

    if not payment:

        return JsonResponse({
            "error": "Payment not found"
        }, status=404)

    lesson_is_paid = False
    zoom_meeting_is_paid = False

    join_url = None

    # =========================================
    # LESSON ACCESS
    # =========================================

    if payment.lesson:

        lesson_is_paid = LessonPurchase.objects.filter(
            user=request.user,
            lesson=payment.lesson
        ).exists()

    # =========================================
    # ZOOM ACCESS
    # =========================================

    if payment.zoom_meeting:

        zoom_meeting_is_paid = ZoomMeetingPurchase.objects.filter(
            user=request.user,
            zoom_meeting=payment.zoom_meeting
        ).exists()

        if zoom_meeting_is_paid:

            join_url = payment.zoom_meeting.join_url

    return JsonResponse({
        "status": payment.status,
        "lesson_is_paid": lesson_is_paid,
        "zoom_meeting_is_paid": zoom_meeting_is_paid,
        "join_url": join_url,
    }, status=200)

# =========================================
# LESSON ACCESS VIEW
# =========================================


# Create View
class ManagementCommitteeCreate(generics.CreateAPIView):
    queryset = ManagementCommittee.objects.all()
    serializer_class = ManagementCommitteeSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

# List View
class ManagementCommitteeList(generics.ListAPIView):
    serializer_class = ManagementCommitteeSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return ManagementCommittee.objects.filter(user=user).order_by('-id')

# Update View
class ManagementCommitteeUpdate(generics.UpdateAPIView):
    queryset = ManagementCommittee.objects.all()
    serializer_class = ManagementCommitteeSerializer
    permission_classes = [Is_Farmer]

# Delete View
class ManagementCommitteeDelete(generics.DestroyAPIView):
    queryset = ManagementCommittee.objects.all()
    serializer_class = ManagementCommitteeSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


# -------------------------------------------
# Hides and Skins Record Views
# -------------------------------------------


# Create View
class HidesAndSkinsRecordCreate(generics.CreateAPIView):
    queryset = HidesAndSkinsRecord.objects.all()
    serializer_class = HidesAndSkinsRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

# List View
class HidesAndSkinsRecordList(generics.ListAPIView):
    serializer_class = HidesAndSkinsRecordSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return HidesAndSkinsRecord.objects.filter(user=user).order_by('-id')

# Update View
class HidesAndSkinsRecordUpdate(generics.UpdateAPIView):
    queryset = HidesAndSkinsRecord.objects.all()
    serializer_class = HidesAndSkinsRecordSerializer
    permission_classes = [Is_Farmer]

# Delete View
class HidesAndSkinsRecordDelete(generics.DestroyAPIView):
    queryset = HidesAndSkinsRecord.objects.all()
    serializer_class = HidesAndSkinsRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


# Create View
class ApprovedDairyFarmCreate(generics.CreateAPIView):
    queryset = ApprovedDairyFarm.objects.all()
    serializer_class = ApprovedDairyFarmSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

# List View
class ApprovedDairyFarmList(generics.ListAPIView):
    serializer_class = ApprovedDairyFarmSerializer
    permission_classes = [Is_Farmer | Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        
        return ApprovedDairyFarm.objects.all().order_by('-id')

# Update View
class ApprovedDairyFarmUpdate(generics.UpdateAPIView):
    queryset = ApprovedDairyFarm.objects.all()
    serializer_class = ApprovedDairyFarmSerializer
    permission_classes = [Is_Farmer]

# Delete View
class ApprovedDairyFarmDelete(generics.DestroyAPIView):
    queryset = ApprovedDairyFarm.objects.all()
    serializer_class = ApprovedDairyFarmSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            

class SlaughterhouseHygieneCreate(generics.CreateAPIView):
    queryset = SlaughterhouseHygiene.objects.all()
    serializer_class = SlaughterhouseHygieneSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SlaughterhouseHygieneList(generics.ListAPIView):
    serializer_class = SlaughterhouseHygieneSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        return SlaughterhouseHygiene.objects.filter(user=self.request.user).order_by('-id')

class SlaughterhouseHygieneUpdate(generics.UpdateAPIView):
    queryset = SlaughterhouseHygiene.objects.all()
    serializer_class = SlaughterhouseHygieneSerializer
    permission_classes = [Is_Farmer]

class SlaughterhouseHygieneDelete(generics.DestroyAPIView):
    queryset = SlaughterhouseHygiene.objects.all()
    serializer_class = SlaughterhouseHygieneSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

# =============================
# Slaughterhouse Asset Views
# =============================


class SlaughterhouseAssetCreate(generics.CreateAPIView):
    queryset = SlaughterhouseAsset.objects.all()
    serializer_class = SlaughterhouseAssetSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SlaughterhouseAssetList(generics.ListAPIView):
    serializer_class = SlaughterhouseAssetSerializer
    permission_classes = [Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        return SlaughterhouseAsset.objects.filter(user=self.request.user).order_by('-id')

class SlaughterhouseAssetUpdate(generics.UpdateAPIView):
    queryset = SlaughterhouseAsset.objects.all()
    serializer_class = SlaughterhouseAssetSerializer
    permission_classes = [Is_Farmer]

class SlaughterhouseAssetDelete(generics.DestroyAPIView):
    queryset = SlaughterhouseAsset.objects.all()
    serializer_class = SlaughterhouseAssetSerializer
    permission_classes = [Is_Farmer]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()         

def livestock_data(request, livestock_type):
    records = LivestockRegistration.objects.filter(
        livestock_type=livestock_type
    ).order_by('-id').values()

    data = {
        "count": records.count(),
        "next": None,
        "previous": None,
        "results": list(records)
    }

    return JsonResponse(data, safe=False)
# Template render views


class LivestockRegistrationCreate(generics.CreateAPIView):
    queryset = LivestockRegistration.objects.all()
    serializer_class = LivestockRegistrationSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

class LivestockRegistrationList(generics.ListAPIView):
    serializer_class = LivestockRegistrationSerializer
    permission_classes = [Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        return LivestockRegistration.objects.filter(user=self.request.user).order_by('-id')

class LivestockRegistrationUpdate(generics.UpdateAPIView):
    queryset = LivestockRegistration.objects.all()
    serializer_class = LivestockRegistrationSerializer
    permission_classes = [Is_Vet]

class LivestockRegistrationDelete(generics.DestroyAPIView):
    queryset = LivestockRegistration.objects.all()
    serializer_class = LivestockRegistrationSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
            
            
class VeterinaryEPrescriptionCreate(generics.CreateAPIView):
    queryset = VeterinaryEPrescription.objects.all()
    serializer_class = VeterinaryEPrescriptionSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class VeterinaryEPrescriptionList(generics.ListAPIView):
    serializer_class = VeterinaryEPrescriptionSerializer
    permission_classes = [Is_Vet | Is_Agrovet]
    pagination_class = CustomPagination

    def get_queryset(self):
        return VeterinaryEPrescription.objects.filter(user=self.request.user).order_by('-id')


class VeterinaryEPrescriptionUpdate(generics.UpdateAPIView):
    queryset = VeterinaryEPrescription.objects.all()
    serializer_class = VeterinaryEPrescriptionSerializer
    permission_classes = [Is_Vet | Is_Agrovet ]


class VeterinaryEPrescriptionDelete(generics.DestroyAPIView):
    queryset = VeterinaryEPrescription.objects.all()
    serializer_class = VeterinaryEPrescriptionSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()

class RoutineManagementCreate(generics.CreateAPIView):
    queryset = RoutineManagement.objects.all()
    serializer_class = RoutineManagementSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class RoutineManagementList(generics.ListAPIView):
    serializer_class = RoutineManagementSerializer
    permission_classes = [Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        return RoutineManagement.objects.filter(user=self.request.user).order_by('-id')


class RoutineManagementUpdate(generics.UpdateAPIView):
    queryset = RoutineManagement.objects.all()
    serializer_class = RoutineManagementSerializer
    permission_classes = [Is_Vet]


class RoutineManagementDelete(generics.DestroyAPIView):
    queryset = RoutineManagement.objects.all()
    serializer_class = RoutineManagementSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
            
            
class AbortionRecordCreate(generics.CreateAPIView):
    queryset = AbortionRecord.objects.all()
    serializer_class = AbortionRecordSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class AbortionRecordList(generics.ListAPIView):
    serializer_class = AbortionRecordSerializer
    permission_classes = [Is_Vet]
    pagination_class = CustomPagination

    def get_queryset(self):
        return AbortionRecord.objects.filter(user=self.request.user).order_by('-id')


class AbortionRecordUpdate(generics.UpdateAPIView):
    queryset = AbortionRecord.objects.all()
    serializer_class = AbortionRecordSerializer
    permission_classes = [Is_Vet]


class AbortionRecordDelete(generics.DestroyAPIView):
    queryset = AbortionRecord.objects.all()
    serializer_class = AbortionRecordSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            


# API Views
class ExtensionServiceCreate(generics.CreateAPIView):
    queryset = ExtensionService.objects.all()
    serializer_class = ExtensionServiceSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class ExtensionServiceList(generics.ListAPIView):
    serializer_class = ExtensionServiceSerializer
    permission_classes = [Is_Vet | Is_Official]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return ExtensionService.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return ExtensionService.objects.filter(assigned_to_official=user).order_by('-id')

    
        return ExtensionService.objects.none()

class ExtensionServiceUpdate(generics.UpdateAPIView):
    queryset = ExtensionService.objects.all()
    serializer_class = ExtensionServiceSerializer
    permission_classes = [Is_Vet]


class ExtensionServiceDelete(generics.DestroyAPIView):
    queryset = ExtensionService.objects.all()
    serializer_class = ExtensionServiceSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.created_by:
            instance.delete()
            
            
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):

    search = request.GET.get('search', '')
    role = request.GET.get('role', '')  # farmer OR vet

    queryset = User.objects.all()

    # Filter by role
    if role == "farmer":
        queryset = queryset.filter(is_farmer=True)
    elif role == "vet":
        queryset = queryset.filter(is_vet_officer=True)
    elif role == "official":
        queryset = queryset.filter(is_official=True)


    # Search username
    if search:
        queryset = queryset.filter(username__icontains=search)

    # Pagination (DRF)
    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginated = paginator.paginate_queryset(queryset, request)

    serializer = UserSearchSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


# API Views
class FieldQuotationCreate(generics.CreateAPIView):
    queryset = FieldQuotation.objects.all()
    serializer_class = FieldQuotationSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)


class FieldQuotationList(generics.ListAPIView):
    serializer_class = FieldQuotationSerializer
    permission_classes = [Is_Vet |Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            
            return FieldQuotation.objects.filter(user=user)
        
        elif user.is_farmer:
            
            return FieldQuotation.objects.filter(assigned_to=user)

        return FieldQuotation.objects.none()


class FieldQuotationUpdate(generics.UpdateAPIView):
    queryset = FieldQuotation.objects.all()
    serializer_class = FieldQuotationSerializer
    permission_classes = [Is_Vet]


class FieldQuotationDelete(generics.DestroyAPIView):
    queryset = FieldQuotation.objects.all()
    serializer_class = FieldQuotationSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
            
ZOOM_CLIENT_ID = config("ZOOM_API_KEY")
ZOOM_CLIENT_SECRET = config("ZOOM_API_SECRET")
ZOOM_REDIRECT_URI= config("REDIRECT_URL")

#@user_passes_test(vet_check, login_url='vet-login')
def zoom_auth(request):
    client_id = ZOOM_CLIENT_ID
    redirect_uri = ZOOM_REDIRECT_URI
    url = f"https://zoom.us/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    return redirect(url)

#@user_passes_test(vet_check, login_url='vet-login')
def zoom_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No code provided"}, status=400)

    client_id = ZOOM_CLIENT_ID
    client_secret = ZOOM_CLIENT_SECRET
    redirect_uri = ZOOM_REDIRECT_URI

    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    token_url = "https://zoom.us/oauth/token"
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    }

    response = requests.post(token_url, headers=headers, data=data)
    token_data = response.json()
    if "access_token" in token_data:
        expires_at = timezone.now() + timedelta(seconds=token_data["expires_in"])
        ZoomToken.objects.update_or_create(
            user=request.user,
            defaults={
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "expires_at": expires_at
            }
        )
        return redirect("schedule_zoom")
    else:
        return JsonResponse({"error": token_data}, status=400)

# ==========================
# Refresh token if expired
# ==========================
def get_valid_access_token(user):
    token = ZoomToken.objects.filter(user=user).first()
    if not token:
        return None

    if token.expires_at < timezone.now():
        # Refresh token
        client_id = ZOOM_CLIENT_ID
        client_secret = ZOOM_CLIENT_SECRET
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_url = "https://zoom.us/oauth/token"
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token
        }
        response = requests.post(token_url, headers=headers, data=data)
        token_data = response.json()
        if "access_token" in token_data:
            token.access_token = token_data["access_token"]
            token.refresh_token = token_data["refresh_token"]
            token.expires_at = timezone.now() + timedelta(seconds=token_data["expires_in"])
            token.save()
        else:
            return None
    return token.access_token

# ==========================
# Schedule Zoom Meeting
# ==========================


def user_can_join_meeting(user, meeting):

     return Payment.objects.filter(
        user=user,
        zoom_meeting=meeting,
        status="Completed",
        user_access_enabled=True
    ).exists() and meeting.access_enabled
@user_passes_test(vet_check, login_url='vet-login')
def zoom_schedule(request):

    # =========================================
    # CREATE MEETING
    # =========================================
    if request.method == "POST":
        if not getattr(request.user, "is_admin", False):
            return JsonResponse({"error": "Admin only"}, status=403)
        topic = (request.POST.get("topic") or "").strip()
        start_time = request.POST.get("start_time")
        if not topic or not start_time:
            return JsonResponse({"error": "topic and start_time are required"}, status=400)
        try:
            price = max(0, int(float(request.POST.get("price") or 0)))
        except ValueError:
            return JsonResponse({"error": "Invalid price"}, status=400)

        access_token = get_valid_access_token(request.user)
        if not access_token:
            return JsonResponse({"error": "zoom_not_connected"}, status=409)
        ...
        zoom_meeting = ZoomMeeting.objects.create(
            ...,
            price=price,
        )
        access_token = get_valid_access_token(request.user)

        if not access_token:
            return redirect("zoom_auth")   # OAuth hand-off, still needs a redirect

        url = "https://api.zoom.us/v2/users/me/meetings"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        data = {
            "topic": topic,
            "type": 2,
            "start_time": start_time,
            "duration": 30,
            "timezone": "Africa/Nairobi"
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:

            meeting = response.json()

            zoom_meeting = ZoomMeeting.objects.create(
                user=request.user,
                meeting_id=meeting["id"],
                topic=meeting["topic"],
                start_time=meeting["start_time"],
                join_url=meeting["join_url"],
                price=0
            )

            # The creator is the host, so they get the full record incl. join_url.
            return JsonResponse(
                safe_values(ZoomMeeting.objects.filter(pk=zoom_meeting.pk))[0],
                status=201
            )

        return JsonResponse({"error": response.json()}, status=500)

    # =========================================
    # LIST MEETINGS (ACCESS LOGIC)
    # =========================================
    queryset = ZoomMeeting.objects.all().order_by("-start_time", "-pk")
    rows = safe_values(queryset, exclude={"join_url"})

    meetings = []
    for m, row in zip(queryset, rows):

        # Blocked users are hard-blocked, even if paid or access is enabled
        is_blocked = m.blocked_users.filter(id=request.user.id).exists()

        user_has_paid = Payment.objects.filter(
            zoom_meeting=m,
            user=request.user,
            status="Completed"
        ).exists()

        can_join = (not is_blocked) and bool(m.access_enabled) and user_has_paid

        row.update({
            "is_blocked": is_blocked,
            "user_has_paid": user_has_paid,
            "can_join": can_join,
            "join_url": m.join_url if can_join else None,
        })
        meetings.append(row)

    return JsonResponse({"meetings": meetings})


# @user_passes_test(vet_check, login_url='vet-login')
# def fetch_zoom_attendance(request, meeting_id):
#     meeting = ZoomMeeting.objects.filter(meeting_id=meeting_id).first()
#     if not meeting:
#         return render(request, "portals/conf/points.html", {
#             "error": "Meeting not found"
#         })

#     access_token = get_valid_access_token(request.user)
#     if not access_token:
#         return redirect("zoom_auth")

#     url = f"https://api.zoom.us/v2/report/meetings/{meeting_id}/participants"
#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }

#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         return render(request, "portals/conf/points.html", {
#             "error": response.json(),
#             "meeting": meeting
#         })

#     participants = response.json().get("participants", [])

#     # Save attendance and calculate points
#     for p in participants:
#         email = p.get("email")
#         user = User.objects.filter(email=email).first()  # link registered user if exists

#         join_time = p.get("join_time")
#         leave_time = p.get("leave_time")
#         duration_minutes = p.get("duration", 0)
#         points = round(duration_minutes / 60, 2)  # 1 point per hour

#         ZoomAttendance.objects.update_or_create(
#             meeting=meeting,
#             user_email=email,
#             defaults={
#                 "user": user,
#                 "user_name": p.get("name"),
#                 "join_time": join_time,
#                 "leave_time": leave_time,
#                 "duration": duration_minutes,
#                 "points": points
#             }
#         )

#     attendance_list = ZoomAttendance.objects.filter(meeting=meeting)

#     return render(request, "portals/conf/points.html", {
#         "meeting": meeting,
#         "attendance": attendance_list,
#         "message": "Attendance fetched and points calculated successfully"
#     })

@user_passes_test(vet_check, login_url="vet-login")
def fetch_zoom_attendance(request, meeting_id):
    meeting = ZoomMeeting.objects.filter(meeting_id=meeting_id).first()
    if not meeting:
        return JsonResponse({"error": "Meeting not found"}, status=404)

    registration_number = getattr(request.user, "registration_number", None)

    # Only this user's attendance. join_url is withheld: it is the paid-for link.
    attendance = ZoomAttendance.objects.filter(
        meeting=meeting,
        kvb_number=registration_number
    )
    meeting_data = safe_values(
        ZoomMeeting.objects.filter(pk=meeting.pk), exclude={"join_url"}
    )[0]

    return JsonResponse({
        "meeting": meeting_data,
        "attendance": safe_values(attendance),
    })


    


class DairyFarmerRegistrationCreate(generics.CreateAPIView):
    queryset = DairyFarmerRegistration.objects.all()
    serializer_class = DairyFarmerRegistrationSerializer
    permission_classes = [Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DairyFarmerRegistrationList(generics.ListAPIView):
    serializer_class = DairyFarmerRegistrationSerializer
    permission_classes = [Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        return DairyFarmerRegistration.objects.filter(
            user=self.request.user
        ).order_by('-id')


class DairyFarmerRegistrationUpdate(generics.UpdateAPIView):
    queryset = DairyFarmerRegistration.objects.all()
    serializer_class = DairyFarmerRegistrationSerializer
    permission_classes = [Is_Coop]


class DairyFarmerRegistrationDelete(generics.DestroyAPIView):
    queryset = DairyFarmerRegistration.objects.all()
    serializer_class = DairyFarmerRegistrationSerializer
    permission_classes = [Is_Coop]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


# ---------------------------------------------------------------------
# 2. MILK COLLECTION CENTER VIEWS
# ---------------------------------------------------------------------

class MilkCollectionCenterCreate(generics.CreateAPIView):
    queryset = MilkCollectionCenter.objects.all()
    serializer_class = MilkCollectionCenterSerializer
    permission_classes = [Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MilkCollectionCenterList(generics.ListAPIView):
    serializer_class = MilkCollectionCenterSerializer
    permission_classes = [Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        return MilkCollectionCenter.objects.filter(
            user=self.request.user
        ).order_by('-id')


class MilkCollectionCenterUpdate(generics.UpdateAPIView):
    queryset = MilkCollectionCenter.objects.all()
    serializer_class = MilkCollectionCenterSerializer
    permission_classes = [Is_Coop]


class MilkCollectionCenterDelete(generics.DestroyAPIView):
    queryset = MilkCollectionCenter.objects.all()
    serializer_class = MilkCollectionCenterSerializer
    permission_classes = [Is_Coop]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


# ---------------------------------------------------------------------
# 3. CURRENT MILK PRICE VIEWS
# ---------------------------------------------------------------------

class CurrentMilkPriceCreate(generics.CreateAPIView):
    queryset = CurrentMilkPrice.objects.all()
    serializer_class = CurrentMilkPriceSerializer
    permission_classes = [Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CurrentMilkPriceList(generics.ListAPIView):
    serializer_class = CurrentMilkPriceSerializer
    permission_classes = [Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        return CurrentMilkPrice.objects.filter(
            user=self.request.user
        ).order_by('-id')


class CurrentMilkPriceUpdate(generics.UpdateAPIView):
    queryset = CurrentMilkPrice.objects.all()
    serializer_class = CurrentMilkPriceSerializer
    permission_classes = [Is_Coop]


class CurrentMilkPriceDelete(generics.DestroyAPIView):
    queryset = CurrentMilkPrice.objects.all()
    serializer_class = CurrentMilkPriceSerializer
    permission_classes = [Is_Coop]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


# ---------------------------------------------------------------------
# 4. FARMER MILK PAYMENT VIEWS
# ---------------------------------------------------------------------

class FarmerMilkPaymentCreate(generics.CreateAPIView):
    queryset = FarmerMilkPayment.objects.all()
    serializer_class = FarmerMilkPaymentSerializer
    permission_classes = [Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FarmerMilkPaymentList(generics.ListAPIView):
    serializer_class = FarmerMilkPaymentSerializer
    permission_classes = [Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        return FarmerMilkPayment.objects.filter(
            user=self.request.user
        ).order_by('-id')


class FarmerMilkPaymentUpdate(generics.UpdateAPIView):
    queryset = FarmerMilkPayment.objects.all()
    serializer_class = FarmerMilkPaymentSerializer
    permission_classes = [Is_Coop]


class FarmerMilkPaymentDelete(generics.DestroyAPIView):
    queryset = FarmerMilkPayment.objects.all()
    serializer_class = FarmerMilkPaymentSerializer
    permission_classes = [Is_Coop]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
class  MilkCollectionCoolerCreate(generics.CreateAPIView):
    queryset =  MilkCollectionCooler.objects.all()
    serializer_class =  MilkCollectionCoolerSerializer
    permission_classes = [Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MilkCollectionCoolerList(generics.ListAPIView):
    serializer_class = MilkCollectionCoolerSerializer
    permission_classes = [Is_Coop,Is_Farmer]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        if user.role == "farmer":
            return MilkCollectionCooler.objects.filter(
                assigned_to=user.username
            ).order_by("-id")

        return MilkCollectionCooler.objects.filter(
            user=user
        ).order_by("-id")

class  MilkCollectionCoolerUpdate(generics.UpdateAPIView):
    queryset =  MilkCollectionCooler.objects.all()
    serializer_class =  MilkCollectionCoolerSerializer
    permission_classes = [Is_Coop]


class  MilkCollectionCoolerDelete(generics.DestroyAPIView):
    queryset =  MilkCollectionCooler.objects.all()
    serializer_class =  MilkCollectionCoolerSerializer
    permission_classes = [Is_Coop]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()
            
class MilkCollectionCenterRecordCreate(generics.CreateAPIView):
    queryset = MilkCollectionCenterRecord.objects.all()
    serializer_class = MilkCollectionCenterRecordSerializer
    permission_classes = [Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MilkCollectionCenterRecordList(generics.ListAPIView):
    serializer_class = MilkCollectionCenterRecordSerializer
    permission_classes = [Is_Coop]
    pagination_class = CustomPagination

    def get_queryset(self):
        return MilkCollectionCenterRecord.objects.filter(
            user=self.request.user
        ).order_by('-id')


class MilkCollectionCenterRecordUpdate(generics.UpdateAPIView):
    queryset = MilkCollectionCenterRecord.objects.all()
    serializer_class = MilkCollectionCenterRecordSerializer
    permission_classes = [Is_Coop]


class MilkCollectionCenterRecordDelete(generics.DestroyAPIView):
    queryset = MilkCollectionCenterRecord.objects.all()
    serializer_class = MilkCollectionCenterRecordSerializer
    permission_classes = [Is_Coop]

    def perform_destroy(self, instance):
        if self.request.user == instance.user:
            instance.delete()


class DailyRevenueCollectionCreate(generics.CreateAPIView):
    queryset = DailyRevenueCollection.objects.all()
    serializer_class = DailyRevenueCollectionSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyRevenueCollectionList(generics.ListAPIView):
    serializer_class = DailyRevenueCollectionSerializer
    permission_classes =[Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return DailyRevenueCollection.objects.filter(user=user)
        if user.is_official:
            return DailyRevenueCollection.objects.filter(assigned_to_official=user)


class DailyRevenueCollectionUpdate(generics.UpdateAPIView):
    queryset = DailyRevenueCollection.objects.all()
    serializer_class = DailyRevenueCollectionSerializer
    permission_classes = [Is_Vet]


class DailyRevenueCollectionDelete(generics.DestroyAPIView):
    queryset = DailyRevenueCollection.objects.all()
    serializer_class = DailyRevenueCollectionSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        instance.delete()
        


class LeaveRequestCreate(generics.CreateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LeaveRequestList(generics.ListAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_vet_officer:
            return LeaveRequest.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return LeaveRequest.objects.filter(assigned_to_official=user).order_by('-id')

       

class LeaveRequestUpdate(generics.UpdateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [Is_Vet]


class LeaveRequestDelete(generics.DestroyAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [Is_Vet]

    def perform_destroy(self, instance):
        instance.delete()
        


# def practitioner_(request):
#     return render(request, 'portals/svco/practitioner.html', {})


# class PractitionersCreate(generics.CreateAPIView):
#     queryset = Practitioners.objects.all()
#     serializer_class = PractitionersSerializer
#     permission_classes = [Is_Vet]
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


# class PractitionersList(generics.ListAPIView):
#     serializer_class = PractitionersSerializer
#     permission_classes = [Is_Vet]

#     def get_queryset(self):
#         return Practitioners.objects.filter(user=self.request.user).order_by('-date_of_record')


# class PractitionersUpdate(generics.UpdateAPIView):
#     queryset = Practitioners.objects.all()
#     serializer_class = PractitionerSerializer
#     permission_classes = [Is_Vet]


# class PractitionersDelete(generics.DestroyAPIView):
#     queryset = Practitioners.objects.all()
#     serializer_class = PractitionersSerializer
#     permission_classes = [Is_Vet]
#     def perform_destroy(self, instance):
#         instance.delete()
        


class SlaughterHousesCreate(generics.CreateAPIView):
    queryset = SlaughterHouses.objects.all()
    serializer_class = SlaughterHousesSerializer
    permission_classes = [Is_Vet]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SlaughterHousesList(generics.ListAPIView):
    serializer_class = SlaughterHousesSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return SlaughterHouses.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return SlaughterHouses.objects.filter(assigned_to_official=user).order_by('-id')

    
        return SlaughterHouses.objects.none()
       
       

class SlaughterHousesUpdate(generics.UpdateAPIView):
    queryset = SlaughterHouses.objects.all()
    serializer_class = SlaughterHousesSerializer
    permission_classes = [Is_Vet]


class SlaughterHousesDelete(generics.DestroyAPIView):
    queryset = SlaughterHouses.objects.all()
    serializer_class = SlaughterHousesSerializer
    permission_classes = [Is_Vet]
    def perform_destroy(self, instance):
        instance.delete()
        


class DailyKillsCreate(generics.CreateAPIView):
    queryset = DailyKills.objects.all()
    serializer_class = DailyKillsSerializer
    permission_classes = [Is_Vet]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyKillsList(generics.ListAPIView):
    serializer_class = DailyKillsSerializer
    permission_classes = [Is_Vet|Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return DailyKills.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return DailyKills.objects.filter(assigned_to_official=user).order_by('-id')

    
        return DailyKills.objects.none()
       
       

class DailyKillsUpdate(generics.UpdateAPIView):
    queryset = DailyKills.objects.all()
    serializer_class = DailyKillsSerializer
    permission_classes = [Is_Vet]


class DailyKillsDelete(generics.DestroyAPIView):
    queryset = DailyKills.objects.all()
    serializer_class = DailyKillsSerializer
    permission_classes = [Is_Vet]
    def perform_destroy(self, instance):
        instance.delete()
        


class MovementPermitsCreate(generics.CreateAPIView):
    queryset = MovementPermits.objects.all()
    serializer_class = MovementPermitsSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MovementPermitsList(generics.ListAPIView):
    serializer_class = MovementPermitsSerializer
    permission_classes = [Is_Vet|Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return MovementPermits.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return MovementPermits.objects.filter(assigned_to_official=user).order_by('-id')

        return MovementPermits.objects.none()

class MovementPermitsUpdate(generics.UpdateAPIView):
    queryset = MovementPermits.objects.all()
    serializer_class = MovementPermitsSerializer
    permission_classes = [Is_Vet]


class MovementPermitsDelete(generics.DestroyAPIView):
    queryset = MovementPermits.objects.all()
    serializer_class = MovementPermitsSerializer
    permission_classes = [Is_Vet | Is_Official]
    def perform_destroy(self, instance):
        instance.delete()
        


class NoObjectionsCreate(generics.CreateAPIView):
    queryset = NoObjections.objects.all()
    serializer_class = NoObjectionsSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoObjectionsList(generics.ListAPIView):
    serializer_class = NoObjectionsSerializer
    permission_classes =[Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return NoObjections.objects.filter(user=user)
        if user.is_official:
            return NoObjections.objects.filter(assigned_to_official=user)


class NoObjectionsUpdate(generics.UpdateAPIView):
    queryset = NoObjections.objects.all()
    serializer_class = NoObjectionsSerializer
    permission_classes = [Is_Vet]


class NoObjectionsDelete(generics.DestroyAPIView):
    queryset = NoObjections.objects.all()
    serializer_class = NoObjectionsSerializer
    permission_classes = [Is_Vet]
    def perform_destroy(self, instance):
        instance.delete()
        
    


class ArtificialInseminationViewSet(viewsets.ModelViewSet):
    queryset = ArtificialInsemination.objects.all()
    serializer_class = ArtificialInseminationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)
class ArtificialInseminationsList(generics.ListAPIView):
    serializer_class = ArtificialInseminationsSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user
        if user.is_vet_officer:
            return ArtificialInseminations.objects.filter(user=user).order_by('-id')
        if user.is_official:
            return ArtificialInseminations.objects.filter(assigned_to_official=user).order_by('-id')


class ArtificialInseminationsUpdate(generics.UpdateAPIView):
    queryset = ArtificialInseminations.objects.all()
    serializer_class = ArtificialInseminationsSerializer
    permission_classes = [Is_Vet]

    def perform_update(self, serializer):
        # Ensure the user remains the owner during updates
        serializer.save(user=self.request.user)


class ArtificialInseminationsDelete(generics.DestroyAPIView):
    queryset = ArtificialInseminations.objects.all()
    serializer_class = ArtificialInseminationsSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        # Ensure users can only delete their own records
        return ArtificialInseminations.objects.filter(user=self.request.user)   


class VaccinationsCreate(generics.CreateAPIView):
    queryset = Vaccinations.objects.all()
    serializer_class = VaccinationsSerializer
    permission_classes = [Is_Vet]
    def perform_create(self, serializer):
        # Automatically set the user field to the logged-in user
        serializer.save(user=self.request.user)


class VaccinationsList(generics.ListAPIView):
    serializer_class = VaccinationsSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return Vaccinations.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return Vaccinations.objects.filter(assigned_to_official=user).order_by('-id')

    
        return Vaccinations.objects.none()
       
       

class VaccinationsUpdate(generics.UpdateAPIView):
    queryset = Vaccinations.objects.all()
    serializer_class = VaccinationsSerializer
    permission_classes = [Is_Vet]


class VaccinationsDelete(generics.DestroyAPIView):
    queryset = Vaccinations.objects.all()
    serializer_class = VaccinationsSerializer
    permission_classes = [Is_Vet]
    def perform_destroy(self, instance):
        instance.delete()
        


class ExtensionServicesCreate(generics.CreateAPIView):
    queryset = ExtensionServices.objects.all()
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]
    def perform_create(self, serializer):
        # Automatically set the user field to the logged-in user
        serializer.save(user=self.request.user)


class ExtensionServicesList(generics.ListAPIView):
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        return ExtensionServices.objects.filter(user=self.request.user).order_by('-date_of_record')


class ExtensionServicesUpdate(generics.UpdateAPIView):
    queryset = ExtensionServices.objects.all()
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]


class ExtensionServicesDelete(generics.DestroyAPIView):
    queryset = ExtensionServices.objects.all()
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]
    def perform_destroy(self, instance):
        instance.delete()
        
    


class DiseaseReportMovsCreate(generics.CreateAPIView):
    queryset = DiseaseReportMov.objects.all()
    serializer_class = DiseaseReportMovsSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        # Automatically link the report to the logged-in Vet
        serializer.save(user=self.request.user)


class DiseaseReportMovsList(generics.ListAPIView):
    serializer_class = DiseaseReportMovsSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return DiseaseReportMov.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return DiseaseReportMov.objects.filter(assigned_to_official=user).order_by('-id')

    
        return DiseaseReportMov.objects.none()
       

class DiseaseReportMovsUpdate(generics.UpdateAPIView):
    queryset = DiseaseReportMov.objects.all()
    serializer_class = DiseaseReportMovsSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        # Ensure a vet can only update their own reports
        return DiseaseReportMov.objects.filter(user=self.request.user)


class DiseaseReportMovsDelete(generics.DestroyAPIView):
    queryset = DiseaseReportMov.objects.all()
    serializer_class = DiseaseReportMovsSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        # Ensure a vet can only delete their own reports
        return DiseaseReportMov.objects.filter(user=self.request.user)
    
class ExtensionServicesCreate(generics.CreateAPIView):
    queryset = ExtensionServices.objects.all()
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        # Automatically set the 'user' field to the current logged-in user
        serializer.save(user=self.request.user)


class ExtensionServicesList(generics.ListAPIView):
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return ExtensionServices.objects.filter(user=user).order_by('-id')
        
        if user.is_official:
            return ExtensionServices.objects.filter(assigned_to_official=user).order_by('-id')

    
        return ExtensionServices.objects.none()
       
       

class ExtensionServicesUpdate(generics.UpdateAPIView):
    queryset = ExtensionServices.objects.all()
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        # Ownership check: users can only update their own records
        return ExtensionServices.objects.filter(user=self.request.user)


class ExtensionServicesDelete(generics.DestroyAPIView):
    queryset = ExtensionServices.objects.all()
    serializer_class = ExtensionServicesSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        # Ownership check: users can only delete their own records
        return ExtensionServices.objects.filter(user=self.request.user)
    
class PractitionersCreate(generics.CreateAPIView):
    queryset = Practitioners.objects.all()
    serializer_class = PractitionersSerializer
    permission_classes = [Is_Vet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class PractitionersList(generics.ListAPIView):
    serializer_class = PractitionersSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        user = self.request.user

        if user.is_vet_officer:
            return Practitioners.objects.filter(user=user)
        if user.is_official:
            return Practitioners.objects.filter(assigned_to_official=user)

class PractitionersUpdate(generics.UpdateAPIView):
    serializer_class = PractitionersSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        return Practitioners.objects.filter(user=self.request.user)
class PractitionersDelete(generics.DestroyAPIView):
    serializer_class = PractitionersSerializer
    permission_classes = [Is_Vet]

    def get_queryset(self):
        return Practitioners.objects.filter(user=self.request.user)

class MilkCollectionClerkCreate(generics.CreateAPIView):
    queryset = MilkCollectionClerk.objects.all()
    serializer_class = MilkCollectionClerkSerializer
    permission_classes = [Is_Vet | Is_Official | Is_Coop]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class MilkCollectionClerkList(generics.ListAPIView):
    serializer_class = MilkCollectionClerkSerializer
    permission_classes = [Is_Vet | Is_Official | Is_Coop|Is_Farmer]

    def get_queryset(self):
        user = self.request.user

        # Cooperative users see their own records
        if user.is_cooperative:
            return MilkCollectionClerk.objects.filter(
                user=user
            ).order_by("-id")

        # Officials see all records
        if user.is_official:
            return MilkCollectionClerk.objects.all().order_by("-id")

        # Farmers see records assigned to their user ID
        return MilkCollectionClerk.objects.filter(
            assigned_to_id=user.id
        ).order_by("-id")
class MilkCollectionClerkUpdate(generics.UpdateAPIView):
    serializer_class = MilkCollectionClerkSerializer
    permission_classes = [Is_Vet | Is_Official]

    def get_queryset(self):
        return MilkCollectionClerk.objects.filter(user=self.request.user)
class MilkCollectionClerkDelete(generics.DestroyAPIView):
    serializer_class = MilkCollectionClerkSerializer
    permission_classes =[Is_Vet | Is_Official]

    def get_queryset(self):
        return MilkCollectionClerk.objects.filter(user=self.request.user)


#Sales

class CashSalesCreate(generics.CreateAPIView):
    queryset = CashSales.objects.all()
    serializer_class = CashSalesSerializer
    permission_classes = [Is_Vet|Is_Agrovet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CashSalesList(generics.ListAPIView):
    serializer_class = CashSalesSerializer
    permission_classes = [Is_Vet|Is_Agrovet]

    def get_queryset(self):
        user = self.request.user
        if user.is_agrovet:
            return CashSales.objects.filter(user=user)
        if user.is_vet_officer:
            return CashSales.objects.all()
        return CashSales.objects.filter(user=user)  # Fallback protection


class CashSalesUpdate(generics.UpdateAPIView):
    serializer_class = CashSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return CashSales.objects.filter(user=self.request.user)


class CashSalesDelete(generics.DestroyAPIView):
    serializer_class = CashSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return CashSales.objects.filter(user=self.request.user)


# =========================================================================
# 2. INVOICE SALES API VIEWS
# =========================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVetOrOfficial])
def invoice_filter(request):
    try:
        user = request.user

        # 🧑‍⚕️ If vet officer: show invoices they created/assigned
        if getattr(user, 'is_vet_officer', False):
            queryset = Invoice.objects.filter(user=user)
            user_type = "vet_officer"

        # 🏛️ If official: show invoices assigned to them (or adjust based on your role logic)
        elif getattr(user, 'is_official', False):
            queryset = Invoice.objects.filter(assigned_to=user)
            user_type = "official"
        else:
            return Response(
                {"error": "You do not have access to these records."},
                status=403
            )

        # Annotate usernames for display convenience
        records = queryset.annotate(
            assigned_to_username=F("assigned_to__username"),
            user_username=F("user__username")
        ).values(
            "id",
            "date_of_invoice",
            "invoice_category",
            "previous_amount",
            "total_amount_due",
            "farmer_name",
            "assigned_to_username",
            "user_username"
        )

        # Calculate totals dynamically across the filtered queryset
        totals = queryset.aggregate(
            total_previous=Sum('previous_amount'),
            total_due=Sum('total_amount_due')
        )

        return Response({
            "user_type": user_type,
            "records": list(records),
            "sum_previous_amount": totals['total_previous'] or 0,
            "sum_total_amount_due": totals['total_due'] or 0,
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )
class InvoiceSalesCreate(generics.CreateAPIView):
    queryset = InvoiceSales.objects.all()
    serializer_class = InvoiceSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet ]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InvoiceSalesList(generics.ListAPIView):
    serializer_class = InvoiceSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        user = self.request.user
        if user.is_agrovet:
            return InvoiceSales.objects.filter(user=user)
        if user.is_vet_officer:
            return InvoiceSales.objects.all()
        return InvoiceSales.objects.filter(user=user)


class InvoiceSalesUpdate(generics.UpdateAPIView):
    serializer_class = InvoiceSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return InvoiceSales.objects.filter(user=self.request.user)


class InvoiceSalesDelete(generics.DestroyAPIView):
    serializer_class = InvoiceSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return InvoiceSales.objects.filter(user=self.request.user)


# =========================================================================
# 3. CREDIT SALES API VIEWS
# =========================================================================

class CreditSalesCreate(generics.CreateAPIView):
    queryset = CreditSales.objects.all()
    serializer_class = CreditSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CreditSalesList(generics.ListAPIView):
    serializer_class = CreditSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        user = self.request.user
        if user.is_agrovet:
            return CreditSales.objects.filter(user=user)
        if user.is_vet_officer:
            return CreditSales.objects.all()
        return CreditSales.objects.filter(user=user)


class CreditSalesUpdate(generics.UpdateAPIView):
    serializer_class = CreditSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return CreditSales.objects.filter(user=self.request.user)


class CreditSalesDelete(generics.DestroyAPIView):
    serializer_class = CreditSalesSerializer
    permission_classes = [Is_Vet | Is_Agrovet ]

    def get_queryset(self):
        return CreditSales.objects.filter(user=self.request.user)


# =========================================================================
# 4. INVOICE PAYMENTS API VIEWS
# =========================================================================
class InvoicePaymentsCreate(generics.CreateAPIView):
    queryset = InvoicePayments.objects.all()
    serializer_class = InvoicePaymentsSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InvoicePaymentsList(generics.ListAPIView):
    serializer_class = InvoicePaymentsSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        user = self.request.user
        if user.is_agrovet:
            return InvoicePayments.objects.filter(user=user)
        if user.is_vet_officer:
            return InvoicePayments.objects.all()
        return InvoicePayments.objects.filter(user=user)


class InvoicePaymentsUpdate(generics.UpdateAPIView):
    serializer_class = InvoicePaymentsSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return InvoicePayments.objects.filter(user=self.request.user)


class InvoicePaymentsDelete(generics.DestroyAPIView):
    serializer_class = InvoicePaymentsSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return InvoicePayments.objects.filter(user=self.request.user)


# =========================================================================
# 5. PETTY CASH EXPENSES API VIEWS
# =========================================================================
class PettyCashExpensesCreate(generics.CreateAPIView):
    queryset = PettyCashExpenses.objects.all()
    serializer_class = PettyCashExpensesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PettyCashExpensesList(generics.ListAPIView):
    serializer_class = PettyCashExpensesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        user = self.request.user
        if user.is_agrovet:
            return PettyCashExpenses.objects.filter(user=user)
        if user.is_vet_officer:
            return PettyCashExpenses.objects.all()
        return PettyCashExpenses.objects.filter(user=user)


class PettyCashExpensesUpdate(generics.UpdateAPIView):
    serializer_class = PettyCashExpensesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return PettyCashExpenses.objects.filter(user=self.request.user)


class PettyCashExpensesDelete(generics.DestroyAPIView):
    serializer_class = PettyCashExpensesSerializer
    permission_classes = [Is_Vet | Is_Agrovet]

    def get_queryset(self):
        return PettyCashExpenses.objects.filter(user=self.request.user)
    
# =========================================================================
# 1. LAYER FLOCK IDENTIFICATION
# =========================================================================

class LayerFlockIdentificationCreate(generics.CreateAPIView):
    queryset = LayerFlockIdentification.objects.all()
    serializer_class = LayerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerFlockIdentificationList(generics.ListAPIView):
    serializer_class = LayerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerFlockIdentification.objects.filter(user=self.request.user)

class LayerFlockIdentificationUpdate(generics.UpdateAPIView):
    serializer_class = LayerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerFlockIdentification.objects.filter(user=self.request.user)

class LayerFlockIdentificationDelete(generics.DestroyAPIView):
    serializer_class = LayerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerFlockIdentification.objects.filter(user=self.request.user)


# =========================================================================
# 2. LAYER DAILY EGG PRODUCTION
# =========================================================================
@json_login_required
def layer_daily_egg_production(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerDailyEggProductionCreate(generics.CreateAPIView):
    queryset = LayerDailyEggProduction.objects.all()
    serializer_class = LayerDailyEggProductionSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerDailyEggProductionList(generics.ListAPIView):
    serializer_class = LayerDailyEggProductionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerDailyEggProduction.objects.filter(flock__user=self.request.user)

class LayerDailyEggProductionUpdate(generics.UpdateAPIView):
    serializer_class = LayerDailyEggProductionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerDailyEggProduction.objects.filter(flock__user=self.request.user)

class LayerDailyEggProductionDelete(generics.DestroyAPIView):
    serializer_class = LayerDailyEggProductionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerDailyEggProduction.objects.filter(flock__user=self.request.user)


# =========================================================================
# 3. LAYER FEED RECORD
# =========================================================================
@json_login_required
def layer_feed_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerFeedRecordCreate(generics.CreateAPIView):
    queryset = LayerFeedRecord.objects.all()
    serializer_class = LayerFeedRecordSerializer
    permission_classes = [Is_Farmer]

    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class LayerFeedRecordList(generics.ListAPIView):
    serializer_class = LayerFeedRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerFeedRecord.objects.filter(flock__user=self.request.user)

class LayerFeedRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerFeedRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerFeedRecord.objects.filter(flock__user=self.request.user)

class LayerFeedRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerFeedRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerFeedRecord.objects.filter(flock__user=self.request.user)


# =========================================================================
# 4. LAYER MORTALITY RECORD
# =========================================================================
@json_login_required
def layer_mortality_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerMortalityRecordCreate(generics.CreateAPIView):
    queryset = LayerMortalityRecord.objects.all()
    serializer_class = LayerMortalityRecordSerializer
    permission_classes = [Is_Farmer]

    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerMortalityRecordList(generics.ListAPIView):
    serializer_class = LayerMortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerMortalityRecord.objects.filter(user=self.request.user)

class LayerMortalityRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerMortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerMortalityRecord.objects.filter(user=self.request.user)

class LayerMortalityRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerMortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerMortalityRecord.objects.filter(user=self.request.user)


# =========================================================================
# 5. LAYER CULLING RECORD
# =========================================================================
@json_login_required
def layer_culling_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerCullingRecordCreate(generics.CreateAPIView):
    queryset = LayerCullingRecord.objects.all()
    serializer_class = LayerCullingRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerCullingRecordList(generics.ListAPIView):
    serializer_class = LayerCullingRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerCullingRecord.objects.filter(flock__user=self.request.user)

class LayerCullingRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerCullingRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerCullingRecord.objects.filter(flock__user=self.request.user)

class LayerCullingRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerCullingRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerCullingRecord.objects.filter(flock__user=self.request.user)


# =========================================================================
# 6. LAYER VACCINATION RECORD
# =========================================================================
@json_login_required
def layer_vaccination_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerVaccinationRecordCreate(generics.CreateAPIView):
    queryset = LayerVaccinationRecord.objects.all()
    serializer_class = LayerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerVaccinationRecordList(generics.ListAPIView):
    serializer_class = LayerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerVaccinationRecord.objects.filter(user=self.request.user)

class LayerVaccinationRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerVaccinationRecord.objects.filter(user=self.request.user)

class LayerVaccinationRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerVaccinationRecord.objects.filter(user=self.request.user)


# =========================================================================
# 7. LAYER TREATMENT RECORD
# =========================================================================
@json_login_required
def layer_treatment_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerTreatmentRecordCreate(generics.CreateAPIView):
    queryset = LayerTreatmentRecord.objects.all()
    serializer_class = LayerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerTreatmentRecordList(generics.ListAPIView):
    serializer_class = LayerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerTreatmentRecord.objects.filter(user=self.request.user)

class LayerTreatmentRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerTreatmentRecord.objects.filter(user=self.request.user)

class LayerTreatmentRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerTreatmentRecord.objects.filter(user=self.request.user)


# =========================================================================
# 8. LAYER SALES RECORD
# =========================================================================
@json_login_required
def layer_sales_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerSalesRecordCreate(generics.CreateAPIView):
    queryset = LayerSalesRecord.objects.all()
    serializer_class = LayerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerSalesRecordList(generics.ListAPIView):
    serializer_class = LayerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerSalesRecord.objects.filter(user=self.request.user)

class LayerSalesRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerSalesRecord.objects.filter(user=self.request.user)

class LayerSalesRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerSalesRecord.objects.filter(user=self.request.user)


# =========================================================================
# 9. LAYER INCOME RECORD
# =========================================================================
@json_login_required
def layer_income_record(request):
    return JsonResponse({
        "flocks": safe_values(LayerFlockIdentification.objects.filter(user=request.user)),
    })


class LayerIncomeRecordCreate(generics.CreateAPIView):
    queryset = LayerIncomeRecord.objects.all()
    serializer_class = LayerIncomeRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerIncomeRecordList(generics.ListAPIView):
    serializer_class = LayerIncomeRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerIncomeRecord.objects.filter(user=self.request.user)

class LayerIncomeRecordUpdate(generics.UpdateAPIView):
    serializer_class = LayerIncomeRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerIncomeRecord.objects.filter(user=self.request.user)

class LayerIncomeRecordDelete(generics.DestroyAPIView):
    serializer_class = LayerIncomeRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerIncomeRecord.objects.filter(user=self.request.user)


# =========================================================================
# 10. LAYER BIOSECURITY AND VISITORS LOG
# =========================================================================

class LayerBiosecurityAndVisitorsLogCreate(generics.CreateAPIView):
    queryset = LayerBiosecurityAndVisitorsLog.objects.all()
    serializer_class = LayerBiosecurityAndVisitorsLogSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LayerBiosecurityAndVisitorsLogList(generics.ListAPIView):
    serializer_class = LayerBiosecurityAndVisitorsLogSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerBiosecurityAndVisitorsLog.objects.filter(user=self.request.user)

class LayerBiosecurityAndVisitorsLogUpdate(generics.UpdateAPIView):
    serializer_class = LayerBiosecurityAndVisitorsLogSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerBiosecurityAndVisitorsLog.objects.filter(user=self.request.user)

class LayerBiosecurityAndVisitorsLogDelete(generics.DestroyAPIView):
    serializer_class = LayerBiosecurityAndVisitorsLogSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LayerBiosecurityAndVisitorsLog.objects.filter(user=self.request.user)

# =========================================================================
# 1. BROILER FLOCK IDENTIFICATION
# =========================================================================

class BroilerFlockIdentificationCreate(generics.CreateAPIView):
    queryset = BroilerFlockIdentification.objects.all()
    serializer_class = BroilerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerFlockIdentificationList(generics.ListAPIView):
    serializer_class = BroilerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerFlockIdentification.objects.filter(user=self.request.user)

class BroilerFlockIdentificationUpdate(generics.UpdateAPIView):
    serializer_class = BroilerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerFlockIdentification.objects.filter(user=self.request.user)

class BroilerFlockIdentificationDelete(generics.DestroyAPIView):
    serializer_class = BroilerFlockIdentificationSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerFlockIdentification.objects.filter(user=self.request.user)


# =========================================================================
# 2. BROILER DAILY MORTALITY
# =========================================================================
@json_login_required
def broiler_daily_mortality(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
        "morts": safe_values(BroilerDailyMortality.objects.filter(user=request.user)),
    })


class BroilerDailyMortalityCreate(generics.CreateAPIView):
    queryset = BroilerDailyMortality.objects.all()
    serializer_class = BroilerDailyMortalitySerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerDailyMortalityList(generics.ListAPIView):
    serializer_class = BroilerDailyMortalitySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerDailyMortality.objects.filter(user=self.request.user)

class BroilerDailyMortalityUpdate(generics.UpdateAPIView):
    serializer_class = BroilerDailyMortalitySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerDailyMortality.objects.filter(user=self.request.user)

class BroilerDailyMortalityDelete(generics.DestroyAPIView):
    serializer_class = BroilerDailyMortalitySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerDailyMortality.objects.filter(user=self.request.user)


# =========================================================================
# 3. BROILER FEED CONSUMPTION
# =========================================================================
@json_login_required
def broiler_feed_consumption(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerFeedConsumptionCreate(generics.CreateAPIView):
    queryset = BroilerFeedConsumption.objects.all()
    serializer_class = BroilerFeedConsumptionSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerFeedConsumptionList(generics.ListAPIView):
    serializer_class = BroilerFeedConsumptionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerFeedConsumption.objects.filter(user=self.request.user)

class BroilerFeedConsumptionUpdate(generics.UpdateAPIView):
    serializer_class = BroilerFeedConsumptionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerFeedConsumption.objects.filter(user=self.request.user)

class BroilerFeedConsumptionDelete(generics.DestroyAPIView):
    serializer_class = BroilerFeedConsumptionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerFeedConsumption.objects.filter(user=self.request.user)


# =========================================================================
# 4. BROILER TREATMENT RECORD
# =========================================================================
@json_login_required
def broiler_treatment_record(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerTreatmentRecordCreate(generics.CreateAPIView):
    queryset = BroilerTreatmentRecord.objects.all()
    serializer_class = BroilerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerTreatmentRecordList(generics.ListAPIView):
    serializer_class = BroilerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerTreatmentRecord.objects.filter(user=self.request.user)

class BroilerTreatmentRecordUpdate(generics.UpdateAPIView):
    serializer_class = BroilerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerTreatmentRecord.objects.filter(user=self.request.user)

class BroilerTreatmentRecordDelete(generics.DestroyAPIView):
    serializer_class = BroilerTreatmentRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerTreatmentRecord.objects.filter(user=self.request.user)


# =========================================================================
# 5. BROILER VACCINATION RECORD
# =========================================================================
@json_login_required
def broiler_vaccination_record(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerVaccinationRecordCreate(generics.CreateAPIView):
    queryset = BroilerVaccinationRecord.objects.all()
    serializer_class = BroilerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerVaccinationRecordList(generics.ListAPIView):
    serializer_class = BroilerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerVaccinationRecord.objects.filter(user=self.request.user)

class BroilerVaccinationRecordUpdate(generics.UpdateAPIView):
    serializer_class = BroilerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerVaccinationRecord.objects.filter(user=self.request.user)

class BroilerVaccinationRecordDelete(generics.DestroyAPIView):
    serializer_class = BroilerVaccinationRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerVaccinationRecord.objects.filter(user=self.request.user)


# =========================================================================
# 6. BROILER GROWTH PERFORMANCE
# =========================================================================
@json_login_required
def broiler_growth_performance(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerGrowthPerformanceCreate(generics.CreateAPIView):
    queryset = BroilerGrowthPerformance.objects.all()
    serializer_class = BroilerGrowthPerformanceSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerGrowthPerformanceList(generics.ListAPIView):
    serializer_class = BroilerGrowthPerformanceSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerGrowthPerformance.objects.filter(user=self.request.user)

class BroilerGrowthPerformanceUpdate(generics.UpdateAPIView):
    serializer_class = BroilerGrowthPerformanceSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerGrowthPerformance.objects.filter(user=self.request.user)

class BroilerGrowthPerformanceDelete(generics.DestroyAPIView):
    serializer_class = BroilerGrowthPerformanceSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerGrowthPerformance.objects.filter(user=self.request.user)


# =========================================================================
# 7. BROILER ENVIRONMENTAL RECORD
# =========================================================================
@json_login_required
def broiler_environmental_record(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerEnvironmentalRecordCreate(generics.CreateAPIView):
    queryset = BroilerEnvironmentalRecord.objects.all()
    serializer_class = BroilerEnvironmentalRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerEnvironmentalRecordList(generics.ListAPIView):
    serializer_class = BroilerEnvironmentalRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerEnvironmentalRecord.objects.filter(user=self.request.user)

class BroilerEnvironmentalRecordUpdate(generics.UpdateAPIView):
    serializer_class = BroilerEnvironmentalRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerEnvironmentalRecord.objects.filter(user=self.request.user)

class BroilerEnvironmentalRecordDelete(generics.DestroyAPIView):
    serializer_class = BroilerEnvironmentalRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerEnvironmentalRecord.objects.filter(user=self.request.user)


# =========================================================================
# 8. BROILER WATER CONSUMPTION
# =========================================================================
@json_login_required
def broiler_water_consumption(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerWaterConsumptionCreate(generics.CreateAPIView):
    queryset = BroilerWaterConsumption.objects.all()
    serializer_class = BroilerWaterConsumptionSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerWaterConsumptionList(generics.ListAPIView):
    serializer_class = BroilerWaterConsumptionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerWaterConsumption.objects.filter(user=self.request.user)

class BroilerWaterConsumptionUpdate(generics.UpdateAPIView):
    serializer_class = BroilerWaterConsumptionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerWaterConsumption.objects.filter(user=self.request.user)

class BroilerWaterConsumptionDelete(generics.DestroyAPIView):
    serializer_class = BroilerWaterConsumptionSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerWaterConsumption.objects.filter(user=self.request.user)


# =========================================================================
# 9. BROILER SALES RECORD
# =========================================================================
@json_login_required
def broiler_sales_record(request):
    return JsonResponse({
        "flocks": safe_values(BroilerFlockIdentification.objects.filter(user=request.user)),
    })


class BroilerSalesRecordCreate(generics.CreateAPIView):
    queryset = BroilerSalesRecord.objects.all()
    serializer_class = BroilerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BroilerSalesRecordList(generics.ListAPIView):
    serializer_class = BroilerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerSalesRecord.objects.filter(user=self.request.user)

class BroilerSalesRecordUpdate(generics.UpdateAPIView):
    serializer_class = BroilerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerSalesRecord.objects.filter(user=self.request.user)

class BroilerSalesRecordDelete(generics.DestroyAPIView):
    serializer_class = BroilerSalesRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return BroilerSalesRecord.objects.filter(user=self.request.user)


class EmployeeRecordCreate(generics.CreateAPIView):
    queryset = EmployeeRecord.objects.all()
    serializer_class = EmployeeRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmployeeRecordList(generics.ListAPIView):
    serializer_class = EmployeeRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return EmployeeRecord.objects.filter(user=self.request.user)


class EmployeeRecordUpdate(generics.UpdateAPIView):
    serializer_class = EmployeeRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return EmployeeRecord.objects.filter(user=self.request.user)


class EmployeeRecordDelete(generics.DestroyAPIView):
    serializer_class = EmployeeRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return EmployeeRecord.objects.filter(user=self.request.user)
    

@json_login_required
def salary_record(request):
    return JsonResponse({
        "employees": safe_values(Employee.objects.filter(user=request.user)),
    })


class SalaryRecordCreate(generics.CreateAPIView):
    queryset = SalaryRecord.objects.all()
    serializer_class = SalaryRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            processed_by=self.request.user
        )


class SalaryRecordList(generics.ListAPIView):
    serializer_class = SalaryRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return SalaryRecord.objects.filter(user=self.request.user)


class SalaryRecordUpdate(generics.UpdateAPIView):
    serializer_class = SalaryRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return SalaryRecord.objects.filter(user=self.request.user)


class SalaryRecordDelete(generics.DestroyAPIView):
    serializer_class = SalaryRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return SalaryRecord.objects.filter(user=self.request.user)
@json_login_required
def farm_visit_record(request):
    return JsonResponse({
        "farm_visits": safe_values(FarmVisit.objects.filter(user_id=request.user.id)),
    })


# API Views
class FarmVisitCreate(generics.CreateAPIView):
    queryset = FarmVisit.objects.all()
    serializer_class = FarmVisitSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FarmVisitList(generics.ListAPIView):
    serializer_class = FarmVisitSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FarmVisit.objects.filter(user=self.request.user)


class FarmVisitUpdate(generics.UpdateAPIView):
    serializer_class = FarmVisitSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FarmVisit.objects.filter(user=self.request.user)


class FarmVisitDelete(generics.DestroyAPIView):
    serializer_class = FarmVisitSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FarmVisit.objects.filter(user=self.request.user)
    
# Template View
@json_login_required
def drug_inventory_record(request):
    return JsonResponse({
        "drugs": safe_values(DrugInventory.objects.filter(user=request.user)),
    })


# API Views
class DrugInventoryCreate(generics.CreateAPIView):
    queryset = DrugInventory.objects.all()
    serializer_class = DrugInventorySerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DrugInventoryList(generics.ListAPIView):
    serializer_class = DrugInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return DrugInventory.objects.filter(user=self.request.user)


class DrugInventoryUpdate(generics.UpdateAPIView):
    serializer_class = DrugInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return DrugInventory.objects.filter(user=self.request.user)


class DrugInventoryDelete(generics.DestroyAPIView):
    serializer_class = DrugInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return DrugInventory.objects.filter(user=self.request.user)

# Template View
@json_login_required
def feed_inventory_record(request):
    return JsonResponse({
        "feeds": safe_values(FeedInventory.objects.filter(user=request.user)),
    })


# API Views
class FeedInventoryCreate(generics.CreateAPIView):
    queryset = FeedInventory.objects.all()
    serializer_class = FeedInventorySerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FeedInventoryList(generics.ListAPIView):
    serializer_class = FeedInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FeedInventory.objects.filter(user=self.request.user)


class FeedInventoryUpdate(generics.UpdateAPIView):
    serializer_class = FeedInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FeedInventory.objects.filter(user=self.request.user)


class FeedInventoryDelete(generics.DestroyAPIView):
    serializer_class = FeedInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FeedInventory.objects.filter(user=self.request.user)
    
# Template View
@json_login_required
def livestock_record(request):
    return JsonResponse({
        "livestock_items": safe_values(Livestock.objects.filter(user=request.user)),
    })


# API Views
class LivestockInventoryCreate(generics.CreateAPIView):
    queryset = LivestockInventory.objects.all()
    serializer_class = LivestockInventorySerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LivestockInventoryList(generics.ListAPIView):
    serializer_class = LivestockInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LivestockInventory.objects.filter(user=self.request.user)


class LivestockInventoryUpdate(generics.UpdateAPIView):
    serializer_class = LivestockInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LivestockInventory.objects.filter(user=self.request.user)


class LivestockInventoryDelete(generics.DestroyAPIView):
    serializer_class = LivestockInventorySerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LivestockInventory.objects.filter(user=self.request.user)


# Template View
@json_login_required
def asset_record(request):
    return JsonResponse({
        "assets": safe_values(Asset.objects.filter(user=request.user)),
    })


# API Views
class AssetCreate(generics.CreateAPIView):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AssetList(generics.ListAPIView):
    serializer_class = AssetSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return Asset.objects.filter(user=self.request.user)


class AssetUpdate(generics.UpdateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return Asset.objects.filter(user=self.request.user)


class AssetDelete(generics.DestroyAPIView):
    serializer_class = AssetSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return Asset.objects.filter(user=self.request.user)

@json_login_required
def fish_record(request):
    return JsonResponse({
        "fish_list": safe_values(Fish.objects.filter(user=request.user)),
    })


@json_login_required
def feeding_record(request):
    return JsonResponse({
        "feeding_records": safe_values(FeedingRecord.objects.filter(user=request.user)),
    })


@json_login_required
def mortality_record(request):
    return JsonResponse({
        "mortality_records": safe_values(MortalityRecord.objects.filter(user=request.user)),
    })


@json_login_required
def growth_monitoring_record(request):
    return JsonResponse({
        "growth_records": safe_values(GrowthMonitoring.objects.filter(user=request.user)),
    })


# ==========================================
# API Views: Fish
# ==========================================

class FishCreate(generics.CreateAPIView):
    queryset = Fish.objects.all()
    serializer_class = FishSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FishList(generics.ListAPIView):
    serializer_class = FishSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return Fish.objects.filter(user=self.request.user)


class FishUpdate(generics.UpdateAPIView):
    serializer_class = FishSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return Fish.objects.filter(user=self.request.user)


class FishDelete(generics.DestroyAPIView):
    serializer_class = FishSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return Fish.objects.filter(user=self.request.user)


# ==========================================
# API Views: Feeding Record
# ==========================================

class FeedingRecordCreate(generics.CreateAPIView):
    queryset = FeedingRecord.objects.all()
    serializer_class = FeedingRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FeedingRecordList(generics.ListAPIView):
    serializer_class = FeedingRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FeedingRecord.objects.filter(user=self.request.user)


class FeedingRecordUpdate(generics.UpdateAPIView):
    serializer_class = FeedingRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FeedingRecord.objects.filter(user=self.request.user)


class FeedingRecordDelete(generics.DestroyAPIView):
    serializer_class = FeedingRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return FeedingRecord.objects.filter(user=self.request.user)


# ==========================================
# API Views: Mortality Record
# ==========================================

class MortalityRecordCreate(generics.CreateAPIView):
    queryset = MortalityRecord.objects.all()
    serializer_class = MortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MortalityRecordList(generics.ListAPIView):
    serializer_class = MortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return MortalityRecord.objects.filter(user=self.request.user)


class MortalityRecordUpdate(generics.UpdateAPIView):
    serializer_class = MortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return MortalityRecord.objects.filter(user=self.request.user)


class MortalityRecordDelete(generics.DestroyAPIView):
    serializer_class = MortalityRecordSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return MortalityRecord.objects.filter(user=self.request.user)


# ==========================================
# API Views: Growth Monitoring
# ==========================================

class GrowthMonitoringCreate(generics.CreateAPIView):
    queryset = GrowthMonitoring.objects.all()
    serializer_class = GrowthMonitoringSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GrowthMonitoringList(generics.ListAPIView):
    serializer_class = GrowthMonitoringSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return GrowthMonitoring.objects.filter(user=self.request.user)


class GrowthMonitoringUpdate(generics.UpdateAPIView):
    serializer_class = GrowthMonitoringSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return GrowthMonitoring.objects.filter(user=self.request.user)


class GrowthMonitoringDelete(generics.DestroyAPIView):
    serializer_class = GrowthMonitoringSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return GrowthMonitoring.objects.filter(user=self.request.user)


@json_login_required
def trade_record(request):
    return JsonResponse({
        "trades_list": safe_values(LivestockTrade.objects.all()),
    })


class LivestockTradeCreate(generics.CreateAPIView):
    queryset = LivestockTrade.objects.all()
    serializer_class = LivestockTradeSerializer
    permission_classes = [Is_Farmer]

    def perform_create(self, serializer):
        serializer.save()


class LivestockTradeList(generics.ListAPIView):
    serializer_class = LivestockTradeSerializer
    permission_classes = []

    def get_queryset(self):
        return LivestockTrade.objects.all()


class LivestockTradeUpdate(generics.UpdateAPIView):
    serializer_class = LivestockTradeSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LivestockTrade.objects.all()


class LivestockTradeDelete(generics.DestroyAPIView):
    serializer_class = LivestockTradeSerializer
    permission_classes = [Is_Farmer]

    def get_queryset(self):
        return LivestockTrade.objects.all()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_menu_access(request):
    """
    GET /api/pos/menu-permissions/mine/
    What the sidebar needs for the logged-in user. Admins always use the built-in
    admin menu, so they can never lock themselves out.
    """
    user = request.user
    if IsAdminUserCustom._check_admin(user):
        return Response({"is_admin": True, "configured": False, "keys": []})
    role_id = getattr(user, "role_id", None)
    rec = RoleMenuPermission.objects.filter(role_id=role_id).first() if role_id else None
    return Response({
        "is_admin": False,
        "configured": rec is not None,
        "keys": rec.menu_keys if rec else [],
    })


@api_view(["GET", "PUT"])
@permission_classes([IsAdminOnly])
def menu_permissions(request):
    """
    GET  /api/pos/menu-permissions/
         -> { roles: [...], permissions: { "<role_id>": ["pos", "sales", ...] } }
         (only roles an admin has customised appear in `permissions`)

    PUT  /api/pos/menu-permissions/
         body { "role": <id>, "menu_keys": ["pos", "sales"] }  -> save this role's menu
         body { "role": <id>, "menu_keys": null }              -> reset the role to built-in defaults
    """
    from users.models import Roles, ActivityLog

    if request.method == "GET":
        # HR-only roles (requires_login=False, e.g. cleaners) never log in, so they have no menu to configure.
        roles = list(
            Roles.objects.filter(requires_login=True).values("id", "role_name", "role_description", "requires_login")
        )
        permissions = {str(p.role_id): p.menu_keys for p in RoleMenuPermission.objects.all()}
        return Response({"roles": roles, "permissions": permissions})

    role = get_object_or_404(Roles, pk=request.data.get("role"))
    if "admin" in (role.role_name or "").lower():
        return Response({"error": "Administrator access is fixed and can't be changed."},
                        status=status.HTTP_400_BAD_REQUEST)
    if not role.requires_login:
        return Response({"error": "This is an HR-only role. It has no system login, so there is no menu to set."},
                        status=status.HTTP_400_BAD_REQUEST)
    if "menu_keys" not in request.data:
        return Response({"error": "menu_keys is required (use null to reset to defaults)."},
                        status=status.HTTP_400_BAD_REQUEST)

    keys = request.data.get("menu_keys")

    if keys is None:
        RoleMenuPermission.objects.filter(role=role).delete()
        ActivityLog.log("menu_access_reset", user=request.user, entity="Roles", entity_id=role.id,
                        detail=f"Reset menu access for role {role.role_name} to defaults", request=request)
        return Response({"role": role.id, "configured": False, "menu_keys": []})

    if not isinstance(keys, list) or not all(isinstance(k, str) and len(k) <= 64 for k in keys):
        return Response({"error": "menu_keys must be a list of menu key strings."},
                        status=status.HTTP_400_BAD_REQUEST)

    keys = sorted({k.strip() for k in keys if k.strip()})
    RoleMenuPermission.objects.update_or_create(
        role=role, defaults={"menu_keys": keys, "updated_by": request.user}
    )
    ActivityLog.log("menu_access_updated", user=request.user, entity="Roles", entity_id=role.id,
                    detail=f"Set menu access for role {role.role_name}: {len(keys)} items", request=request)
    return Response({"role": role.id, "configured": True, "menu_keys": keys})