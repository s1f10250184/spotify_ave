import os
import dj_database_url
from .settings import *

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
hostname = os.environ('RENDER_EXTERNAL_HOSTNAME')
if hostname:
    ALLOWED_HOSTS.append(hostname)

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

DATABASES = {
    'default': dj_database_url.config()
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


