#@PydevCodeAnalysisIgnore

DATABASES = {
        'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
        }
}

INSTALLED_APPS = ['flows', 'flows.statestore.tests']

SECRET_KEY = 'flow_tests'

TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

_optional = ['django_jenkins', 'south']
for app in _optional:
    try:
        __import__(app)
    except ImportError:
        pass
    else:
        INSTALLED_APPS.append(app)
