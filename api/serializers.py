from rest_framework import serializers
from django.db.models import Sum
from datetime import timedelta, date
from .models import *
from django.contrib.auth import get_user_model
from django.db import transaction




class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'role_name', 'role_description']


class UserBasicSerializer(serializers.ModelSerializer):
    role = RoleSerializer(many=False, read_only=True)
   

    class Meta:
        model = User
        fields = ['id', 'username', 'firstname', 'lastname', 'email', 'phone', 'role', 'date_joined', 'is_active', 'is_admin']

class PregnancyMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = PregnancyMonitoring
        fields = [
            'id', 'user', 'name', 'reg_no', 'date_of_ai','exp_heat_date','repeat_heat_date',
            'first_preg_diag_date','steaming_up_date', 'expected_dob' 
            
        ]
        read_only_fields = ['exp_heat_date','repeat_heat_date', 'first_preg_diag_date', 'steaming_up_date', 'expected_dob']

class HeatSignMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeatSignMonitoring
        fields = [
            'id',
            'user',
            'name',
            'reg_no',
            'status',
            'date_of_heat_sign',
            'date_of_repeat_monitoring',
            'exp_date_of_repeated_heat',
            'reason_skip_monitoring'
        ]
        read_only_fields = ['date_of_repeat_monitoring', 'exp_date_of_repeated_heat']
class AnimalSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnimalSale
        fields = [
            'id',
            'user',
            'number_sold',
            'name',
            'reg_no',
            'date_sold',
            'breed',
            'age',
            'sex',
            'weight',
            'selling_price',
            'reason',
            'comment',
        ]

class LivestockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Livestock
        fields = [
            'id',
            'user',
            'animal_type',
            'breed_category',
            'date_added',
            'no_of_animals',
            'no_of_males',
            'no_of_females',
            'no_of_adults',
            'no_of_young',
            'no_of_dead',
            'reason_for_death',
            'comment'
        ]

class NewAnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewAnimal
        fields = [
            'id',
            'user',
            'name',
            'reg_no',
            'source',
            'farmer_name',
            'animal_type',
            'breed',
            'breeding_level',
            'defect',
            'defect_reason',
            'animal_color',
            'market_value',
            'medical_history',
            'assessed_by_vet',
            'insured',
            'insuring_company',
            'date_added'
        ]

class CullingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Culling
        fields = [
            'id',
            'user', 
            'name', 
            'reg_no', 
            'age', 
            'gender',
            'animal_type',
            'breed', 
            'culling_method', 
            'no_of_culled', 
            'culling_reason', 
            'culling_date', 
            'culling_price', 
            'comment'
        ]

class DeadAnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeadAnimal
        fields = [
            'id',
            'user', 
            'name', 
            'farm_name', 
            'no_of_affected', 
            'gender', 
            'breed', 
            'sickness_period', 
            'cause_of_death', 
            'death_date', 
            'death_time', 
            'signs_before_death', 
            'postmortem_by_vet', 
            'safety_precaution', 
            'comment'
        ]

class CalfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calf
        fields = [
            'id',
            'user',
            'name_given',
            'registration_number',
            'dam_details',
            'birth_date',
            'breed',
            'gender',
            'sire_details',
            'color',
            'birth_weight',
            'medical_conditions',
            'registration_date',
            'expected_weaning',
            'breeding_level',
            'comments'
        ]

class FeedsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feeds
        fields = [
            'id',
            'user',
            'date_of_purchase',
            'feed_type',
            'company',
            'expiry_date',
            'quantity_purchased',
            'trade_name',
            'weight',
            'cost',
            'comment'
        ]


class MineralsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Minerals
        fields = ['id', 'user', 'date_of_purchase', 'mineral_type', 'quantity', 'company', 'expiry_date', 'cost', 'comment']

class VeterinaryBillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VeterinaryBills
        fields = ['id', 'user', 'date_of_billing', 'bill_category', 'amount','amount_billed','balance', 'billing_details', 'comment']
        read_only_fields=['balance']
class ArcharicidesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Archaricides
        fields = ['id', 'user', 'date_of_purchase', 'chemical_name','trade_name','quantity', 'company', 'application_rate', 'expiry_date', 'times_used', 'cost', 'comment']

class DairyEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DairyEquipment
        fields = ['id', 'user', 'name','date_of_purchase', 'quantity', 'equipment_type','model_number', 'company', 'cost', 'source', 'comment']

class DairyHygieneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DairyHygiene
        fields = ['id', 'user','chemical_name','trade_name','date_of_purchase', 'item_purchased', 'company', 'quantity', 'cost', 'expiry_date', 'comment']
class SalariesSerializer(serializers.ModelSerializer):
    employee_name = serializers.SlugRelatedField(queryset=Employees.objects.all(), slug_field='id')
    
    class Meta:
        model = Salaries
        fields = ['id', 'user','employee_name', 'employee_position', 'identification', 'mode_of_payment','bank_account','salary_amount','amount', 'balance', 'payment_date', 'payment_type', 'comment']
        read_only_fields = ['bank_account','balance']
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        employee_instance = Employees.objects.get(id=data['employee_name'])  
        data['employee_names'] = employee_instance.employee_name 
        print(data)
        return data


class LivestockInsuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivestockInsurance
        fields = ['id', 'user', 'number_insured','breed','animal_species','number_insured','company', 'mode_of_payment', 'payment_date', 'total', 'comment']

class VeterinaryDrugsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VeterinaryDrugs
        fields = ['id', 'user','date_of_purchase', 'name', 'category','company','expiry_date', 'strange_condition', 'vet_reg', 'cost', 'comment']

class EmployeesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employees
        fields = [
            'id',
            'user',
            'enrollment_date',
            'employee_name',
            'id_no',
            'phone_no',
            'county',
            'district',
            'village',
            'next_of_kin',
            'next_of_kin_phone_no',
            'chief_name',
            'chief_phone_no',
            'employee_position',
            'salary',
            'payment_method',
            'bank_account',
            'mode_of_employment',
            'contract_rewal_period',
        ]

class LactatingCowSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=1)

    class Meta:
        model = LactatingCow
        fields = ['id', 'user', 'cow_name', 'reg_no', 'sire_details', 'breed',
                  'breeding_level', 'age', 'calving_down_date', 'no_of_calves',
                  'average_daily_milk', 'lactation_stage', 'expected_date_of_drying_off']


class MilkRecordSerializer(serializers.ModelSerializer):
    employee_full_name = serializers.SerializerMethodField()

    class Meta:
        model = MilkRecord
        fields = [
            'id',
            'user',
            'cow_name',
            'employee_name',
            'employee_full_name',
            'date',
            'time_of_milking',
            'quantity'
        ]

    def get_employee_full_name(self, obj):
        if obj.employee_name:
            return getattr(obj.employee_name, 'employee_name', str(obj.employee_name))
        return None                        
