from django.core.management.base import NoArgsCommand
from flows.statestore.django_store import StateModel

class Command(NoArgsCommand):
    help = "Removes expired flow state from the database (only valid if using the Django state store)"

    def handle_noargs(self, **options):
        count = StateModel.objects.remove_expired_state()
        print 'Deleted %d expired tasks\' state' % count