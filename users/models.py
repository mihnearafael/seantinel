from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('analist_ong', 'Analist ONG'),
        ('analist_cercetare', 'Analist Cercetare'),
        ('inspector_mediu', 'Inspector de Mediu'),
        ('garda_coasta', 'Gardă de Coastă'),
        ('politia_frontiera', 'Poliția de Frontieră'),
        ('autoritate_navala', 'Autoritate Navală'),
        ('investigator', 'Investigator'),
        ('supervizor', 'Supervizor'),
        ('administrator', 'Administrator Sistem'),
        ('altul', 'Altul'),
    ]

    institution_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Instituție")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, blank=True, null=True, verbose_name="Rol")

    def __str__(self):
        return f"{self.username} ({self.institution_name})"

    def get_role_display_ro(self):
        return dict(self.ROLE_CHOICES).get(self.role, "Nespecificat")