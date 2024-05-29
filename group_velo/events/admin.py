from django.contrib import admin

from .models import (
    Event,
    EventOccurence,
    EventOccurenceMember,
    EventOccurenceMemberWaitlist,
    EventOccurenceMessage,
    EventOccurenceMessageVisit,
)

admin.site.register(Event)
admin.site.register(EventOccurence)
admin.site.register(EventOccurenceMember)
admin.site.register(EventOccurenceMemberWaitlist)
admin.site.register(EventOccurenceMessage)
admin.site.register(EventOccurenceMessageVisit)
