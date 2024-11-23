from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = "Create a superuser, and allow password to be provided"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--password",
            dest="password",
            default=None,
            help="Specifies the password for the superuser.",
        )
        parser.add_argument(
            "--preserve",
            dest="preserve",
            default=False,
            action="store_true",
            help="Exit normally if the user already exists.",
        )

    def handle(self, *args, **options):
        password = options.get("password")
        username = options.get("username")
        database = options.get("database")

        if password and not username:
            raise CommandError(
                "--username is required if specifying --password")

        if username and options.get("preserve"):
            exists = (
                self.UserModel._default_manager.db_manager(database)
                .filter(username=username)
                .exists()
            )
            if exists:
                self.stdout.write(
                    "User exists, exiting normally due to --preserve")
                return

        # Call the parent handle method to create the user
        super(Command, self).handle(*args, **options)

        # Try to retrieve and set the password for the created user
        try:
            user = self.UserModel._default_manager.db_manager(database).get(
                username=username
            )
            if password:
                user.set_password(password)
                user.save()
        except self.UserModel.DoesNotExist:
            raise CommandError(
                f"Superuser with username '{username}' was not created.")

