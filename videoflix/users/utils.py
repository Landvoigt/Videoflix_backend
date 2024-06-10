import string
import random

from django.contrib.auth.models import User

def generate_unique_username(base='user'):
    while True:
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        username = f'{base}_{random_suffix}'
        if not User.objects.filter(username=username).exists():
            return username