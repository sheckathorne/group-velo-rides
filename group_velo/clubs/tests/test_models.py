import datetime
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from group_velo.clubs.models import Club, ClubMembership, ClubMembershipRequest
from group_velo.data.choices import MemberType, RequestStatus


def truncate_tables():
    get_user_model().objects.all().delete()
    Club.objects.all().delete()
    ClubMembership.objects.all().delete()
    ClubMembershipRequest.objects.all().delete()


class ClubModelTest(TestCase):
    def setUp(self, private=False):
        truncate_tables()

        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpassword", email="testemail@email.com"
        )
        self.another_user = get_user_model().objects.create_user(
            username="testuser2",
            password="testpassword2",
            email="testanotheremail@email.com",
        )
        self.club = Club.objects.create(
            name="Test Club",
            url="http://example.com",
            city="City",
            state="CA",
            zip_code="12345",
            latitude=12.345678,
            longitude=98.765432,
            founded_date="2020-01-01",
            created_by=self.user,
            slug="test-club",
            description="Test club description",
            private=private,
        )

    def test_image_upload_to(self):
        image_path = self.club.image_upload_to(instance="test.jpg")
        self.assertEqual(image_path, "Club/test-club/test.jpg")

    def test_get_logo_with_logo(self):
        self.club.logo = "test/logo.jpg"
        self.club.save()
        logo_url = self.club.get_logo
        self.assertEqual(logo_url, "/media/test/logo.jpg")

    def test_get_logo_without_logo(self):
        logo_url = self.club.get_logo
        self.assertEqual(logo_url, "/media/default/bicycle.png")

    def test_save_with_invalid_zip_code(self):
        self.club.zip_code = "invalid"
        with self.assertRaises(ValidationError):
            self.club.save()

    def test_save_with_valid_zip_code(self):
        self.club.zip_code = "12345"
        self.club.save()
        self.assertIsNotNone(self.club.latitude)
        self.assertIsNotNone(self.club.longitude)

    def test_member_count(self):
        ClubMembership.objects.all().delete()
        ClubMembership.objects.create(
            user=self.user,
            club=self.club,
            active=True,
            membership_expires=datetime.datetime(
                year=9999,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                tzinfo=datetime.UTC,
            ),
            membership_type=MemberType.PaidMember,
        )
        self.assertEqual(self.club.member_count, 1)

    def test_active_memberships(self):
        ClubMembership.objects.all().delete()
        ClubMembership.objects.create(
            user=self.user,
            club=self.club,
            active=True,
            membership_expires=datetime.datetime(
                year=9999,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                tzinfo=datetime.UTC,
            ),
            membership_type=MemberType.PaidMember,
        )
        ClubMembership.objects.create(
            user=self.another_user,
            club=self.club,
            active=False,
            membership_expires=datetime.datetime(
                year=9999,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                tzinfo=datetime.UTC,
            ),
            membership_type=MemberType.PaidMember,
        )
        active_members = self.club.active_memberships()
        self.assertEqual(active_members.count(), 1)

    def test_membership_requests(self):
        ClubMembershipRequest.objects.all().delete()
        ClubMembershipRequest.objects.create(user=self.user, club=self.club, status=RequestStatus.Pending)
        membership_requests = self.club.membership_requests()
        self.assertEqual(membership_requests.count(), 1)

    def test_pending_requests(self):
        ClubMembershipRequest.objects.all().delete()
        ClubMembershipRequest.objects.create(user=self.user, club=self.club, status=RequestStatus.Pending)
        pending_requests = self.club.pending_requests()
        self.assertEqual(pending_requests.count(), 1)

    def test_active_and_current_member_count(self):
        ClubMembership.objects.all().delete()
        ClubMembership.objects.create(
            user=self.user,
            club=self.club,
            active=True,
            membership_expires=datetime.datetime(
                year=9999,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                tzinfo=datetime.UTC,
            ),
            membership_type=MemberType.PaidMember,
        )
        active_and_current_member_count = self.club.active_and_current_member_count
        self.assertEqual(active_and_current_member_count, 1)

    def test_club_admins(self):
        ClubMembership.objects.all().delete()
        admin_membership = ClubMembership.objects.create(
            user=self.user,
            club=self.club,
            active=True,
            membership_type=MemberType.Admin,
            membership_expires=datetime.datetime(
                year=9999,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                tzinfo=datetime.UTC,
            ),
        )
        admins = self.club.club_admins
        self.assertEqual(admins.count(), 1)
        self.assertIn(admin_membership, admins)


class ClubMembershipModelTest(TestCase):
    def setUp(self):
        truncate_tables()
        self.user = get_user_model().objects.create_user(username="testuser", password="testpassword")
        self.club = Club.objects.create(
            name="Test Club",
            url="http://example.com",
            city="City",
            state="CA",
            zip_code="12345",
            latitude=12.345678,
            longitude=98.765432,
            founded_date="2020-01-01",
            created_by=self.user,
            slug="test-club",
            description="Test club description",
            private=True,
        )

        # Creating a club automatically creates a club membership object for the user
        self.membership = ClubMembership.objects.get(user=self.user, club=self.club)

    def test_is_expired(self):
        self.assertFalse(self.membership.is_expired())

        # Expire membership and test again
        self.membership.membership_expires = timezone.now() - timedelta(days=1)
        self.membership.save()
        self.assertTrue(self.membership.is_expired())

    def test_is_inactive(self):
        self.assertFalse(self.membership.is_inactive())

        # Deactivate membership and test again
        self.membership.active = False
        self.membership.save()
        self.assertTrue(self.membership.is_inactive())

    def test_level(self):
        self.assertEqual(self.membership.level, "Creator")

    def test_can_create_club_rides(self):
        self.assertTrue(self.membership.can_create_club_rides)

        # Set membership type to Unpaid Member and test again
        self.membership.membership_type = MemberType.UnpaidMember
        self.membership.save()
        self.assertFalse(self.membership.can_create_club_rides)

    def test_expired(self):
        self.assertFalse(self.membership.expired)

        # Expire membership and test again
        self.membership.membership_expires = timezone.now() - timedelta(days=1)
        self.membership.save()
        self.assertTrue(self.membership.expired)

    def test_inactive(self):
        self.assertFalse(self.membership.inactive)

        # Deactivate membership and test again
        self.membership.active = False
        self.membership.save()
        self.assertTrue(self.membership.inactive)

    def test_user_can_manage_club(self):
        self.assertTrue(self.membership.user_can_manage_club)

        # Set membership type to Paid Member and test again
        self.membership.membership_type = MemberType.PaidMember
        self.membership.save()
        self.assertFalse(self.membership.user_can_manage_club)

    def test_membership_type_label(self):
        self.assertEqual(self.membership.membership_type_label, "Creator")
