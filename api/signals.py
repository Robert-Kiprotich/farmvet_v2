from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MilkCollectionClerk, MilkCollectionCooler, Supplier

@receiver(post_save, sender=MilkCollectionClerk)
def create_cooler_record(sender, instance, created, **kwargs):
    if created:
        # Try to get supplier name from Supplier model
        try:
            supplier = Supplier.objects.get(supply_number=instance.supply_number)
            supplier_name = supplier.name  # <-- use 'name' field
        except Supplier.DoesNotExist:
            supplier_name = "Unknown Supplier"

        # Create MilkCollectionCooler record
        MilkCollectionCooler.objects.create(
            user=instance.user,
            clerk_record=instance,
            date=instance.date,
            supply_number=instance.supply_number,
            total_kg_supplied=instance.total_kg_supplied,
            name_of_supplier=supplier_name,  # automatically bound
            collection_status='Accepted',     # default
            reason='N/A',                     # default
            remarks=''
        )