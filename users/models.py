from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager

class Roles(models.Model):
    """
    System pre-set user roles model
    """
    role_name = models.CharField(max_length=100)
    role_description = models.CharField(max_length=200, blank=True)
    role_date = models.DateTimeField(auto_now_add=True)
    role_udate = models.DateTimeField(auto_now=True)

class UserManager(BaseUserManager):
    def create_user(self, email,username, password=None,**extra_fields):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username,password=None,**extra_fields):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            username,
            password,
            **extra_fields
        )
        user.is_admin = True
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser):
    """
    User profile model - an extension of users model
    """
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    firstname = models.CharField(max_length=100, blank=False)
    lastname = models.CharField(max_length=100, blank=False)
    username = models.CharField(max_length=40, unique=True)
    phone = models.CharField(max_length=20, blank=False)
    address = models.CharField(max_length=100, blank=True)
    town = models.CharField(max_length=100, blank=True)
    can_login = models.BooleanField(default=True)
    role = models.ForeignKey(Roles, related_name="role", on_delete=models.RESTRICT, default=1)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    queue_status = models.CharField(max_length=100, default="OFFLINE", blank=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    lastcalltime = models.DateTimeField(null=True)
    offdays = models.JSONField(default=dict)
    lastevent = models.CharField(max_length=100, blank=True, default="")
    lastlogin = models.DateTimeField(blank=True, null=True)
    lastlogout = models.DateTimeField(blank=True, null=True)

    # ---- Fields carried over from the old model ----

    # User type flags
    is_vet_officer = models.BooleanField(default=False)
    is_farmer = models.BooleanField(default=False)
    is_official = models.BooleanField(default=False)
    is_cooperative = models.BooleanField(default=False)
    is_agrovet = models.BooleanField(default=False)
    is_slaughterhouse = models.BooleanField(default=False)

    # Professional details
    specialization = models.CharField(max_length=100, null=True, blank=True)
    vet_category = models.CharField(max_length=100, null=True, blank=True)
    supervisor = models.CharField(max_length=100, null=True, blank=True)
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    licence_number = models.CharField(max_length=100, null=True, blank=True)
    vmd_number = models.CharField(max_length=100, null=True, blank=True)

    # Location details
    county = models.CharField(max_length=100, null=True, blank=True)
    subcounty = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)

    # Business / organisation names
    business_name = models.CharField(max_length=100, default="SOIN VETERINARY SERVICES")
    cooperative_name = models.CharField(max_length=100, default="DAIRY COOPERATIVE SERVICES")
    farm_name = models.CharField(max_length=100, default="SOINFARM")
    agrovet_name = models.CharField(max_length=100, default="SOIN AGROVET SERVICES")

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['firstname', 'lastname', 'email', 'role']

    def __str__(self):
        return self.firstname + " " + self.lastname

    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.firstname} {self.lastname}".strip()

    def get_short_name(self):
        """Return the user's short name (first name)."""
        return self.firstname

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        # Needed for Django admin access, since AbstractBaseUser doesn't provide it
        return self.is_admin

class ActivityLog(models.Model):
    user       = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='activity_logs')
    action     = models.CharField(max_length=100)          # e.g. 'login', 'case_created'
    entity     = models.CharField(max_length=100, blank=True)  # e.g. 'Case', 'User'
    entity_id  = models.CharField(max_length=100, blank=True)
    detail     = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    @classmethod
    def log(cls, action, user=None, entity='', entity_id='', detail='', request=None):
        ip = None
        if request:
            try:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0].strip()
                if not ip:
                    ip = request.META.get('REMOTE_ADDR')
            except Exception:
                ip = None
        cls.objects.create(user=user, action=action, entity=entity,
                           entity_id=str(entity_id), detail=detail, ip_address=ip)