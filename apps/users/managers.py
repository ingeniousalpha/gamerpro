from django.contrib.auth.models import BaseUserManager
from django.db import transaction


class UserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email,and password.
        """
        print('_create_user')
        if not email:
            raise ValueError('User should have valid email')
        try:
            with transaction.atomic():
                groups = extra_fields.pop('groups', [])
                user_permissions = extra_fields.pop('user_permissions', [])
                user = self.model(email=email, **extra_fields)
                user.set_password(password)
                for group in groups:
                    user.groups.set(group)
                for permission in user_permissions:
                    user.user_permissions.set(permission)
                user.save(using=self._db)
                print("i am creating new user")
                return user
        except:
            raise

    def create_user(self, email, password=None, **extra_fields):
        print('create_user')
        # extra_fields.setdefault('is_staff', False)
        # extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password=password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        print('create_superuser')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, password=password, **extra_fields)

    def active(self):
        return self.filter(is_active=True)

    def have_completed_application(self):
        return self.filter(has_completed_application=True)
