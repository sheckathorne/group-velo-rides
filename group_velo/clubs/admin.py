from django.contrib import admin

from .models import Club, ClubMembership, ClubMembershipRequest, ClubRideClassificationLimit, ClubVerificationRequest

admin.site.register(Club)
admin.site.register(ClubMembership)
admin.site.register(ClubMembershipRequest)
admin.site.register(ClubRideClassificationLimit)
admin.site.register(ClubVerificationRequest)
