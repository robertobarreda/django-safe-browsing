import logging

from django.db import models, IntegrityError

from ..models import BaseProvider

logger = logging.getLogger('safebrowsing')


class GSB_BaseProvider(BaseProvider):
    GOOG_MALWARE = 1
    GOOG_REGTEST = 2
    GOOG_WHITEDOMAIN = 3
    GOOG_PHISH = 4

    LIST_TYPE = {
        GOOG_MALWARE: 'goog-malware-shavar',
        GOOG_REGTEST: 'goog-regtest-shavar',
        GOOG_WHITEDOMAIN: 'goog-whitedomain-shavar',
        GOOG_PHISH: 'googpub-phish-shavar',
    }

    class Meta:
        abstract = True


class GSB_Add(GSB_BaseProvider):
    provider_key = 'google'
    list_id = models.PositiveSmallIntegerField(
        choices=GSB_BaseProvider.LIST_TYPE.iteritems())
    add_chunk_num = models.IntegerField()
    host_key = models.CharField(max_length=8, db_index=True)
    prefix = models.CharField(max_length=64)

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'host_key', 'prefix')


class GSB_Sub(GSB_BaseProvider):
    provider_key = 'google'
    list_id = models.PositiveSmallIntegerField(
        choices=GSB_BaseProvider.LIST_TYPE.iteritems())
    add_chunk_num = models.IntegerField()
    host_key = models.CharField(max_length=8)
    prefix = models.CharField(max_length=64)
    sub_chunk_num = models.IntegerField()

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'host_key', 'prefix')
        # index_together = [('list_id', 'sub_chunk_num')]


class GSB_FullHash(GSB_BaseProvider):
    list_id = models.PositiveSmallIntegerField(
        choices=GSB_BaseProvider.LIST_TYPE.iteritems())
    add_chunk_num = models.IntegerField()
    fullhash = models.CharField(max_length=64)
    create_ts = models.PositiveIntegerField()

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'fullhash')


class GSB_rfd(GSB_BaseProvider):
   next_attempt = models.PositiveIntegerField()
   error_count = models.PositiveIntegerField()
   last_attempt = models.PositiveIntegerField()
   last_success = models.PositiveIntegerField()
