from django import forms


class CoreTempForm(forms.Form):
    site_id = forms.CharField()
    mgmt_subnet = forms.CharField()


class IntDescriptionForm(forms.Form):
    site_id = forms.CharField()
    mgmt_subnet = forms.GenericIPAddressField()


class IosUpgradeForm(forms.Form):
    site_id = forms.CharField()