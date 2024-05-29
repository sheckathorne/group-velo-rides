from enum import Enum

from django.db import models


class PrivacyLevel(models.IntegerChoices):
    Open = (1, "Open")
    SemiPrivate = (2, "Semi-private")
    Private = (3, "Private")


class DropDesignation(models.IntegerChoices):
    Drop = (1, "Drop")
    NoDrop = (2, "No-Drop")


class RecurrenceFrequency(models.IntegerChoices):
    Zero = (0, "None")
    Daily = (1, "Daily")
    Weekly = (7, "Weekly")


class GroupClassification(models.TextChoices):
    A = ("A", "A")
    B = ("B", "B")
    C = ("C", "C")
    D = ("D", "D")
    N = ("N", "Novice")
    NA = ("NA", "None")


class MemberType(models.IntegerChoices):
    Creator = (1, "Creator")
    Admin = (2, "Admin")
    RideLeader = (3, "Ride Leader")
    RouteContributor = (4, "Route Contributor")
    PaidMember = (5, "Paid Member")
    UnpaidMember = (6, "Unpaid Member")
    NonMember = (7, "Non-Member")


class SurfaceType(models.TextChoices):
    Road = ("R", "Road")
    Gravel = ("G", "Gravel")
    OffRoad = ("O", "Off Road")
    Mixed = ("M", "Mixed")


class RoleType(models.IntegerChoices):
    Creator = (0, "Ride Creator")
    Leader = (1, "Ride Leader")
    Rider = (2, "Rider")


class EmailType(Enum):
    CANCEL = 1
    MODIFY = 2


class MemberListType(Enum):
    RIDE = 1
    WAITLIST = 2


class RideType(models.IntegerChoices):
    Available = (0, "available_rides")
    Registered = (1, "my_rides")
    Waitlist = (3, "my_waitlist")


class RequestStatus(models.IntegerChoices):
    Pending = (1, "Pending")
    Approved = (2, "Approved")
    Denied = (3, "Denied")


class Relationship(models.IntegerChoices):
    SpousePartner = (1, "Spouse/Partner")
    Mother = (2, "Mother")
    Father = (3, "Father")
    Sister = (4, "Sister")
    Brother = (5, "Brother")
    Daughter = (6, "Daughter")
    Son = (7, "Son")
    Ohter = (8, "Other")


class EventMemberType(models.IntegerChoices):
    Members = (
        MemberType(MemberType.PaidMember).value,
        "Current Members",
    )
    Open = (
        MemberType(MemberType.NonMember).value,
        "Open",
    )


class NotificationType(models.IntegerChoices):
    RideChange = (0, "Ride Modified")
    RideCancel = (1, "Ride Canceled")
    WaitlistPromotion = (2, "Waitlist Promotion")
    RideRegistrationDeleted = (3, "Ride Registration Canceled")
    WaitlistRegistrationDeleted = (4, "Waitlist Registration Deleted")