class WeeklyMilkRecordSerializer(serializers.ModelSerializer):
    cow_name = serializers.SlugRelatedField(queryset=LactatingCow.objects.all(), slug_field='cow_name')
    
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = WeeklyMilkRecord
        fields = ['id','cow_name',  'week_start_date', 'total_quantity']

    def get_total_quantity(self, obj):
        week_end_date = obj.week_start_date + timedelta(days=6)
        total_quantity = MilkRecord.objects.filter(
            cow_name=obj.cow_name,
            date__range=[obj.week_start_date, week_end_date]
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0.0
        return total_quantity

class DailyMilkRecordSerializer(serializers.ModelSerializer):
    cow_name = serializers.SlugRelatedField(queryset=LactatingCow.objects.all(), slug_field='cow_name')
    
    class Meta:
        model = DailyMilkRecord
        fields = ['id','cow_name', 'date', 'total_quantity']

class MonthlyMilkRecordSerializer(serializers.ModelSerializer):
    cow_name = serializers.SlugRelatedField(queryset=LactatingCow.objects.all(), slug_field='cow_name')
    
    total_quantity = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyMilkRecord
        fields = ['id','cow_name', 'month', 'total_quantity']

    def get_total_quantity(self, obj):
        start_date = obj.month.replace(day=1)
        next_month = start_date.month % 12 + 1
        year = start_date.year if next_month > 1 else start_date.year + 1
        end_date = date(year, next_month, 1) - timedelta(days=1)
        total_quantity = MilkRecord.objects.filter(
            cow_name=obj.cow_name,
            date__range=[start_date, end_date]
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0.0
        return total_quantity

class BuyerSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Buyer
        fields = ['id','user','name', 'category', 'contact','date_of_enrollment','duration_of_supply','payment_mode','agreed_price_per_kg']

class OtherExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherExpense
        fields = ['id', 'date', 'description', 'cost', 'comment']
            
class SalesOfMilkSerializer(serializers.ModelSerializer):
    # accepts the buyer's ID in POST/PATCH/PUT
    buyer = serializers.PrimaryKeyRelatedField(
        queryset=Buyer.objects.all(),
        write_only=True          # hide the numeric ID in the response (optional)
    )
    # shows the buyer's name in GET responses
    buyer_name = serializers.CharField(
        source='buyer.name',
        read_only=True
    )

    class Meta:
        model = SalesOfMilk
        fields = [
            'id',
            'user',
            'date_of_sales',
            'milk_sales_to',
            'buyer',          # ID expected on write
            'buyer_name',     # name returned on read
            'balance',
            'total_cash_received',
            'comment',
        ]


class PaymentsSerializer(serializers.ModelSerializer):
    payment_received_from = serializers.CharField(source='buyer.name', read_only=True)
    buyer = serializers.PrimaryKeyRelatedField(queryset=Buyer.objects.all(), write_only=True)
    category_of_buyer = serializers.ReadOnlyField(source='buyer.category')
    buyer_choices = serializers.SerializerMethodField()
    category_choices = serializers.SerializerMethodField()

    class Meta:
        model = Payments
        fields = [
            'id',
            'user',
            'category',
            'buyer',
            'buyer_choices',
            'category_choices',
            'category_of_buyer',
            'date_of_payment',
            'total_kg_supplied',
            'price_per_kg',
            'total_amount_to_receive',
            'previous_balance',
            'grand_total',
            'amount_received',
            'balance',
            'payment_received_from',
            'payment_received_by',
            'contracts',
            'remarks',
        ]

    def get_buyer_choices(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            buyers = Buyer.objects.filter(user=request.user)
        else:
            buyers = Buyer.objects.none()

        return [{'id': b.id, 'name': b.name, 'category': b.category} for b in buyers]

    def get_category_choices(self, obj):
        return [{'value': key, 'label': val} for key, val in Payments.CATEGORIES]
    
class VeterinaryBillingSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = VeterinaryBilling
        fields = ['id','user','assigned_to', 'billing_category','other_billing_category','total_amount_billed', 'total_paid', 'balance', 'mode_of_payment',
                  'agreed_date', 'payment_plan', 'farmer_name', 'village', 'contact',
                 'signature']
        read_only_fields=['balance']

class DewormingSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = Deworming
        fields = ['id','user','assigned_to', 'species_targeted', 'other','animal_name','no_of_adults', 'no_of_young_ones', 'body_conditions',
                    'deworming_date', 'drug_of_choice', 'parasites', 'withdrawal_period', 'side_effects',
                    'nxt_deworming_date', 'farmer_name', 'village', 'contact',
                    'signature']

class ArtificialInseminationSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    assigned_to_cooperative = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(),required=False,allow_null=True)

    class Meta:
        model = ArtificialInsemination
        fields = [
            'id', 'user', 'assigned_to', 'assigned_to_official','assigned_to_cooperative','assigned_by', 'farm_name', 'species', 'cow_name', 
            'reg_no','animal_status', 'dam_details','sire_details', 'no_of_repeats', 'rab_status', 'abortion_status', 
            'time_of_heat_sign', 'date_of_heat_sign', 'insemination_date', 'insemination_time', 'insemination_status', 
            'semen_type', 'breed_used', 'other_breed', 'bull_name', 'bull_reg_no', 'semen_source', 'other_source', 
            'heat_sign_mtr_date', 'repeat_heat_date', 'first_pd_date', 'expected_delivery_date', 'owners_name', 
            'sub_county', 'ward', 'village', 'contact',  
             'location','signature_stamp'
        ]
        read_only_fields = ['assigned_by', 'heat_sign_mtr_date', 'repeat_heat_date', 'first_pd_date', 'expected_delivery_date']

   

class PregnancyDiagnosisSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = PregnancyDiagnosis
        fields = ['id','user','assigned_to', 'cow_name', 'reg_no', 'category', 'date_of_ai', 'pg_diag_date', 'pd_results',
                  'pd_method', 'positive_pd_months', 'negative_pd_comment', 'pd_nxt_date', 'expctd_delivery_date',
                  'comment', 'owners_name', 'village', 'contact',
                  'signature']

class FarmConsultationSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = FarmConsultation
        fields = ['id','user','assigned_to','visit_date','area_of_interest','other','recommendation', 
                   'manager',  'farmer_name', 'contact', 'village',
                  'signature']

class ReferralSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = Referral
        fields = ['id','user','assigned_to', 'species', 'treatment_duration', 'previous_treatment_state', 'prognosis',
                  'referral_date', 'referral_choice', 
                  'farmer_name', 'village', 'contact']
        
class SurgicalRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = SurgicalRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category_affected',
            'other_livestock_category',
            'name_of_animal',
            'registration_number',
            'sex_of_animal',
            'age_of_animal',
            'nature_of_surgery',
            'type_of_surgery',
            'other_surgery',
            'status_before_operation',
            'pre_operative_management',
            'date_of_operation',
            'post_operation_management',
            'prognosis_of_patient',
            'case_history',
            'comment',
            'owner_name',
            'owner_village',
            'owner_mobile_number',
            'signature',
            
        ]

class SampleCollectionSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = SampleCollection
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category',
            'other_livestock',
            'name_of_animal',
            'registration_number',
            'age_of_animal',
            'sex_of_animal',
            'history_of_animal',
            'clinical_signs_of_animal',
            'type_of_sample_collected',
            'date_of_sampling',
            'sample_storage_condition',
            'means_of_transportation',
            'sample_rating',
            'owner_name',
            'owner_village',
            'owner_mobile_number',
           
           
            'signature',
            
        ]

class SampleProcessingSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = SampleProcessing
        fields = [
           'id',  
            'user',
            'assigned_to',
            'livestock_category',
            'type_of_sample_received',
            'sample_rating',
            'animal_name',
            'registration_number',
            'sex_of_animal',
            'age_of_animal',
            'date_of_reception',
            'date_of_sample_processing',
            'number_of_days_for_processing',
            'date_of_sample_results',
            'laboratory_findings',
            'comment',
            'owner_name',
            'owner_village',
            'owner_mobile_number',
            'lab_technologist_name',
            'lab_technologist_registration_number',
            'lab_technologist_mobile_number',
            'laboratory_name',
            'signature',
            
        ]
class LaboratoryRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = LaboratoryRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category',
            'other_livestock',
            'name_of_animal',
            'registration_number',
            'age_of_animal',
            'sex_of_animal',
            'history_of_animal',
            'clinical_signs',
            'type_of_sample_collected',
            'date_of_sampling',
            'sample_storage_condition',
            'means_of_transportation',
            'sample_rating',
            'owner_name',
            'owner_village',
            'owner_mobile_number',
           
           'signature',
            'stamp'
        ]
class LivestockIncidentSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = LivestockIncident
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category',
            'animal_name',
            'sex',
            'age',
            'case_history',
            'number_of_sick_animals',
            'morbidity_rate',
            'incidence_date',
            'incidence_time',
            'cadaver_signs',
            'open_for_pm',
            'no_pm_reason',
            'path_condition',
            'sample_sent',
            'cause_notifiable',
            'cause_zoonotic',
            'precaution',
            'disposal_way',
        ]
class VaccinationRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    assigned_by = serializers.StringRelatedField()

    class Meta:
        model = VaccinationRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'assigned_to_official',
            'assigned_by',
            'species_targeted',
            'other_species',
            'number_of_animals_vaccinated',
            'name_of_animal',
            'age_of_animal',
            'sex_of_animal',
            'breed_of_animal',
            'reg_no',
            'color_of_animal',
            'other_description',
            'vaccination_of',
            'other_disease',
            'vaccines_used',
            'batch_number',
            'dosage',
            'route_administration',
            'manufacturer',
            'expiry_date',
            'date_of_vaccination',
            'vaccination_type',
            'next_date_of_vaccination',
            'name_of_rash',
            'nature_of_vaccination_program',
            'name_of_owner',
            'sub_county',
            'ward',
            'location_name',
            'village',
            'contact',
            'signature',
            'location',
            'certificate_file',
            
        ]
        read_only_fields = ['assigned_by']

    
class PostMortemRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = PostMortemRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category',
            'other_livestock',
            'name_of_animal',
            'reg_no',
            'sex',
            'age',
            'case_history',
            'number_of_sick_animals',
            'number_of_dead',
            'morbidity_rate',
            'date_of_incidence',
            'time_of_incidence',
            'signs_of_cadaver',
            'cadaver_open_for_pm',
            'reasons_for_not_opening',
            'major_pathological_conditions',
            'cause_of_death',
            'sample_sent_to_lab',
            'cause_of_death_notifiable',
            'cause_of_death_zoonotic',
            'precautions_if_zoonotic',
            'cadaver_disposed_by',
            'owner_name',
            'owner_village',
            'owner_mobile_number',
            
            
            'signature',
            
        ]
        
class ClinicalRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = ClinicalRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'animal_species_affected',
            'other_species',
            #'number_of_animals_sick',
            'name_of_animal_affected',
            'registration_number',
            'age_of_animal',
            'breed_of_animal',
            'nature_of_disease',
            'case_history',
            'refer_case_to_other_vet',
            'clinical_signs',
            'prognosis',
            'differential_diagnosis',
            'final_diagnosis',
            'treatment_plan',
            'drugs_of_choice',
            'date_of_start_dose',
            'final_treatment_date',
            'is_zoonotic',
            'precautions',
            'is_disease_notifiable',
            'notified_authority',
            'comment',
            'owner_name',
            'owner_village',
            'owner_contact',
            
            'vet_signature',
            
        ]
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id','user', 'date_of_enrollment', 'full_name', 'mobile_number', 'location', 'livestock_interest', 'remarks']
        
class DiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Diary
        fields = ['id','user', 'date','time_of_event', 'main_activity', 'client_contact', 'remarks']
        
class DiseaseReportSerializer(serializers.ModelSerializer):
    #assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = DiseaseReport
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date',
            'livestock_category',
            'other_livestock_category',
            'number_of_animals_affected',
            'sex_of_animals_affected',
            'age_of_animals_affected',
            'clinical_signs',
            'number_of_dead_animals',
            'propose_control_measures',
            'sample_taken_to_lab',
            'tentative_diagnosis',
            'village_disease_occurred',
            'sub_county',
            'county',
            'owner_name',
            'owner_mobile_number',
            
            'signature',
           
        ]
        

# Slaughterhouse Serializer
class SlaughterhouseSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    assigned_to_vet = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = Slaughterhouse
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'assigned_to_vet',
            'reg_date',
            'name', 
            'county', 
            'sub_county', 
            'location',
            'slaughterhouse_status',
            'slaughterhouse_category', 
            'livestock_slaughtered', 
            'number_of_employees', 
            'roller_mark_number',
            'inspector_name',
            'inspector_registration_number',
            'inspector_employment_number',
            'inspector_mobile_number'
        ]


# Employee Serializer
class EmployeeSerializer(serializers.ModelSerializer):
    assigned_to_vet = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )
    slaughterhouse = serializers.CharField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'user',
            'assigned_to_vet',
            'enrollment_date',
            'slaughterhouse',
            'name',
            'id_number',
            'mobile_number',
            'position',
            'medical_license_status',
        ]

# Butcher Serializer
class ButcherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Butcher
        fields = [
            'id', 
            'user',
            'enrollment_date',
            'name', 
            'id_number', 
            'mobile_number', 
            'medical_license_status', 
            'livestock_slaughtered', 
            'meat_container_number', 
            'meat_carrier_number', 
            'means_of_transport'
        ]

User = get_user_model()

class InvoiceSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), required=False)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'user',
            'assigned_to',
            'invoice_category',
            'other_invoice_category',
            'invoice_particulars',
            'date_of_invoice',
            'previous_amount',
            'total_amount_due',
            'payment_method',
            'farmer_name',
            'village',
            'contact',
            'signature',
        ]
        
        
# class ChoiceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Choice
#         fields = ['id', 'text']

# class QuestionSerializer(serializers.ModelSerializer):
#     choices = ChoiceSerializer(many=True, read_only=True)

#     class Meta:
#         model = Question
#         fields = ['id', 'text', 'choices']

# class UserAnswerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserAnswer
#         fields = ['id','user', 'question', 'choice']
        
        
#tutorial
        
class ChoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CpdChoices
        fields = ['id', 'text', 'is_correct']


