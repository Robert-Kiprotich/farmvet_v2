from functools import wraps

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated


def _role_name(user):
    try:
        return user.role.role_name.strip().lower()
    except Exception:
        return ""


def make_role_permission(class_name, flag, *role_names):
    """
    Build a permission class that:
      1. requires an authenticated user (IsAuthenticated), AND
      2. requires the matching is_* flag OR matching role name.
    Supports DRF composition: Is_Vet | Is_Farmer, Is_Vet & Is_Official, ~Is_Farmer
    """
    def has_permission(self, request, view):
        if not IsAuthenticated.has_permission(self, request, view):
            return False
        user = request.user
        return bool(getattr(user, flag, False)) or _role_name(user) in role_names

    return type(
        class_name,
        (IsAuthenticated,),
        {
            "message": f"{class_name.replace('_', ' ')} role required.",
            "has_permission": has_permission,
        },
    )


Is_Farmer       = make_role_permission("Is_Farmer", "is_farmer", "farmer")
Is_Vet          = make_role_permission("Is_Vet", "is_vet_officer", "vet officer")
Is_Official     = make_role_permission("Is_Official", "is_official", "official")
Is_Coop         = make_role_permission("Is_Coop", "is_cooperative", "cooperative")
Is_Agrovet      = make_role_permission("Is_Agrovet", "is_agrovet", "agrovet")
Is_SlaughterHouse = make_role_permission("Is_SlaughterHouse", "is_slaughterhouse", "slaughterhouse")
Is_Admin        = make_role_permission("Is_Admin", "is_admin", "administrator")

IsVetOrOfficial = Is_Vet | Is_Official


# ---- for plain Django views (replaces @user_passes_test(vet_check)) ----------
def role_required(*flags):
    """@role_required('is_vet_officer') -> 401 if anonymous, 403 if wrong role."""
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return JsonResponse({"detail": "Authentication required."}, status=401)
            if not any(getattr(user, f, False) for f in flags):
                return JsonResponse({"detail": "You do not have permission."}, status=403)
            return view(request, *args, **kwargs)
        return wrapper
    return decorator