from django.db import models


##############################################################################
# Provider settings
##############################################################################

class ProviderSettings(models.Model):
    PROVIDERS = (
        ('google', 'Google'),  # https://developers.google.com/safe-browsing/
        ('phishtank', 'Phishtank'),  # http://www.phishtank.com/
    )

    provider = models.CharField(max_length=10, choices=PROVIDERS)
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        unique_together = ('provider', 'key', 'value')



##############################################################################
# Base Provider
##############################################################################

class BaseProvider(models.Model):
    provider_key = None
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        abstract = True
