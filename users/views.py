import json
import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from users.models import ActivityLog, Roles, User
from django.views.decorators.csrf import ensure_csrf_cookie

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ROLE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

# role_name (lowercase) -> boolean flag on the User model.
# These are the roles a person may pick when registering themselves.
SELF_REGISTER_ROLES = {
    "farmer": "is_farmer",
    "vet officer": "is_vet_officer",
    "agrovet": "is_agrovet",
    "cooperative": "is_cooperative",
    "slaughterhouse": "is_slaughterhouse",
}

# All roles that map to a flag (includes roles only an admin can assign).
ALL_ROLE_FLAGS = {**SELF_REGISTER_ROLES, "official": "is_official"}
ALL_FLAGS = set(ALL_ROLE_FLAGS.values())

# Optional profile fields accepted at registration and in admin create/edit.
OPTIONAL_FIELDS = [
    "address", "town", "county", "subcounty", "location",
    "specialization", "vet_category", "supervisor",
    "registration_number", "licence_number", "vmd_number",
    "business_name", "cooperative_name", "farm_name", "agrovet_name",
]


def sync_role_flags(user):
    """
    Turn on the is_* flag that matches user.role and turn the others off.
    Only the Administrator role gets is_admin.
    """
    role_name = user.role.role_name.strip().lower()

    for flag in ALL_FLAGS:
        setattr(user, flag, False)

    flag = ALL_ROLE_FLAGS.get(role_name)
    if flag:
        setattr(user, flag, True)

    user.is_admin = role_name == "administrator"


def _get_payload(request):
    """Accept JSON or normal form POST. Returns None on invalid JSON."""
    if request.content_type == "application/json":
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return None
    return request.POST


