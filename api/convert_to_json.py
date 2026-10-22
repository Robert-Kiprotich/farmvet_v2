#!/usr/bin/env python3
"""
convert_to_json.py

Refactors Django view modules so nothing renders a template any more:

  1. Views whose only job is `return render(request, 'x.html', {})`
     (with or without a decorator) are DELETED.
  2. Views that passed data into a template are REPLACED with versions
     that return JsonResponse. (See REPLACEMENTS below - reviewed by hand.)
  3. Anything still calling render() afterwards is reported so nothing
     slips through silently.

Usage:
    python convert_to_json.py views.py more_views.py [--urls urls.py] [--dry-run]

Each file is backed up to <file>.bak before being rewritten, and the result
is checked with ast.parse() before anything is written.
--urls only PRINTS the url patterns that still point at removed views;
it never edits urls.py.
"""
import argparse
import ast
import re
import shutil
import sys
import textwrap
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────
# Helper code injected once, right after `logger = ...` in the views module
# ──────────────────────────────────────────────────────────────────────────
HELPERS = r'''
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
'''
HELPER_ANCHOR = "logger = logging.getLogger(__name__)"

# ──────────────────────────────────────────────────────────────────────────
# Replacements (name -> new source). Applies to module-level defs/classes.
# ──────────────────────────────────────────────────────────────────────────
REPLACEMENTS = {}


def add(name, src):
    REPLACEMENTS[name] = textwrap.dedent(src).strip("\n") + "\n\n"


def list_view(name, pairs):
    """Generate a `{key: safe_values(queryset)}` JSON view."""
    body = ",\n".join(f'        "{k}": safe_values({expr})' for k, expr in pairs)
    REPLACEMENTS[name] = (
        f"@json_login_required\n"
        f"def {name}(request):\n"
        f"    return JsonResponse({{\n{body},\n    }})\n\n"
    )


# -- Portals ---------------------------------------------------------------
add("csrf_failure", '''
    def csrf_failure(request, reason=""):
        return JsonResponse({"error": "CSRF verification failed", "reason": reason}, status=403)
''')

for _name, _check, _login, _key, _model, _role in [
    ("portal_vet", "vet_check", "vet-login", "all_vets", "Vet_Officer", "vet"),
    ("cooperative", "cooperative_check", "cooperative-login", "all_coops", "DairyCooperative", "cooperative"),
    ("portal_official", "official_check", "official-login", "all_officers", "Official", "officer"),
    ("portal_slaughterhouse", "slaughterhouse_check", "slaughterhouse-login", "all_animals", "SlaughterHouse", "slaughterhouse"),
    ("portal_farmer", "farmer_check", "farmer-login", "all_vets", "Vet_Officer", "farmer"),
    ("agrovet", "agrovet_check", "agrovet-login", "all_vets", "Agrovet", "agrovet"),
]:
    add(_name, f'''
        @user_passes_test({_check}, login_url='{_login}')
        def {_name}(request):
            return JsonResponse({{
                "{_key}": safe_values({_model}.objects.all()),
                "role": "{_role}",
            }})
    ''')

add("vet_list", '''
    @user_passes_test(farmer_check, login_url='farmer-login')
    def vet_list(request):
        return JsonResponse({"all_vets": safe_values(Vet_Officer.objects.all())})
''')
add("vet_list_vet", '''
    @user_passes_test(vet_check, login_url='vet-login')
    def vet_list_vet(request):
        return JsonResponse({"all_vets": safe_values(Vet_Officer.objects.all())})
''')

# -- Farmer ----------------------------------------------------------------
add("milk_record", '''
    @user_passes_test(farmer_check, login_url='farmer-login')
    def milk_record(request):
        return JsonResponse({
            "employees": safe_values(EmployeeRecord.objects.filter(user=request.user)),
            "cows": safe_values(LactatingCow.objects.filter(user=request.user)),
        })
''')

list_view("salary_record", [("employees", "Employee.objects.filter(user=request.user)")])
list_view("farm_visit_record", [("farm_visits", "FarmVisit.objects.filter(user_id=request.user.id)")])
list_view("drug_inventory_record", [("drugs", "DrugInventory.objects.filter(user=request.user)")])
list_view("feed_inventory_record", [("feeds", "FeedInventory.objects.filter(user=request.user)")])
list_view("livestock_record", [("livestock_items", "Livestock.objects.filter(user=request.user)")])
list_view("asset_record", [("assets", "Asset.objects.filter(user=request.user)")])
list_view("fish_record", [("fish_list", "Fish.objects.filter(user=request.user)")])
list_view("feeding_record", [("feeding_records", "FeedingRecord.objects.filter(user=request.user)")])
list_view("mortality_record", [("mortality_records", "MortalityRecord.objects.filter(user=request.user)")])
list_view("growth_monitoring_record", [("growth_records", "GrowthMonitoring.objects.filter(user=request.user)")])
list_view("trade_record", [("trades_list", "LivestockTrade.objects.all()")])