class SectionSerializer(serializers.ModelSerializer):
    lesson_id = serializers.IntegerField(source='lesson.id', read_only=True)

    class Meta:
        model = Section
        fields = ['id', 'lesson_id', 'lesson', 'title', 'content','file','created_at']

class TutorialSerializer(serializers.ModelSerializer):

    has_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tutorial

        fields = [
            'id',
            'lesson',
            'cpd_number',
            'theme',
            'unit_price',
            'start',
            'stop',
            'points',
            'presented_by',
            'contact_hours',
            'created_at',

            # ONLY THIS
            'has_paid',
        ]
        
class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'section', 'author', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        
# class UserAnswersSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserAnswers
#         fields = ['user', 'question', 'choice']
#cpd quiz
class CpdChoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CpdChoices
        fields = ['id', 'choice_text','is_correct']

class CpdQuestionsSerializer(serializers.ModelSerializer):
    choices = CpdChoicesSerializer(many=True)

    class Meta:
        model = CpdQuestions
        fields = ['id', 'question_text', 'choices']

class QuizResultSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  
    section = serializers.StringRelatedField()  

    class Meta:
        model = QuizResult
        fields = ['id', 'user', 'section', 'score', 'passed', 'timestamp']
        # read_only_fields = ['id', 'timestamp']
# class QuestionResultSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField()  
      

#     class Meta:
#         model = QuestionResult
#         fields = ['id', 'user', 'score', 'passed', 'timestamp']
#         # read_only_fields = ['id', 'timestamp']
       
class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = '__all__'
        
class LivestockExaminationRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = LivestockExaminationRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category',
            'other_category',
            'age_of_animal',
            'breed',
            'sex_of_animal',
            'number_of_animals',
            'origin_of_animal',
            'destination',
            'reason_for_examination',
            'recommendation',
            'owner_name',
            'owner_mobile_number',
            
            'veterinary_officer_signature',
            'created_at',
        ]

class CalvingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalvingRecord
        fields = [
            'id',
            'user',
            'date_of_calving',
            'insemination_date',
            'days_to_calving_down',
            'cow_name',
            'registration_number',
            'calving_procedure',
            'rab_status',
            'hours_for_natural_expulsion',
            'calf_sex',
            'calf_status',
            'reason_for_dead_foetus',
            'comment',
            'created_at',
        ]
        read_only_fields = ['days_to_calving_down', 'created_at']
class AssessmentRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = AssessmentRecord
        fields = [
            'id',
            'user',
            'assigned_to',
            'livestock_category',
            'other_category',
            'breed',
            'date_of_assessment',
            'name_of_animal',
            'registration_number',
            'color_of_animal',
            'age_of_animal',
            'sex_of_animal',
            'number_of_animals',
            'origin_of_animal',
            'place_of_assessment',
            'destination',
            'reason_for_assessment',
            'recommendation',
            'owner_of_animal',
            'owner_mobile_number',
            
            'signature_and_stamp',
        ]
        
class DailyKillSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    
    assigned_by = serializers.StringRelatedField()
    

    class Meta:
        model = DailyKill
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'assigned_by',
            'date',
            'livestock_category',
            #'number_of_females_killed',
            #'number_of_males_killed',
            'total_kills_per_day',
            'condemnation_done',
            'price_per_head',
            'condemnation_status',
            'comment_by_inspector',
            'inspector_name',
            'inspector_reg_number',
            'inspector_status',
        ]
class MovementPermitSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

 # Displays assigned_to as a string
    class Meta:
        model = MovementPermit
        fields = [
            'id', 'user', 'assigned_to_official', 'date_of_permit', 'sub_county_district',
            'ward_level', 'authorized_by', 'registration_number', 'phone_number',
            'uploaded_permit'
        ]


class NoObjectionSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = NoObjection
        fields = [
            'id', 'user', 'assigned_to_official', 'date_of_confirmation', 'sub_county_district',
            'ward_level', 'confirmed_by', 'registration_number', 'phone_number',
            'uploaded_no_objection_form'
        ]


class MonthlyReportSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = MonthlyReport
        fields = [
            'id', 'user', 'assigned_to_official', 'date_of_submission', 'sub_county',
            'ward_level', 'submitted_by', 'registration_number', 'phone_number',
            'uploaded_report'
        ]
class QuarterlyReportSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = QuarterlyReport
        fields = [
            'id', 'user', 'assigned_to_official', 'date_of_submission', 'sub_county',
            'ward_level', 'submitted_by', 'registration_number', 'phone_number',
            'uploaded_report'
        ] 
class YearlyReportSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = YearlyReport
        fields = [
            'id', 'user', 'assigned_to_official', 'date_of_submission', 'sub_county',
            'ward_level', 'submitted_by', 'registration_number', 'phone_number',
            'uploaded_report'
        ]      
class PractitionerSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = Practitioner
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'assigned_by',
            'first_name',
            'last_name',
            'reg_date',
            'phone_number',
            'email',
            'county',
            'subcounty',
            'ward',
            'area_of_operation',
            'specialization',
            'vet_category',
            'registration_number',
            'employment_status'
        ]
        read_only_fields=['assigned_by']

class UterineIrrigationRecordSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = UterineIrrigationRecord
        fields = [
            'id',  
            'user',
            'assigned_to',
            'livestock_category',
            'name_of_animal',
            'registration_number',
            'registration_date',
            'reason',
            'number_of_repeats',
            'abortion_status_history',
            'rabies_status_history',
            'exp_ex_date',
            'previous_insemination_by',
            'treatment_plan',
            'drugs_of_choice',
            'comment',
            'owner_name',
            'village',
            'contact',
            'sign_and_stamp',
        ]



class EmergencyCareSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = EmergencyCare
        fields = [
            'id',
            'user',
            'assigned_to',
            'date',
            'livestock_category',
            'other_category',
            'number_of_animals_affected',
            'name_of_affected_animal',
            'registration_number',
            #'registration_date',
            'emergency_category',
            'condition_of_emergency',
            'case_history',
            'clinical_signs',
            'prognosis',
            'differential_diagnosis',
            'final_diagnosis',
            'referral_status',
            'treatment_plan',
            'drugs_of_choice',
            #'comment',
            'owner_name',
            'village',
            'contact',
    
            
            'signature_and_stamp',
        ]
class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = [
            'id',
            'user',
            'date_of_purchase',
            'product_name',
            'manufacturing_company',
            'buying_price',
            'retail_price',
            'wholesale_price',
            'expiring_date',
        ]
        
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id',
            'user',
            'date_of_enrollment',
            'supply_number',
            'name',
            'mobile_number',
            'location',
            'business_name',
            'mode_of_payment',
            'account_details',
        ]
        
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id',
            'user',
            'date_of_enrollment',
            'name',
            'mobile_number',
            'location',
            'remarks',
        ]
        
class CreditorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Creditor
        fields = [
            'id',
             'user',
            'date_of_transaction',
            'name',
            'mobile_number',
            'total_amount_to_pay',
            'amount_paid',
            'balance_to_pay',
            'agreed_date_of_balance_payment',
            'remarks',
        ]
class DebtorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debtor
        fields = [
            'id',
             'user',
            'date_of_transaction',
            'name',
            'mobile_number',
            'invoice_no',
            'total_invoice_amount',
            'correction_done',
            'amount_of_correction',
            'total_amount_to_pay',
            'previous_balance',
            'grand_total',
            'amount_paid',
            'balance_to_pay',
            'remarks',
        ]
class ClientRequestSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(
        slug_field='username', 
        queryset=User.objects.filter(is_vet_officer=True)
    )
    assigned_by = serializers.SlugRelatedField(
        slug_field='username', 
        queryset=User.objects.filter(is_farmer=True),
        required=False,  # Make it optional because we'll set it automatically
        allow_null=True
    )
    consent_display = serializers.SerializerMethodField()  # Read-only display field
    consent = serializers.BooleanField()  # Editable field

    class Meta:
        model = ClientRequest
        fields = [
            'id', 
            'user',
            'assigned_to',
            'assigned_by', 
            'farmer_name',
            'contact',
            'location',
            'date_of_request',
            'time_of_request',
            'telemedicine_category',
            'request_type', 
            'communication_methods',
            'emergency_condition',
            'non_emergency_condition', 
            'case_history',
            'livestock_category', 
            'other_livestock_category', 
            'consultation_fee', 
            'photo',
            'consent', 
            'status', 
            'judgement',         
            'consent_display',
        ]
        read_only_fields = ['user', 'farmer_name', 'contact', 'assigned_by', 'location']  # Prevent manual input

    def get_consent_display(self, obj):
        return "Yes" if obj.consent else "No"

    def create(self, validated_data):
        request = self.context["request"]  # Get the request object
        user = request.user  # Get the authenticated user

        validated_data["user"] = user  # Set the authenticated user as the request owner

        # If 'assigned_to' exists, set 'assigned_by' to the authenticated user
        if "assigned_to" in validated_data and validated_data["assigned_to"]:
            validated_data["assigned_by"] = user

        return super().create(validated_data)

class VetJudgmentSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.filter(is_farmer=True))

    class Meta:
        model = VetJudgment
        fields = [
            'id', 
            'user',
            'assigned_to', 
            'date_of_judgment', 
            'telemedicine_category', 
            'request_type', 
            'emergency_condition',
            'non_emergency_condition',
            'livestock_category',
            'other_livestock_category',
            'tentative_diagnosis',
            'prognosis',
            'practitioner_judgment',
            'prescription_details',
             
            'referral_details',
        ]
        read_only_fields = []  # Prevent manual input
        
class DailyCheckSerializer(serializers.ModelSerializer):
    #check_section_display = serializers.CharField(source='get_check_section_display', read_only=True)
    #section_status_display = serializers.CharField(source='get_section_status_display', read_only=True)

    class Meta:
        model = DailyCheck
        fields = [
            'id',
            'user',
            'date_of_check',
            'time_of_check',
            'check_section',
            'remarks',
            'checked_by',
            'contact',
        ]
       # read_only_fields = ['user']
class ManagementCommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementCommittee
        fields = [
            'id',
            'user',
            'name',
            'id_number',
            'contact',
            'position',
            'date_of_enrolment',
            'date_of_election',
            'time_period',
            'next_election_date',
            'remarks',
        ]


class HidesAndSkinsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HidesAndSkinsRecord
        fields = [
            'id',
             'user',
            'date_of_kills',
            'category',
            'number_collected',
            'date_of_transportation',
            'means_of_transportation',
            'reg_no_of_vehicle',
            'taken_by',
            'contact',
            'remarks',
        ]
class ApprovedDairyFarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovedDairyFarm
        fields = [
            'id',
            
            'date_of_approval',
            'name_of_farm',
            'county',
            'sub_county',
            'location',
            'name_of_owner',
            'contact',
            'farm_breeding_level',
            'average_milk_per_cow',
            'highest_milk_producer',
            'approved_by',
            'designation',
            'officer_contact',
            'comment',
        ]
class SlaughterhouseHygieneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlaughterhouseHygiene
        fields = [
            'id',
             'user',
            'date_of_cleaning',
            'cleaning_category',
            'cleaning_procedure',
            'state_other_cleaning',
            'cleaning_done_by',
            'contact_of_cleaner',
            'supervised_by',
            'supervisor_contact',
            'remarks',
        ]


class SlaughterhouseAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlaughterhouseAsset
        fields = [
            'id',
             'user',
            'date_of_entry',
            'type_of_asset',
            'other_asset',
            'model_number',
            'registration_number',
            'original_cost',
            'appossession_value',
            'depossession_value',
            'remarks',
        ]
class LivestockRegistrationSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = LivestockRegistration
        fields = [
            "id",
            "user",
            "assigned_to",
            "livestock_type",
            "date_of_registration",
            "breed",
            "sex",
            "age",
            "body_weight",
            "colour",
            "number_of_births",
            "given_name",
            "registration_number",
            "breeding_level",
            "dam_details",
            "sire_details",
            "origin",
            "country_of_importation",
            "source",
            "farm_name",
            "owner_name",
            "owner_phone",
            "owner_id_number",
            "county",
            "sub_county",
            "village",
           
            
            "signature_and_stamp",
            "photo",
            
        ]
        
class VeterinaryEPrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VeterinaryEPrescription
        fields = [
            "id",
            "user",
            "date_of_prescription",
            "drug_category",
            "prescription_target",
            "animal_species",
            "breed",
            "age",
            "drug_trade_name",
            "manufacturer",
            "batch_no",
            "quantity_purchased",
            "drug_volume",
            "dosage",
            "clinical_use",
            "duration_of_treatment",
            "withdrawal_period",
            "storage_condition",
            "side_effect",
            "expiry_date",
            "name_of_the_buyer",
            "buyer_kvb_no",
            "buyer_licence_no",
            "buyer_contact",
            "vet_pharmacist_comment",
            "signature_and_stamp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
class RoutineManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutineManagement
        fields = [
            "id",
            "user",
            "assigned_to",
            "date_of_service",
            "livestock_category",
            "number_of_animals",
            "animal_name",
            "reg_no",
            "age",
            "routine_management",
            "other_management_practice",
            "owner_name",
            "village",
            "contact", 
            "signature_and_stamp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        
class AbortionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbortionRecord
        fields = [
            "id",
            "user",
            "livestock_category",
            "number_of_animals_aborted",
            "animal_name",
            "reg_no",
            "date_of_insemination",
            "date_of_abortion",
            "reason_for_abortion",
            "other_reason",
            "treatment_given",
            "remarks",
            "owner_name",
            "contact",
            "village",
           
           
            "signature_and_stamp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        
class ExtensionServiceSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = ExtensionService
        fields = [
            "id",
            "user",
            "assigned_to_official",
            "date_of_extension",
            "venue",
            "target_group",
            "topic_covered",
            "number_of_participants",
            "female_attendance",
            "male_attendance",
            "children_attendance",
            "name_of_group",
            "location",
            "group_project",
            "village",
            "sub_county",
            "chairperson",
            "secretary",
            "treasurer",
            "member",
            "facilitator_name",
            "facilitator_contact",
            "gps_token",
            "extension_organized_by",
            "remarks",
            "group_photo",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]
        
class UserSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_farmer', 'is_vet_officer']
        

class FieldQuotationSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.filter(is_farmer=True))
    class Meta:
        model = FieldQuotation
        fields = [
            'id',
            'user',
            'assigned_to',
            'date_of_quotation',
            'quotation_category',
            'number_of_animals',
            'payment_description',
            'amount_to_payment',
            'name_of_farm',
            'owner_name',
            'owner_contact',
          
            
            'signature_and_stamp',
        ]
        read_only_fields = ['user'] 
        
        
class DairyFarmerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DairyFarmerRegistration
        fields = [
            "id",
            "user",
            "date_of_registration",
            "full_name",
            "mobile_number",
            "total_number_of_dairy_cows",
            "number_of_lactating_cows",
            "breeds_used",
            "location",
            "milk_supply_number",
        ]


class MilkCollectionCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkCollectionCenter
        fields = [
            "id",
            "user",
            "date_of_enrollment",
            "name_of_collection_centre",
            "location",
            "agent_incharge",
            "mobile_number",
            "approximate_number_of_farmers",
            "means_of_transfer",
            "transporter_name",
            "transporter_mobile",
            "time_of_milk_collection",
        ]


class CurrentMilkPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentMilkPrice
        fields = [
            "id",
            "user",
            "date_of_amendment",
            "last_milk_price",
            "current_milk_price",
            "remarks",
        ]


class FarmerMilkPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerMilkPayment
        fields = [
            "id",
            "user",
            "date_of_payment",
            "milk_supply_number",
            "name_in_full",
            "total_milk_supplied",
            "amount_to_be_paid",
            "amount_paid",
            "balance",
            "remarks",
        ]
        
class MilkCollectionCoolerSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    class Meta:
        model = MilkCollectionCooler
        fields = [
            'id',
            'user',
            'assigned_to',
            'date',
            'location',
            'supply_number',
            'collection_status',
            'reason',
            'total_kg_supplied',
            'name_of_supplier',
            'remarks'
        ]

class MilkCollectionClerkSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = MilkCollectionClerk
        fields = [
            "id",
            "user",
            "assigned_to",
            "location",
            "date",
            "supply_number",
            "total_kg_supplied",
        ]
# Serializer for MilkCollectionCenterRecord
class MilkCollectionCenterRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = MilkCollectionCenterRecord
        fields = [
            'id',
            'user',
            'date',
            'supply_number',
            'collection_status',
            'reason',
            'total',
            'name_of_center',
            'name_of_agent',
            'remarks'
        ]
class DailyRevenueCollectionSerializer(serializers.ModelSerializer):

    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = DailyRevenueCollection
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'source_of_revenue',
            'total_collection',
            'remarks',
            'created_at',
            'updated_at',
        ]
class LeaveRequestSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())


    class Meta:
        model = LeaveRequest
        fields = (
            'id',
            'user',
            'assigned_to_official',
            'date_of_leave_request',
            'sub_county',
            'total_annual_leave_days',
            'days_of_leave_taken',
            'remaining_days',
            'reason_for_leave',
            'name_of_officer',
            'employment_number',
            'working_station',
            'leave_status',
            'remarks',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'leave_status')
        
class MovementPermitsSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = MovementPermits
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'livestock_category',
            'total_animals',
            'price_per_animal',
            'total_revenue_collected',
            'created_at',
        ]
        
        read_only_fields = ['id', 'created_at', 'total_revenue_collected']

    def validate(self, data):
        """
        Optional: Automatically calculate total_revenue_collected 
        before saving if it's not provided or to ensure accuracy.
        """
        total_animals = data.get('total_animals')
        price = data.get('price_per_animal')
        
        if total_animals and price:
            data['total_revenue_collected'] = total_animals * price
            
        return data
class NoObjectionsSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = NoObjections
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'livestock_category',
            'number_of_animals',
            'cost_of_no_objection',
            'total_revenue_collected',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'total_revenue_collected']

    def validate(self, data):
        """
        Ensures total_revenue_collected is the product of 
        number_of_animals and cost_of_no_objection.
        """
        count = data.get('number_of_animals')
        unit_cost = data.get('cost_of_no_objection')
        
        if count is not None and unit_cost is not None:
            data['total_revenue_collected'] = count * unit_cost
            
        return data
class DiseaseReportMovsSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = DiseaseReportMov
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'livestock_category',
            'number_of_reports',
            'suspected_disease',
            'proposed_intervention',
            'remarks',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        
class PractitionersSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    total_practitioners = serializers.ReadOnlyField()

    class Meta:
        model = Practitioners
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'number_employed_by_county',
            'number_in_private_practice',
            'total_practitioners'
        ]
class SlaughterHousesSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    total_slaughterhouses = serializers.ReadOnlyField()

    class Meta:
        model = SlaughterHouses
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'private_slaughterhouses',
            'county_slaughterhouses',
            'total_slaughterhouses',
            'employed_inspectors',
            'roller_markers'
        ]
        
class DailyKillsSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    total_revenue_collected = serializers.ReadOnlyField()

    class Meta:
        model = DailyKills
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'livestock_category',
            'number_of_kills',
            'price_per_kill',
            'total_revenue_collected',
            'remarks'
        ]
        read_only_fields = ['id', 'total_revenue_collected','created_at']
class ArtificialInseminationsSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = ArtificialInseminations
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'number_of_cows_served',
            'semen_type',
            'repeat_cases',
            'revenue_collected',
            'remarks',
        ]
class VaccinationsSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = Vaccinations
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'animal_species',
            'total_vaccinated',
            'vaccine_used',
            'vaccine_source',
            'batch_number',
            'expiry_date',
            'revenue_collected',
            'remarks',
        ]
class ExtensionServicesSerializer(serializers.ModelSerializer):
    assigned_to_official = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = ExtensionServices
        fields = [
            'id',
            'user',
            'assigned_to_official',
            'date_of_record',
            'sub_county',
            'number_of_extensions_done',
            'provider',
            'remarks',
        ]



# =========================
# CASH SALES SERIALIZER
# =========================
class CashSalesSerializer(serializers.ModelSerializer):

    class Meta:
        model = CashSales
        fields = [
            'id',
            'user',
            'sale_date',
            'payment_account_number',
            'cash_in_mpesa',
            'cash_at_hand',
            'total_sales',
            'remarks',
            'created_at',
            'updated_at',
        ]


# =========================
# INVOICE SALES SERIALIZER
# =========================
class InvoiceSalesSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceSales
        fields = [
            'id',
            'user',
            'invoice_date',
            'customer_name',
            'account_customer_number',
            'invoice_number',
            'amount_to_be_paid',
            'status',
            'total_invoice_sales',
            'remarks',
            'created_at',
            'updated_at',
        ]


# =========================
# CREDIT SALES SERIALIZER
# =========================
class CreditSalesSerializer(serializers.ModelSerializer):

    class Meta:
        model = CreditSales
        fields = [
            'id',
            'user',
            'credit_date',
            'client_name',
            'mobile_number',
            'item_taken',
            'amount_to_pay',
            'status',
            'total_credit_sales',
            'remarks',
            'created_at',
            'updated_at',
        ]