def _log(action, **kwargs):
    """Write to ActivityLog without ever breaking the request."""
    try:
        ActivityLog.log(action, **kwargs)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# USER MANAGEMENT (admin)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def users(request, userid=False, action=False):
    """
    User management.
    Handles:
    - User listing
    - User creation / editing
    - Password reset
    - Password change (own account)
    - Enable / disable users
    - User profiles
    """

    data = {
        "title": "User List",
        "message": False,
        "status": "success",
    }

    messages = {
        "passwordreset": "Could not reset password, try again",
    }

    is_admin = bool(getattr(request.user, "is_admin", False))

    # ─────────────────────────────────────────────────────────────────────
    # POST REQUESTS
    # ─────────────────────────────────────────────────────────────────────

    if request.method == "POST":

        # Everything except changing your own password is admin-only.
        if action != "changepassword" and not is_admin:
            return JsonResponse(
                {"status": "error", "message": "Forbidden"},
                status=403,
            )

        try:

            # ── Reset user password ──────────────────────────────────────
            if action == "resetpassword":
                try:
                    usr = User.objects.get(pk=userid)

                    # Development only: password becomes the username
                    usr.set_password(usr.username)
                    usr.save()

                    data["message"] = "Password reset successful."
                    code = 200

                except User.DoesNotExist:
                    data["message"] = "User not found."
                    code = 404

                except Exception:
                    logger.exception("Password reset failed")
                    data["message"] = messages["passwordreset"]
                    code = 500

                return JsonResponse(data, status=code)

            # ── Enable / disable user ────────────────────────────────────
            if action in ["disable", "enable"]:
                status = action == "enable"

                try:
                    usr = User.objects.get(pk=userid)

                    # Don't let an admin lock themselves out
                    if usr.pk == request.user.pk and not status:
                        return JsonResponse(
                            {
                                "status": "error",
                                "message": "You cannot disable your own account.",
                            },
                            status=400,
                        )

                    usr.is_active = status
                    usr.save(update_fields=["is_active"])

                    data["message"] = (
                        f"User {'enabled' if status else 'disabled'} successfully."
                    )
                    code = 200

                except User.DoesNotExist:
                    data["message"] = "User not found."
                    code = 404

                except Exception:
                    logger.exception("Enable/disable failed")
                    data["message"] = (
                        f"Could not {'enable' if status else 'disable'} user, "
                        "try again"
                    )
                    code = 500

                return JsonResponse(data, status=code)

            # ── Change current user's password ───────────────────────────
            if action == "changepassword":
                password = request.POST.get("passwd")

                if not password:
                    return JsonResponse(
                        {"status": "error", "message": "Password is required"},
                        status=400,
                    )

                try:
                    validate_password(password, user=request.user)
                except ValidationError as e:
                    return JsonResponse(
                        {"status": "error", "message": " ".join(e.messages)},
                        status=400,
                    )

                usr = request.user
                usr.set_password(password)
                usr.save()

                # Keep the current session alive after password change
                login(request, usr)

                return JsonResponse(
                    {"status": "success", "message": "Password changed successfully"}
                )

            # ── Edit existing user ───────────────────────────────────────
            if action == "edit":
                usr = User.objects.get(pk=userid)
                creating = False

            # ── Create new user ──────────────────────────────────────────
            else:
                creating = True

                username = str(request.POST.get("username", "")).strip().lower()

                if not username:
                    return JsonResponse(
                        {"status": "error", "message": "Username is required"},
                        status=400,
                    )

                if User.objects.filter(username__iexact=username).exists():
                    return JsonResponse(
                        {"status": "error", "message": "Username already exists"},
                        status=400,
                    )

                usr = User(username=username)

                # Development default password (same as username)
                usr.set_password(username)

                usr.offdays = {}
                usr.can_login = True
                usr.is_active = True

            # ── Common fields ────────────────────────────────────────────
            usr.firstname = request.POST.get("firstname", "").strip()
            usr.lastname = request.POST.get("lastname", "").strip()
            usr.email = request.POST.get("email", "").strip().lower()
            usr.phone = request.POST.get("phone", "").strip()

            for field in OPTIONAL_FIELDS:
                if field in request.POST:
                    setattr(usr, field, request.POST.get(field, "").strip())

            if not usr.address:
                usr.address = "N/A"

            # ── Role ─────────────────────────────────────────────────────
            role_id = request.POST.get("userrole")

            if not role_id:
                return JsonResponse(
                    {"status": "error", "message": "User role is required"},
                    status=400,
                )

            usr.role = Roles.objects.get(pk=role_id)

            # ── Avatar (uploaded file, or plain value as before) ─────────
            avatar_file = request.FILES.get("fl_avatar")
            if avatar_file:
                usr.avatar = avatar_file
            elif request.POST.get("fl_avatar"):
                usr.avatar = request.POST.get("fl_avatar")

            # Keep is_* flags and is_admin in sync with the role
            sync_role_flags(usr)

            usr.save()

            data["message"] = (
                "User created successfully." if creating else "User updated successfully."
            )
            data["status"] = "success"

            return JsonResponse(data, status=201 if creating else 200)

        except User.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "User not found."},
                status=404,
            )

        except Roles.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Selected role does not exist."},
                status=400,
            )

        except IntegrityError:
            return JsonResponse(
                {"status": "error", "message": "Username or email already exists."},
                status=400,
            )

        except Exception as e:
            logger.exception("User operation failed")
            return JsonResponse(
                {"status": "error", "message": f"User operation failed: {str(e)}"},
                status=500,
            )

    # ─────────────────────────────────────────────────────────────────────
    # GET REQUESTS
    # ─────────────────────────────────────────────────────────────────────

    # Edit user form (admin only)
    if action == "edit":
        if not is_admin:
            return JsonResponse(
                {"status": "error", "message": "Forbidden"}, status=403
            )

        data["roles"] = Roles.objects.all().order_by("-id")
        data["user"] = get_object_or_404(User, pk=userid)

        return render(request, "users/edit.html", data)

    # User profile (own profile, or any profile for admins)
    if userid and not action:
        if not is_admin and str(request.user.pk) != str(userid):
            return JsonResponse(
                {"status": "error", "message": "Forbidden"}, status=403
            )

        data["user"] = get_object_or_404(User, pk=userid)
        data["title"] = "User Profile"

        return render(request, "main/profile.html", data)

    # User list (admin only)
    if not is_admin:
        return JsonResponse(
            {"status": "error", "message": "Forbidden"}, status=403
        )

    data["users"] = User.objects.all().order_by("-id")
    data["roles"] = Roles.objects.all().order_by("-id")

    return render(request, "users/users.html", data)


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────────────────────
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def user_register(request):
    """
    GET  /register/  -> roles a person can register as
    POST /register/  -> create the account
    """

    allowed_roles = [
        r for r in Roles.objects.all()
        if r.role_name.strip().lower() in SELF_REGISTER_ROLES
    ]

    if request.method == "GET":
        return JsonResponse(
            {
                "status": "success",
                "roles": [{"id": r.id, "name": r.role_name} for r in allowed_roles],
            }
        )

    payload = _get_payload(request)
    if payload is None:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON"}, status=400
        )

    username = str(payload.get("username", "")).strip().lower()
    email = str(payload.get("email", "")).strip().lower()
    firstname = str(payload.get("firstname", "")).strip()
    lastname = str(payload.get("lastname", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    password = payload.get("password", "")
    password2 = payload.get("password2", "")
    role_id = payload.get("role")

    # ── Required fields ──────────────────────────────────────────────────
    required = {
        "username": username,
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "phone": phone,
        "password": password,
        "role": role_id,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}",
            },
            status=400,
        )

    if password2 and password != password2:
        return JsonResponse(
            {"status": "error", "message": "Passwords do not match"}, status=400
        )

    # ── Role (only roles allowed for self-registration) ──────────────────
    role = next((r for r in allowed_roles if str(r.id) == str(role_id)), None)
    if role is None:
        return JsonResponse(
            {"status": "error", "message": "Invalid role selected"}, status=400
        )

    # ── Duplicates ───────────────────────────────────────────────────────
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse(
            {"status": "error", "message": "Username already exists"}, status=400
        )

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {"status": "error", "message": "Email already registered"}, status=400
        )

    # ── Password strength (uses AUTH_PASSWORD_VALIDATORS from settings) ──
    candidate = User(
        username=username, email=email, firstname=firstname, lastname=lastname
    )
    try:
        validate_password(password, user=candidate)
    except ValidationError as e:
        return JsonResponse(
            {"status": "error", "message": " ".join(e.messages)}, status=400
        )

    # ── Create ───────────────────────────────────────────────────────────
    try:
        with transaction.atomic():
            usr = User(
                username=username,
                email=email,
                firstname=firstname,
                lastname=lastname,
                phone=phone,
                role=role,
                offdays={},
            )
            usr.set_password(password)

            for field in OPTIONAL_FIELDS:
                value = str(payload.get(field, "")).strip()
                if value:
                    setattr(usr, field, value)

            sync_role_flags(usr)
            usr.save()

    except IntegrityError:
        return JsonResponse(
            {"status": "error", "message": "Username or email already exists"},
            status=400,
        )
    except Exception as e:
        logger.exception("Registration failed")
        return JsonResponse(
            {"status": "error", "message": f"Registration failed: {str(e)}"},
            status=500,
        )

    _log(
        "register",
        user=usr,
        entity="User",
        entity_id=usr.id,
        detail=f"{usr.username} registered as {role.role_name}",
        request=request,
    )

    return JsonResponse(
        {
            "status": "success",
            "message": "Account created successfully. You can now log in.",
            "redirect_to": "/login/",
        },
        status=201,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

def user_logout(request):

    if request.user.is_authenticated:
        _log(
            "logout",
            user=request.user,
            entity="User",
            entity_id=request.user.id,
            detail=f"{request.user.username} logged out",
            request=request,
        )

        try:
            request.user.lastlogout = timezone.now()
            request.user.save(update_fields=["lastlogout"])
        except Exception:
            pass

    logout(request)

    return redirect("/login/")


# ─────────────────────────────────────────────────────────────────────────────
# CSRF
# ─────────────────────────────────────────────────────────────────────────────

def csrf_token_view(request):
    """
    GET /users/csrf/
    Returns the CSRF token for the frontend.
    """

    token = get_token(request)

    response = JsonResponse({"csrftoken": token})
    response["X-CSRFToken"] = token

    return response


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

def user_login(request):
    """
    Authenticate a user and return their information.
    """

    try:
        data = json.loads(request.body)

        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()

        if not username or not password:
            return JsonResponse(
                {"status": "error", "message": "Username and password required"},
                status=400,
            )

        user = authenticate(request, username=username, password=password)

        # ── Invalid login ────────────────────────────────────────────────
        if user is None:
            _log(
                "login_failed",
                user=None,
                entity="User",
                entity_id="",
                detail=f"Failed login attempt for username: '{username}'",
                request=request,
            )
            return JsonResponse(
                {"status": "error", "message": "Invalid credentials"},
                status=401,
            )

        # ── Disabled account / login not allowed ─────────────────────────
        if not user.is_active or not getattr(user, "can_login", True):
            _log(
                "login_failed",
                user=user,
                entity="User",
                entity_id=user.id,
                detail=f"Login blocked: account disabled: '{username}'",
                request=request,
            )
            return JsonResponse(
                {"status": "error", "message": "Account is disabled"},
                status=403,
            )

        # ── Login ────────────────────────────────────────────────────────
        login(request, user)

        try:
            user.lastlogin = timezone.now()
            user.save(update_fields=["lastlogin"])
        except Exception:
            pass

        _log(
            "login",
            user=user,
            entity="User",
            entity_id=user.id,
            detail=f"{user.username} logged in",
            request=request,
        )

        # ── Role ─────────────────────────────────────────────────────────
        role_name = ""
        try:
            if user.role:
                role_name = user.role.role_name
        except Exception:
            pass

        # ── Avatar ───────────────────────────────────────────────────────
        avatar_url = ""
        if getattr(user, "avatar", None):
            try:
                avatar_url = request.build_absolute_uri(user.avatar.url)
            except Exception:
                pass

        return JsonResponse(
            {
                "status": "success",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": (
                        f"{getattr(user, 'firstname', '')} "
                        f"{getattr(user, 'lastname', '')}"
                    ).strip() or user.username,
                    "email": user.email,
                    "phone": getattr(user, "phone", ""),
                    "role": role_name,
                    "is_admin": user.is_admin,
                    "is_farmer": user.is_farmer,
                    "is_vet_officer": user.is_vet_officer,
                    "is_official": user.is_official,
                    "is_cooperative": user.is_cooperative,
                    "is_agrovet": user.is_agrovet,
                    "is_slaughterhouse": user.is_slaughterhouse,
                    "avatar_url": avatar_url,
                },
                "redirect_to": "/",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON"}, status=400
        )

    except Exception as e:
        logger.exception("Login error")
        return JsonResponse(
            {"status": "error", "message": f"Login failed: {str(e)}"},
            status=500,
        )