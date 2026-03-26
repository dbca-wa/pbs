from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
import logging
import os

from swingers.models.auth import Audit
from swingers import models
from django.utils import timezone
from django.db.models import Max, Q
from smart_selects.db_fields import ChainedForeignKey

from pbs.document.fields import ContentTypeRestrictedFileField
from pbs.document.utils import get_dimensions
from pbs.prescription.models import Prescription
import datetime
from functools import reduce

# from south.modelsinspector import add_introspection_rules
# add_introspection_rules([], ["^pbs\.document\.fields\.ContentTypeRestrictedFileField"])

logger = logging.getLogger(__name__)


def content_file_name(self, filename):
    if filename.rsplit('.')[-1] == "zip":
        extension = "zip"
    else:
        extension = "pdf"
    return "uploads/{0}/{0}_{1}_{2}_{3}.{4}".format(
        str(self.prescription.season).strip().replace("/", "_"),
        self.prescription.burn_id,
        self.descriptor.strip().replace(" ", "_"),
        timezone.localtime(self.document_created).isoformat(
        ).rsplit(".")[0].replace(":", "")[:-7],
        extension)



class DocumentCategory(models.Model):
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class CategoryManager(models.Manager):
    use_for_related_fields = True

    def _query_by_names(self, *names):
        return reduce(lambda x, y: x | y,
                      (Q(name__iexact=name) for name in names),
                      Q())

    def not_tag_names(self, *names):
        return self.get_queryset().exclude(self._query_by_names(*names))

    def tag_names(self, *names):
        return self.get_queryset().filter(self._query_by_names(*names))



class DocumentTag(models.Model):
    name = models.CharField(verbose_name="Document Tag", max_length=200)
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT)
    objects = CategoryManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class TagManager(models.Manager):
    use_for_related_fields = True

    def _query_by_names(self, *names):
        return reduce(lambda x, y: x | y,
                      (Q(tag__name__iexact=name) for name in names),
                      Q())

    def not_tag_names(self, *names):
        return self.get_queryset().exclude(self._query_by_names(*names))

    def tag_names(self, *names):
        return self.get_queryset().filter(self._query_by_names(*names))

    def __getattr__(self, name):
        if name[:4] == "tag_":
            qs = self.get_queryset().filter(
                tag__name__iexact=name[4:].replace("_", " "))
            qs.modified = qs.aggregate(Max('modified'))["modified__max"]
            return qs
        else:
            return super(TagManager, self).__getattr__(name)

    def printable(self):
        """
        Return the set of printable documents. This removes any zip files from
        the set of documents.
        """
        qs = self.get_queryset()
        return filter(lambda x: x.filename.endswith('.pdf'), qs)



class Document(Audit):
    prescription = models.ForeignKey(
        Prescription, null=True,
        help_text="Prescription that this document belongs to", on_delete=models.PROTECT)
    category = models.ForeignKey(DocumentCategory, related_name="documents", on_delete=models.PROTECT)
    tag = ChainedForeignKey(
        DocumentTag, chained_field="category", chained_model_field="category",
        show_all=False, auto_choose=True, verbose_name="Descriptor", on_delete=models.PROTECT)
    custom_tag = models.CharField(
        max_length=64, blank=True, verbose_name="Custom Descriptor")
    document = ContentTypeRestrictedFileField(
        upload_to=content_file_name, max_length=200,
        content_types=['application/pdf', 'image/tiff', 'image/tif',
                       'image/jpeg', 'image/jpg', 'image/gif', 'image/png',
                       'application/zip', 'application/x-zip-compressed'],
        help_text='Acceptable file types: pdf, tiff, jpg, gif, png, zip')

    document_created = models.DateTimeField(
        verbose_name="Date Document Created", default=timezone.now, editable=True, null=True, blank=True)

    document_archived = models.BooleanField(default=False, verbose_name="Archived Document")

    objects = TagManager()

    def save(self, *args, **kwargs):
        super(Document, self).save(*args, **kwargs)
        # confirm that file is written to filesystem, if not remove the record
        if not self.exists:
            fname = self.document.name
            Document.objects.get(id=self.id).delete()
            raise Exception('ERROR: File not created on filesystem {}'.format(fname))
        return

    @property
    def descriptor(self):
        if self.custom_tag:
            return "Other ({0})".format(self.custom_tag)
        else:
            return self.tag.name

    @property
    def dimensions(self):
        return get_dimensions(self.document.path)

    @property
    def filename(self):
        try:
            return os.path.basename(self.document.path)
        except:
            return None

    @property
    def exists(self):
        """
        Check if file exists on the file system
        """
        try:
            return os.path.exists(self.document.file.name)
        except:
            return False


    @property
    def is_zipped(self):
        return self.filename.endswith('.zip')

    class Meta:
        ordering = ['tag', 'document']
        permissions = (
            ("archive_document", "Can archive documents"),
        )

    def __str__(self):
        return "{0} - {1}".format(self.prescription, self.document.name)

import reversion
reversion.register(Document)