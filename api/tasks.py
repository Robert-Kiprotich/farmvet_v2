from celery import shared_task
from .models import VaccinationRecord


@shared_task
def generate_certificate_task(record_id):
    from .views import (
    generate_vaccination_certificate,
    save_certificate_to_media
)
    record = VaccinationRecord.objects.get(pk=record_id)

    pdf_bytes = generate_vaccination_certificate(record)
    saved_path = save_certificate_to_media(record, pdf_bytes)

    VaccinationRecord.objects.filter(pk=record_id).update(
        certificate_file=saved_path
    )