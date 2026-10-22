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
    
@auth_required
def tutorial(request):
    return json_page(request, 'portals/reports/cpd.html')
@auth_required
def tutorialtest(request):
    
    return json_page(request, 'portals/reports/cpdtest.html')
@auth_required
def lesson(request):
    return json_page(request, 'portals/reports/lessons.html')
    
class TutorialCreate(generics.CreateAPIView):
    queryset = Tutorial.objects.all()
    serializer_class = TutorialSerializer
    permission_classes = [Is_Vet]


class TutorialList(generics.ListAPIView):

    serializer_class = TutorialSerializer
    permission_classes = [Is_Vet]
    pagination_class = PageNumberPagination

    def get_queryset(self):

        user = self.request.user

        purchases = LessonPurchase.objects.filter(
            lesson=OuterRef('pk'),
            user=user
        )

        return Tutorial.objects.annotate(
            has_paid=Exists(purchases)
        ).order_by('-created_at')
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
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

# class SectionList(generics.ListAPIView):
#     serializer_class = SectionSerializer
#     permission_classes = [Is_Vet]

#     def get_queryset(self):
#         lesson_id = self.kwargs['lesson_id']
#         return Section.objects.filter(lesson_id=lesson_id).order_by('-id')



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
            try:
                purchase = LessonPurchase.objects.get(user=request.user, lesson_id=lesson_id)
                payment_date = purchase.purchased_at
            except LessonPurchase.DoesNotExist:
                return JsonResponse({"locked": True, "reason": "payment_required"})

            tutorial = get_object_or_404(Tutorial, id=lesson_id)
            contact_hours_value = get_contact_hours_value(tutorial.contact_hours)
            unlock_time = get_unlock_time(payment_date, contact_hours_value)

            if unlock_time is None or now() < unlock_time:
                return JsonResponse({
                    "locked": True,
                    "reason": "time_locked",
                    "unlock_time": unlock_time.isoformat() if unlock_time else None,
                })

            section = (
                Section.objects
                .filter(lesson_id=lesson_id)
                .order_by("-id")
                .first()
            )

            if not section:
                return JsonResponse({"locked": True, "reason": "no_sections"}, status=404)

            try:
                exam_url = reverse('questions-list', kwargs={'section_id': section.id})
            except NoReverseMatch as e:
                return JsonResponse({"locked": True, "reason": "config_error", "detail": str(e)}, status=500)

            return JsonResponse({"locked": False, "exam_url": exam_url})

        except Exception as e:
            return JsonResponse({"locked": True, "reason": "server_error", "detail": str(e)}, status=500)
def download_file(request, section_id):
    try:
        section = Section.objects.get(id=section_id)
        file_path = section.file.path  # Get the absolute file path
        
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
      
        
#cpd qustions 

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
    
@auth_required
def result(request):
    return json_page(request, 'portals/reports/myresults.html')


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

    registration_number = request.user.registration_number
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

    registration_number = request.user.registration_number
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
class QuizResultList(generics.ListAPIView):
    serializer_class = QuizResultSerializer
    permission_classes = [Is_Vet]
    
    def get_queryset(self):
        user=self.request.user
        return QuizResult.objects.filter(user=user).order_by('-id')
    