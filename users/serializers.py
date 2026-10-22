from rest_framework import serializers
from .models import User, Roles


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'role_name', 'role_description']


class UserSerializer(serializers.ModelSerializer):
    role_detail = RolesSerializer(source='role', read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            # Core
            'id', 'email', 'firstname', 'lastname', 'username', 'password',
            'phone', 'address', 'town', 'role', 'role_detail',
            'avatar', 'date_of_birth', 'is_active', 'queue_status',
            'date_joined', 'lastevent', 'lastlogin', 'lastlogout',

            # User type flags
            'is_vet_officer', 'is_farmer', 'is_official',
            'is_cooperative', 'is_agrovet', 'is_slaughterhouse',

            # Professional details
            'specialization', 'vet_category', 'supervisor',
            'registration_number', 'licence_number', 'vmd_number',

            # Location details
            'county', 'subcounty', 'location',

            # Business / organisation names
            'business_name', 'cooperative_name', 'farm_name', 'agrovet_name',
        ]
        read_only_fields = ['id', 'date_joined', 'lastlogin', 'lastlogout']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance