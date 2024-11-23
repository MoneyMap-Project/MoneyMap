from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from decouple import config


class Command(createsuperuser.Command):
    help = "Create a superuser, and allow password to be provided from .env"

    def handle(self, *args, **options):
        # Retrieve username and password from .env
        username = config("SUPERUSER_USERNAME", default=None)
        password = config("SUPERUSER_PASSWORD", default=None)
        database = options.get("database")

        if not username or not password:
            raise CommandError(
                "SUPERUSER_USERNAME and SUPERUSER_PASSWORD must be set in the .env file"
            )

        # Check if the user already exists
        if self.UserModel._default_manager.db_manager(database).filter(
            username=username
        ).exists():
            self.stdout.write(f"Superuser '{username}' already exists.")
            return

        # Create the superuser
        options["username"] = username
        options["password"] = password
        super(Command, self).handle(*args, **options)

        # Set the password explicitly
        user = self.UserModel._default_manager.db_manager(database).get(
            username=username
        )
        user.set_password(password)
        user.save()
        self.stdout.write(f"Superuser '{username}' created successfully.")
