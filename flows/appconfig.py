import django


def _setup():
    from flows import statestore
    statestore.setup()


if django.VERSION >= (1, 7):
    from django.apps import AppConfig

    class FlowsAppConfig(AppConfig):
        name = 'flows'
        def ready(self):
            _setup()
else:
    _setup()
