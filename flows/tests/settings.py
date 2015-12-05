import django

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = ['flows', 'flows.statestore.tests', 'django_nose']

SECRET_KEY = 'flow_tests'

if django.VERSION < (1, 6):
    TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

MIDDLEWARE_CLASSES = []
ROOT_URLCONF = ''

if django.VERSION < (1, 7):
    try:
        __import__('south')
    except ImportError:
        pass
    else:
        INSTALLED_APPS.append('south')
