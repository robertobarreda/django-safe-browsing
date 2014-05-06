import logging

from django.db import models, IntegrityError

logger = logging.getLogger('safebrowsing.gsb')


class GSB(models.Model):
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

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, auto_now_add=True)

    class Meta:
        abstract = True


class GSB_Add(GSB):
    list_id = models.PositiveSmallIntegerField(
        choices=GSB.LIST_TYPE.iteritems(), db_index=True)
    add_chunk_num = models.IntegerField()
    host_key = models.CharField(max_length=8, db_index=True)
    prefix = models.CharField(max_length=64)

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'host_key', 'prefix')


class GSB_Sub(GSB):
    add_chunk_num = models.OneToOneField(
        GSB_Add, primary_key=True, related_name='sub_chunk_num')
    sub_chunk_num = models.IntegerField(db_index=True)


class GSB_FullHash(GSB):
    list_id = models.PositiveSmallIntegerField(
        choices=GSB.LIST_TYPE.iteritems(), db_index=True)
    add_chunk_num = models.IntegerField()
    fullhash = models.CharField(max_length=64)

    class Meta:
        unique_together = ('list_id', 'add_chunk_num', 'fullhash')


class GSB_RFD(GSB):
   next_attempt = models.PositiveIntegerField()
   error_count = models.PositiveIntegerField()
   last_attempt = models.PositiveIntegerField()
   last_success = models.PositiveIntegerField()
