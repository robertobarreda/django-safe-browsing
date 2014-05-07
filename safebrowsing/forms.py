"""Forms for safebrowsing."""

from django import forms
from django.utils.translation import ugettext as _

from .managers import gsb_manager


class SafeBrowsingForm(forms.Form):
    url= forms.CharField()

    def clean_url(self):
        url = self.cleaned_data['url']
        if gsb_manager.lookup(url):
            raise forms.ValidationError(_('The URL has been reported'))
        return url
