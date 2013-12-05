from django.db import models


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


class BaseProvider(models.Model):
    provider_key = None
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        abstract = True


class GSBAdd(BaseProvider):
    provider_key = 'google'
    list_id = models.IntegerField()
    add_chunk_num = models.IntegerField()
    host_key = models.CharField(max_length=8, db_index=True)
    prefix = models.CharField(max_length=64)

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'host_key', 'prefix')

class GSBSub(BaseProvider):
    provider_key = 'google'
    list_id = models.IntegerField()
    add_chunk_num = models.IntegerField()
    sub_chunk_num = models.IntegerField()
    host_key = models.CharField(max_length=8)
    prefix = models.CharField(max_length=64)

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'host_key', 'prefix')
        index_together = [('list_id', 'sub_chunk_num')]

class GSBFullHash(BaseProvider):
    list_id = models.IntegerField()
    add_chunk_num = models.IntegerField()
    fullhash = models.CharField(max_length=64)
    create_ts = models.PositiveIntegerField()

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'fullhash')

class GSBrfd(BaseProvider):
   next_attempt = models.PositiveIntegerField()
   error_count = models.PositiveIntegerField()
   last_attempt = models.PositiveIntegerField()
   last_success = models.PositiveIntegerField()

class Phishtank(BaseProvider):
    provider_key = 'phishtank'