# =========================
# INVOICE PAYMENTS SERIALIZER
# =========================
class InvoicePaymentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoicePayments
        fields = [
            'id',
            'user',
            'payment_date',
            'customer_name',
            'invoice_number',
            'previous_balance',
            'amount_paid',
            'balance_remaining',
            'remarks',
            'total_payment_received',
            'created_at',
            'updated_at',
        ]


# =========================
# PETTY CASH EXPENSES SERIALIZER
# =========================
class PettyCashExpensesSerializer(serializers.ModelSerializer):

    class Meta:
        model = PettyCashExpenses
        fields = [
            'id',
            'user',
            'expense_date',
            'purpose',
            'specify_other',
            'amount',
            'remarks',
            'total_petty_cash',
            'created_at',
            'updated_at',
        ]



# ==========================================
# 1. LAYER FLOCK IDENTIFICATION SERIALIZER
# ==========================================
class LayerFlockIdentificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LayerFlockIdentification
        fields = [
            'id',
            'user',
            'date_of_arrival',
            'flock_name_batch_number',
            'age_at_arrival',
            'source_of_chicks_or_pullets',
            'breed',
            'number_of_birds_received',
            'number_of_dead_on_arrival',
            'vaccination_history_at_arrival',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']


# ==========================================
# 2. LAYER DAILY EGG PRODUCTION SERIALIZER
# ==========================================
class LayerDailyEggProductionSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerDailyEggProduction
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_collection',
            'number_of_eggs_collected',
            'number_of_broken_eggs',
            'number_of_dirty_eggs',
            'total_saleable_eggs',
            'eggs_collected_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'total_saleable_eggs']


# ==========================================
# 3. LAYER FEED RECORD SERIALIZER
# ==========================================
class LayerFeedRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerFeedRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_feed_delivery',
            'total_birds_on_feeding',
            'type_of_feed',
            'quantity_received_kg_bags',
            'quantity_fed_daily_per_flock',
            'feed_conversion_ratio',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']

# ==========================================
# 4. LAYER MORTALITY RECORD SERIALIZER
# ==========================================
class LayerMortalityRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerMortalityRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date',
            'number_of_dead_birds',
            'cause_of_death',
            'number_of_live_birds',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']


# ==========================================
# 5. LAYER CULLING RECORDS SERIALIZER
# ==========================================
class LayerCullingRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerCullingRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_culling',
            'number_culled',
            'reasons_for_culling',
            'remarks',
            'created_at',
            'updated_at',
        ]


# ==========================================
# 6. LAYER VACCINATION RECORD SERIALIZER
# ==========================================
class LayerVaccinationRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerVaccinationRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_vaccination',
            'vaccine_administered',
            'total_number_of_birds_vaccinated',
            'age_at_vaccination',
            'next_vaccination_date',
            'withdrawal_period',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']


# ==========================================
# 7. LAYER TREATMENT RECORD SERIALIZER
# ==========================================
class LayerTreatmentRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerTreatmentRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_treatment',
            'number_of_birds',
            'drugs_used',
            'purpose',
            'clinical_signs_of_disease',
            'mode_of_application',
            'duration_of_treatment',
            'withdrawal_period',
            'comments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']


# ==========================================
# 8. LAYER SALES RECORDS SERIALIZER
# ==========================================
class LayerSalesRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_name_batch_number', read_only=True)
    class Meta:
        model = LayerSalesRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_sales',
            'number_of_eggs_sold',
            'price_per_egg',
            'total_amount_received',
            'mode_of_payment',
            'name_of_the_buyer',
            'contact',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'total_amount_received']


# ==========================================
# 9. LAYER INCOME RECORD SERIALIZER
# ==========================================
class LayerIncomeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerIncomeRecord
        fields = [
            'id',
            'user',
            'date',
            'egg_sales',
            'manure_sales',
            'sales_of_culled_birds',
            'other_income_sources',
            'total_aggregate_income',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'total_aggregate_income']


# ==========================================
# 10. LAYER BIOSECURITY AND VISITORS LOG SERIALIZER
# ==========================================
class LayerBiosecurityAndVisitorsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerBiosecurityAndVisitorsLog
        fields = [
            'id',
            'user',
            'date_of_visit',
            'visitor_name',
            'purpose_of_visit',
            'biosecurity_measures_taken',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']







# ==========================================
# 1. BROILER FLOCK IDENTIFICATION SERIALIZER
# ==========================================
class BroilerFlockIdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroilerFlockIdentification
        fields = [
            'id',
            'user',
            'flock_number_batch_id',
            'source_of_chicks',
            'price_per_chick',
            'date_of_arrival',
            'breed',
            'number_of_chicks_ordered',
            'number_of_chicks_received',
            'number_of_weak_chicks',
            'number_of_dead_on_arrival',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user']


# ==========================================
# 2. DAILY MORTALITY SERIALIZER
# ==========================================
class BroilerDailyMortalitySerializer(serializers.ModelSerializer):
    # READABLE field for display
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)

    class Meta:
        model = BroilerDailyMortality

        fields = [
            'id',
            'user',
            'flock',       
            'flock_name',  
            'date',
            'number_of_deaths',
            'possible_cause_of_death',
            'intervention',
            'total_deaths',
            'remarks',
        ]

        read_only_fields = ['user', 'total_deaths']

    def to_representation(self, instance):
        """
        Keep API clean and avoid breaking frontend editing logic
        """
        representation = super().to_representation(instance)

        # fallback safety
        representation['flock_name'] = (
            instance.flock.flock_number_batch_id
            if instance.flock else "-"
        )

        return representation
# ==========================================
# 3. FEED CONSUMPTION SERIALIZER
# ==========================================
class BroilerFeedConsumptionSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    class Meta:
        model = BroilerFeedConsumption
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date',
            'type_of_feed',
            'quantity_of_feed_given_per_day',
            'feed_company',
            'remarks_on_feed',
            'total_feed_consumed',
        ]
        read_only_fields = ['user', 'total_feed_consumed']


# ==========================================
# 4. TREATMENT RECORD SERIALIZER
# ==========================================
class BroilerTreatmentRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    class Meta:
        model = BroilerTreatmentRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date',
            'type_of_drug',
            'purpose',
            'dosage',
            'administration_method',
            'withdrawal_period',
            'remarks',
        ]
        read_only_fields = ['user']


# ==========================================
# 5. VACCINATION RECORD SERIALIZER
# ==========================================
class BroilerVaccinationRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    class Meta:
        model = BroilerVaccinationRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_vaccination',
            'type_of_vaccines_used',
            'dosage',
            'administrative_method',
            'withdrawal_period',
            'next_vaccination_date',
            'type_of_vaccination_to_be_done',
            'remarks',
        ]
        read_only_fields = ['user']


# ==========================================
# 6. GROWTH PERFORMANCE SERIALIZER
# ==========================================
class BroilerGrowthPerformanceSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    # JSONField maps automatically to DRF JSONField handling arrays gracefully
    
    class Meta:
        model = BroilerGrowthPerformance
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_record',
            'body_weight_samples',
            'average_daily_gain',
            'feed_conversion_ratio',
            'remarks',
        ]
        read_only_fields = ['user']


