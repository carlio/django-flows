#@PydevCodeAnalysisIgnore

DATABASES = {
        'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
        }
}

INSTALLED_APPS = ['flows', 'flows.statestore.tests']

try:
    import south
except ImportError:
    pass
else:
    INSTALLED_APPS += ['south']
