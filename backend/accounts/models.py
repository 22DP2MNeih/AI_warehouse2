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

    company = models.ForeignKey('inventory.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')

    def __str__(self):
        org = f"{self.company.name}" if self.company else "Nav uzņēmuma"
        if self.warehouse:
            org += f" - {self.warehouse.name}"
        return f"{self.username} ({self.get_role_display()}) @ {org}"