# -- Poultry ---------------------------------------------------------------
for _n in [
    "layer_daily_egg_production", "layer_feed_record", "layer_mortality_record",
    "layer_culling_record", "layer_vaccination_record", "layer_treatment_record",
    "layer_sales_record", "layer_income_record",
]:
    list_view(_n, [("flocks", "LayerFlockIdentification.objects.filter(user=request.user)")])

list_view("broiler_daily_mortality", [
    ("flocks", "BroilerFlockIdentification.objects.filter(user=request.user)"),
    ("morts", "BroilerDailyMortality.objects.filter(user=request.user)"),
])
for _n in [
    "broiler_feed_consumption", "broiler_treatment_record", "broiler_vaccination_record",
    "broiler_growth_performance", "broiler_environmental_record",
    "broiler_water_consumption", "broiler_sales_record",
]:
    list_view(_n, [("flocks", "BroilerFlockIdentification.objects.filter(user=request.user)")])

# -- Payments --------------------------------------------------------------
add("payment", '''
    def payment(request, lesson_id):
        lesson = get_object_or_404(Tutorial, id=lesson_id)
        return JsonResponse({
            "lesson_id": lesson.id,
            "lesson": lesson.lesson,
            "unit_price": lesson.unit_price,
        })
''')
add("payment_zoom", '''
    def payment_zoom(request, meeting_id):
        meeting = get_object_or_404(ZoomMeeting, id=meeting_id)
        return JsonResponse({
            "meeting_id": meeting.id,
            "topic": meeting.topic,
            "price": meeting.price,
        })
''')

# -- Quiz / score ----------------------------------------------------------
add("score", '''
    @json_login_required
    def score(request):
        return JsonResponse({"scores": safe_values(Attempt.objects.filter(user=request.user))})
''')
add("quiz_page", '''
    def quiz_page(request):
        moderator = Moderator.objects.first()
        data = None
        if moderator:
            data = safe_values(Moderator.objects.filter(pk=moderator.pk))[0]
        return JsonResponse({"moderator": data})
''')

# -- CPD lessons -----------------------------------------------------------
add("SectionList", '''
    class SectionList(View):

        def get(self, request, lesson_id):
            ctx = {"request": request}

            sections = (
                Section.objects
                .filter(lesson_id=lesson_id)
                .order_by("-id")
            )

            payment_date = None
            if request.user.is_authenticated:
                try:
                    purchase = LessonPurchase.objects.get(
                        user=request.user,
                        lesson_id=lesson_id
                    )
                    payment_date = purchase.purchased_at
                except LessonPurchase.DoesNotExist:
                    payment_date = None

            tutorial = get_object_or_404(Tutorial, id=lesson_id)
            contact_hours_value = get_contact_hours_value(tutorial.contact_hours)
            unlock_time = get_unlock_time(payment_date, contact_hours_value)

            comments = (
                Comment.objects
                .filter(section__in=sections)
                .select_related("author")
                .order_by("-created_at")[:5]
            )

            return JsonResponse({
                "lesson_id": lesson_id,
                "tutorial": TutorialSerializer(tutorial, context=ctx).data,
                "sections": SectionSerializer(sections, many=True, context=ctx).data,
                "comments": CommentSerializer(comments, many=True, context=ctx).data,
                "payment_date": payment_date,
                "unlock_time": unlock_time,          # payment_date + contact_hours
                "contact_hours": contact_hours_value,
            })
''')

add("CommentListView", '''
    class CommentListView(View):

        def get(self, request, section_id):
            get_object_or_404(Section, id=section_id)
            comments = Comment.objects.filter(section__id=section_id).order_by('-created_at')
            return JsonResponse({
                "section_id": section_id,
                "comments": CommentSerializer(comments, many=True, context={"request": request}).data,
            })
''')

add("QuizView", '''
    class QuizView(View):

        def get(self, request, section_id):
            ctx = {"request": request}
            section = get_object_or_404(Section, id=section_id)
            questions = CpdQuestions.objects.filter(section=section)
            first_name = request.user.first_name.replace('%', '').strip()
            last_name = request.user.last_name.replace('%', '').strip()
            failed_attempts = QuizResult.objects.filter(
                user=request.user, section=section, passed='fail'
            ).count()

            return JsonResponse({
                "section": SectionSerializer(section, context=ctx).data,
                "questions": CpdQuestionsSerializer(questions, many=True, context=ctx).data,
                "combined_name": f"{first_name} {last_name}",
                "failed_attempts": failed_attempts,
                "disable_submit": failed_attempts >= 2,
            })
''')

