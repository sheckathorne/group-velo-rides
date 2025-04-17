from django.db import models

# from group_velo.clubs.models import Club


class SubscriptionLevel(models.Model):
    pass


class Subscription(models.Model):
    pass


#  club = models.ForeignKey(Club, on_delete=models.CASCADE)
#  subscription_level = models.ForeignKey(SubscriptionLevel, on_delete=models.CASCADE)
#  auto_renew = models.BooleanField("Auto Renew")
#  start_date = models.DateField("Start Date")