# ==========================================
# 7. ENVIRONMENTAL RECORDS SERIALIZER
# ==========================================
class BroilerEnvironmentalRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    class Meta:
        model = BroilerEnvironmentalRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date',
            'temperature',
            'humidity',
            'ventilation_status',
            'litter_condition',
            'remarks',
        ]
        read_only_fields = ['user']


# ==========================================
# 8. WATER CONSUMPTION SERIALIZER
# ==========================================
class BroilerWaterConsumptionSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    class Meta:
        model = BroilerWaterConsumption
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_record',
            'water_usage_per_litres',
            'abnormal_change_in_water_intake',
            'remarks',
        ]
        read_only_fields = ['user']


# ==========================================
# 9. SALES RECORD SERIALIZER
# ==========================================
class BroilerSalesRecordSerializer(serializers.ModelSerializer):
    flock_name = serializers.CharField(source='flock.flock_number_batch_id', read_only=True)
    class Meta:
        model = BroilerSalesRecord
        fields = [
            'id',
            'user',
            'flock',
            'flock_name',
            'date_of_sales',
            'total_birds_sold',
            'price_per_bird',
            'average_kg_body_weight',
            'total_sales',
            'name_of_the_buyer',
            'mobile_number',
            'remarks',
        ]
        read_only_fields = ['user', 'total_sales']

class EmployeeRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeRecord
        fields = [
            'id',
            'user',
            'date_of_employment',
            'full_name',
            'id_number',
            'mobile_number',
            'next_of_kin_name',
            'next_of_kin_contact',
            'home_county',
            'sub_county',
            'location',
            'area_chief_name',
            'chief_contact',
            'assigned_department',
            'job_position',
            'mode_of_employment',
            'agreed_salary',
            'payment_period',
            'means_of_payment',
            'bank_details',
            'created_at'
        ]
class SalaryRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = SalaryRecord
        fields = [
            'id',
            'user',
            'employee',
            'date_of_payment',
            'salary_status',
            'deductions',
            'amount_paid',
            'balance_to_pay',
            'processed_by',
            'remarks',
            'created_at'
        ]

    read_only_fields = ['user', 'created_at']

class FarmVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmVisit
        fields = [
            'id',
            'user',
            'date_of_visit',
            'visitor_category',
            'number_of_visitors',
            'county_of_origin',
            'objective_of_visits',
            'trainings_covered',
            'areas_visited',
            'training_payment_received',
            'reporting_time',
            'departure_time',
            'remarks',
        ]


class DrugInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugInventory
        fields = [
            'id',
            'user',
            'date_of_purchased',
            'drug_category',
            'drug_name',
            'batch_no',
            'expiry_date',
            'drug_volume',
            'quantity_purchased',
            'quantity_used',
            'balance',
            'unit_cost',
            'total_cost',
            'date_of_record_update',
            'remarks',
        ]


class FeedInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedInventory
        fields = [
            'id',
            'user',
            'date_of_purchased',
            'feed_category',
            'company',
            'expiry_date',
            'quantity_purchased',
            'packed_volume',
            'quantity_used',
            'balance',
            'unit_cost',
            'total_cost',
            'date_of_records_update',
            'remarks',
        ]


class LivestockInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivestockInventory
        fields = [
            'id',
            'user',
            'animal_species',
            'breed',
            'sex',
            'age',
            'total_number',
            'previous_number',
            'source',
            'date_of_record',
            'remarks',
        ]


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'id',
            'user',
            'date_of_record',
            'asset_category',
            'asset_name',
            'date_acquired',
            'model_number',
            'quantity',
            'purchase_cost',
            'current_value',
            'condition',
            'remarks',
        ]


class FishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fish
        fields = [
            'id', 
            'user', 
            'registration_no', 
            'date_of_stocking', 
            'source', 
            'stock_type', 
            'fish_species', 
            'quantity_purchased', 
            'price_per_fish', 
            'total_cost', 
            'dead_on_arrival', 
            'seller_name', 
            'mobile_number', 
            'remarks'
        ]

class FeedingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedingRecord
        fields = [
            'id', 
            'user', 
            'date', 
            'feed_type', 
            'quantity', 
            'remarks'
        ]

class MortalityRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortalityRecord
        fields = [
            'id', 
            'user', 
            'date', 
            'fish_category', 
            'number_of_dead', 
            'possible_cause', 
            'intervention_given', 
            'remarks'
        ]

class GrowthMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrowthMonitoring
        fields = [
            'id', 
            'user', 
            'date_of_sampling', 
            'avg_weight_gain', 
            'avg_length_growth', 
            'remarks'
        ]
class LivestockTradeSerializer(serializers.ModelSerializer):
    total_value = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LivestockTrade
        fields = ["id", "farm_name", "livestock_category", "status", "age", "other_description", "breed", "sex", "number_on_sale", "price_per_unit", "total_value", "sales_period_start", "sales_period_end", "sales_status", "county", "sub_county", "location", "seller_name", "seller_contacts", "vet_incharge","kvb_number", "vet_contacts", "photo", "photo_url", "approval_status", "approved_by", "approved_by_name", "approved_at", "rejection_reason", "created_at", "updated_at"]
        read_only_fields = ["id", "total_value", "photo_url", "approved_by", "approved_by_name", "approved_at", "created_at", "updated_at"]

    def get_total_value(self, obj):
        return obj.number_on_sale * obj.price_per_unit

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if not obj.photo:
            return None
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url

    def get_approved_by_name(self, obj):
        if not obj.approved_by:
            return None
        name = obj.approved_by.get_full_name() if hasattr(obj.approved_by, "get_full_name") else ""
        return name or getattr(obj.approved_by, "username", str(obj.approved_by))

    def validate_number_on_sale(self, value):
        if value < 1:
            raise serializers.ValidationError("Number on sale must be at least 1.")
        return value

    def validate_price_per_unit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price per unit must be greater than zero.")
        return value

    def validate(self, attrs):
        start = attrs.get("sales_period_start")
        end = attrs.get("sales_period_end")
        if start and end and end < start:
            raise serializers.ValidationError({"sales_period_end": "Sales period end date cannot be before the start date."})
        return attrs

class AdminSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "title", "content", "file", "created_at"]
        read_only_fields = ["id", "created_at"]


class AdminChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CpdChoices
        fields = ["id", "choice_text", "is_correct"]
        read_only_fields = ["id"]


class AdminQuestionSerializer(serializers.ModelSerializer):
    choices = AdminChoiceSerializer(many=True)

    class Meta:
        model = CpdQuestions
        fields = ["id", "question_text", "choices"]
        read_only_fields = ["id"]

    def validate_choices(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Add at least two choices.")
        if sum(1 for c in value if c["is_correct"]) != 1:
            raise serializers.ValidationError("Mark exactly one choice as correct.")
        return value

    @transaction.atomic
    def create(self, validated):
        choices = validated.pop("choices")
        q = CpdQuestions.objects.create(**validated)  # user + section come from save()
        CpdChoices.objects.bulk_create([CpdChoices(question=q, **c) for c in choices])
        return q