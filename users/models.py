from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError


# =====================================================
# Custom User Manager
# =====================================================
class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email is required"))

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Roles.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True"))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True"))

        return self.create_user(email, password, **extra_fields)


# =====================================================
# Custom User Model
# =====================================================
class CustomUser(AbstractUser):
    username = None

    # -------------------------------------------------
    # Roles
    # -------------------------------------------------
    class Roles(models.TextChoices):
        USER = "user", _("User")
        OWNER = "owner", _("Hostel Owner")
        MESS_OWNER = "mess_owner", _("Mess Owner")
        ADMIN = "admin", _("Admin")

    email = models.EmailField(unique=True, db_index=True)

    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(regex=r"^\+?1?\d{9,15}$", message=_("Enter a valid phone number"))],
        unique=True,
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.USER,
        db_index=True,
    )

    # -------------------------------------------------
    # Profile
    # -------------------------------------------------
    profile_image = models.ImageField(upload_to="users/profile_images/", blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=500)

    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # -------------------------------------------------
    # Verification & status
    # -------------------------------------------------
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    kyc_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    # -------------------------------------------------
    # Activity tracking
    # -------------------------------------------------
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_active = models.DateTimeField(blank=True, null=True)
    registered_at = models.DateTimeField(default=timezone.now)

    # -------------------------------------------------
    # Django auth config
    # -------------------------------------------------
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    # -------------------------------------------------
    # Methods
    # -------------------------------------------------
    def __str__(self):
        return f"{self.email} ({self.role})"

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active"])

    def clean(self):
        """Extra validation"""
        if self.role in [self.Roles.OWNER, self.Roles.MESS_OWNER] and not self.phone_verified:
            raise ValidationError(_("Owner must have verified phone number"))

    # -------------------------------------------------
    # Role helpers
    # -------------------------------------------------
    @property
    def is_user(self):
        return self.role == self.Roles.USER

    @property
    def is_owner(self):
        return self.role == self.Roles.OWNER

    @property
    def is_mess_owner(self):
        return self.role == self.Roles.MESS_OWNER

    @property
    def is_admin(self):
        return self.role == self.Roles.ADMIN

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]
