from django.contrib.auth.models import AbstractUser
from django.db import models

# LIETOTĀJU KONTU PĀRVALDĪBA
# Šis modelis paplašina standarta Django lietotāju ar specifiskām lomām un piederību uzņēmumam.
# Tas ļauj sistēmai kontrolēt piekļuvi datiem, balstoties uz darbinieka lomu.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrators'),
        ('CEO', 'Uzņēmuma vadītājs'),
        ('WAREHOUSE_MANAGER', 'Noliktavas vadītājs'),
        ('MECHANIC', 'Mehāniķis'),
    )
    username = models.CharField(max_length=20, default='', unique=True)
    # email = models.EmailField(unique=True)
    
    # This is the crucial line:
    # USERNAME_FIELD = 'email'
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MECHANIC')
    email = models.CharField(max_length=20, default='')
