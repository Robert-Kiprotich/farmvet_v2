"""
create_test_users.py
====================
Development-only script to seed system roles and test users using role constants.

Usage:
    python create_test_users.py
"""

import os
import sys

# ── Django setup ─────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from users.models import Roles

User = get_user_model()


# ── Role Constants ───────────────────────────────────────────────────────────

ADMIN = "administrator"
FARMER = "farmer"
VET = "vet officer"
AGROVET = "agrovet"
COOP = "cooperative"
SLAUGHTER = "slaughterhouse"


# ── 1. Define and Seed Roles First ───────────────────────────────────────────

DEFAULT_ROLES = [
    {
        "role_name": ADMIN,
        "role_description": "System administrator with full access privileges.",
    },
    {
        "role_name": FARMER,
        "role_description": "Livestock or crop farmer profile.",
    },
    {
        "role_name": VET,
        "role_description": "Registered veterinary officer and practitioner.",
    },
    {
        "role_name": AGROVET,
        "role_description": "Agrovet store owner or operator.",
    },
    {
        "role_name": COOP,
        "role_description": "Farmers cooperative representative.",
    },
    {
        "role_name": SLAUGHTER,
        "role_description": "Slaughterhouse facility operator.",
    },
]


def seed_roles():
    print("\nEnsuring roles exist in database...")
    for role_data in DEFAULT_ROLES:
        role, created = Roles.objects.update_or_create(
            role_name=role_data["role_name"],
            defaults={
                "role_description": role_data["role_description"],
            },
        )
        action = "Created" if created else "Updated"
        print(f"  📌 Role | {role.role_name:<18} ({action})")


# ── 2. Helper to Create / Update Users ───────────────────────────────────────

def get_role(role_name):
    try:
        return Roles.objects.get(role_name=role_name)
    except Roles.DoesNotExist:
        print(f"❌ Role '{role_name}' does not exist")
        return None


def create_or_update_user(
    username,
    password,
    firstname,
    lastname,
    email,
    phone,
    role_name,
    is_admin=False,
    role_flags=None,
):
    if role_flags is None:
        role_flags = {}

    role = get_role(role_name)
    if not role:
        return

    # Base field defaults matching your custom User model
    defaults = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "phone": phone,
        "role": role,
        "is_active": True,
        "is_admin": is_admin,
    }

    # Add all user type boolean flags
    all_flags = [
        "is_vet_officer",
        "is_farmer",
        "is_official",
        "is_cooperative",
        "is_agrovet",
        "is_slaughterhouse",
    ]
    for flag in all_flags:
        defaults[flag] = role_flags.get(flag, False)

    user, created = User.objects.get_or_create(
        username=username,
        defaults=defaults,
    )

    # Update existing user fields if already present
    if not created:
        user.firstname = firstname
        user.lastname = lastname
        user.email = email
        user.phone = phone
        user.role = role
        user.is_active = True
        user.is_admin = is_admin
        for flag in all_flags:
            setattr(user, flag, role_flags.get(flag, False))

    # Always reset password securely
    user.set_password(password)
    user.save()

    action = "Created" if created else "Updated"
    print(
        f"✅ {action}: "
        f"{username:<15} | "
        f"{role.role_name:<15} | "
        f"password: {password}"
    )


# ── 3. Define Test Users ─────────────────────────────────────────────────────

TEST_USERS = [
    # username, password, firstname, lastname, email, phone, role_name, is_admin, role_flags

    (
        "admin",
        "admin123",
        "System",
        "Administrator",
        "admin@system.local",
        "0700000001",
        ADMIN,
        True,
        {"is_official": True},
    ),

    (
        "farmer_user",
        "farmer123",
        "John",
        "Farmer",
        "farmer@system.local",
        "0711000002",
        FARMER,
        False,
        {"is_farmer": True},
    ),

    (
        "vet_user",
        "vet123",
        "Dr. Vet",
        "Officer",
        "vet@system.local",
        "0711000003",
        VET,
        False,
        {"is_vet_officer": True},
    ),

    (
        "agrovet_user",
        "agrovet123",
        "Agrovet",
        "Shop",
        "agrovet@system.local",
        "0711000004",
        AGROVET,
        False,
        {"is_agrovet": True},
    ),

    (
        "coop_user",
        "coop123",
        "Farmers",
        "Cooperative",
        "coop@system.local",
        "0711000005",
        COOP,
        False,
        {"is_cooperative": True},
    ),

    (
        "slaughter_user",
        "slaughter123",
        "Central",
        "Slaughterhouse",
        "slaughter@system.local",
        "0711000006",
        SLAUGHTER,
        False,
        {"is_slaughterhouse": True},
    ),
]


# ── 4. Execution ─────────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("SYSTEM — DEVELOPMENT SEEDER SCRIPT")
print("=" * 70)

# Step A: Seed Roles
seed_roles()

# Step B: Seed Users
print("\nCreating / updating users...\n")
for user_data in TEST_USERS:
    try:
        create_or_update_user(*user_data)
    except Exception as e:
        print(f"❌ Failed: {user_data[0]} → {e}")


# ── Summary Report ───────────────────────────────────────────────────────────

print("\n" + "=" * 70)
print("LOGIN CREDENTIALS SUMMARY")
print("=" * 70)
print(f"{'Username':<15}{'Password':<15}{'Role Name'}")
print("-" * 50)

for user_data in TEST_USERS:
    username = user_data[0]
    password = user_data[1]
    role_name_val = user_data[6]
    print(f"{username:<15}{password:<15}{role_name_val}")

print("=" * 70)
print("Database seeding completed successfully.")
print("=" * 70)