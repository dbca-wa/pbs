from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.utils import quote
from django.urls import reverse


class DetailChangeList(ChangeList):
    def url_for_result(self, result):
        if self.model_admin.changelist_link_detail:
            pk = getattr(result, self.pk_attname)
            return reverse('admin:%s_%s_detail' % (self.opts.app_label,
                                                   self.opts.model_name),
                           args=(quote(pk),),
                           current_app=self.model_admin.admin_site.name)
        else:
            return super(DetailChangeList, self).url_for_result(result)