add("QuizSubmit", '''
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
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "tutorial_id": tutorial.id if tutorial else None,
            })
''')

# -- Zoom ------------------------------------------------------------------
add("fetch_zoom_attendance", '''
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
''')

add("zoom_schedule", '''
    @user_passes_test(vet_check, login_url='vet-login')
    def zoom_schedule(request):

        # =========================================
        # CREATE MEETING
        # =========================================
        if request.method == "POST":

            topic = request.POST.get("topic")
            start_time = request.POST.get("start_time")

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
''')

# -- Second file (heat/pregnancy/feeds/gestation) --------------------------
add("add_gestation", '''
    def add_gestation(request):
        if request.method != 'POST':
            return JsonResponse({"error": "Method not allowed"}, status=405)

        form = GestationForm(request.POST)
        if form.is_valid():
            gestation = form.save()
            return JsonResponse({"success": True, "id": gestation.pk}, status=201)

        return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)
''')

# Not "pure" by shape (context is {user: user}) but carries no real data.
FORCE_REMOVE = {"broiler_flock_identification"}


# ──────────────────────────────────────────────────────────────────────────
# Detection
# ──────────────────────────────────────────────────────────────────────────
def is_pure_render(node):
    """def f(request): return render(request, 'x.html' [, {}])"""
    body = [
        n for n in node.body
        if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str))
    ]
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return False
    call = body[0].value
    if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
            and call.func.id == "render"):
        return False
    if len(call.args) < 3 and not call.keywords:
        return True
    if len(call.args) >= 3:
        ctx = call.args[2]
        return isinstance(ctx, ast.Dict) and not ctx.keys
    return False


def span(node):
    start = node.lineno
    for d in getattr(node, "decorator_list", []):
        start = min(start, d.lineno)
    return start, node.end_lineno


def convert(path: Path, dry_run: bool):
    src = path.read_text()
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)

    edits = []          # (start, end, replacement or None, name, kind)
    used_replacements = set()

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            continue
        start, end = span(node)
        name = node.name
        if name in REPLACEMENTS and name not in used_replacements:
            edits.append((start, end, REPLACEMENTS[name], name, "replaced"))
            used_replacements.add(name)
        elif isinstance(node, ast.FunctionDef) and (name in FORCE_REMOVE or is_pure_render(node)):
            edits.append((start, end, None, name, "removed"))

    for start, end, repl, _n, _k in sorted(edits, key=lambda e: e[0], reverse=True):
        lines[start - 1:end] = [repl] if repl else []

    out = "".join(lines)

    if HELPER_ANCHOR in out and used_replacements and "def safe_values(" not in out:
        out = out.replace(HELPER_ANCHOR, HELPER_ANCHOR + "\n" + HELPERS, 1)

    out = re.sub(r"\n{4,}", "\n\n\n", out)

    try:
        ast.parse(out)
    except SyntaxError as e:
        sys.exit(f"{path}: result does not parse ({e}); nothing written.")

    removed = [e[3] for e in edits if e[4] == "removed"]
    replaced = [e[3] for e in edits if e[4] == "replaced"]
    leftovers = [
        (i, l.rstrip()) for i, l in enumerate(out.splitlines(), 1)
        if re.search(r"\brender\(", l) and not l.lstrip().startswith("#")
    ]

    print(f"\n== {path} ==")
    print(f"removed  ({len(removed)}): {', '.join(removed) or '-'}")
    print(f"replaced ({len(replaced)}): {', '.join(replaced) or '-'}")
    if leftovers:
        print("STILL CALLS render() - handle by hand:")
        for i, l in leftovers:
            print(f"  line {i}: {l}")
    else:
        print("no render() calls left")

    if not dry_run:
        shutil.copy(path, path.with_suffix(path.suffix + ".bak"))
        path.write_text(out)
    return removed


def report_urls(urls_path: Path, names):
    print(f"\n== {urls_path}: patterns still pointing at removed views ==")
    hits = 0
    for i, line in enumerate(urls_path.read_text().splitlines(), 1):
        if "path(" not in line:
            continue
        for n in names:
            if re.search(rf"\b{re.escape(n)}\b", line):
                print(f"  line {i}: {line.strip()}")
                hits += 1
                break
    if not hits:
        print("  none found")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--urls", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    all_removed = []
    for f in args.files:
        all_removed += convert(f, args.dry_run)
    if args.urls:
        report_urls(args.urls, all_removed)
