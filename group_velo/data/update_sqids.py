import os
import shutil

from django.utils.text import slugify
from sqids.sqids import Sqids

from config.settings.base import SQIDS_ALPHABET, SQIDS_MIN_LEN
from group_velo.clubs.models import Club
from group_velo.users.models import User

clubs = Club.objects.all()
users = User.objects.all()
sqids = Sqids(alphabet=SQIDS_ALPHABET, min_length=SQIDS_MIN_LEN)
for club in clubs:
    club.slug = slugify(f"{club.name}") + f"-{sqids.encode([club.id])}"
    club.save()
for user in users:
    user.slug = slugify(f"{user.name}") + f"-{sqids.encode([user.id])}"
    user.save()


clubs = Club.objects.all()
users = User.objects.all()

for club in clubs:
    old_slug = slugify(f"{club.name}-{club.id}")
    new_slug = slugify(f"{club.name}-f{Sqids(min_length=16).encode([club.id])}")

    old_path = os.path.join("/app/group_velo/media/Club/", old_slug)
    new_path = os.path.join("/app/group_velo/media/Club/", new_slug)

    try:
        # Rename the folder
        shutil.move(old_path, new_path)
        # Update the slug value in the database
    except FileNotFoundError:
        print(f"Folder '{old_slug}' not found")
    except Exception as e:
        print(f"An error occurred: {e}")


for user in users:
    old_slug = slugify(f"{user.name}-{user.id}")
    new_slug = slugify(f"{user.name}-f{Sqids(min_length=16).encode([user.id])}")

    old_path = os.path.join("/app/group_velo/media/CustomUser/", old_slug)
    new_path = os.path.join("/app/group_velo/media/CustomUser/", new_slug)

    try:
        # Rename the folder
        shutil.move(old_path, new_path)
        # Update the slug value in the database
        print(f"Renamed folder from '{old_slug}' to '{new_slug}'")
    except FileNotFoundError:
        print(f"Folder '{old_slug}' not found")
    except Exception as e:
        print(f"An error occurred: {e}")
