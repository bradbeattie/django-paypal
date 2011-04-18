#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from paypal.pro.fields import CreditCardField, CreditCardExpiryField, CreditCardCVV2Field, CountryField
from paypal.pro.exceptions import PayPalFailure

class PaymentForm(forms.Form):
    """Form used to process direct payments."""
    firstname = forms.CharField(255, label=_("First Name"))
    lastname = forms.CharField(255, label=_("Last Name"))

    street = forms.CharField(255, label=_("Street Address"))
    street2 = forms.CharField(255, label="", required=False)
    city = forms.CharField(255, label=_("City"))
    state = forms.CharField(255, label=_("State / Province"))
    countrycode = CountryField(label=_("Country"), initial="US")
    zip = forms.CharField(32, label=_("Postal / Zip Code"))

    acct = CreditCardField(label=_("Credit Card Number"))
    expdate = CreditCardExpiryField(label=_("Expiration Date"))
    cvv2 = CreditCardCVV2Field(label=_("Card Security Code"), help_text=_("You can find the 3-digit code on the back of your Visa/MasterCard/Discover card, next to your signature, or a small 4-digit number printed on the front of your American Express card."))

    def process(self, ipaddress, user, item):
        """Process a PayPal direct payment."""
        from paypal.pro.helpers import PayPalWPP
        wpp = PayPalWPP(ipaddress, user)
        params = self.cleaned_data
        params['creditcardtype'] = self.fields['acct'].card_type
        params['expdate'] = self.cleaned_data['expdate'].strftime("%m%Y")
        params['ipaddress'] = ipaddress
        params.update(item)

        try:
            # Create single payment:
            if 'billingperiod' not in params:
                nvp_obj = wpp.doDirectPayment(params)
            # Create recurring payment:
            else:
                nvp_obj = wpp.createRecurringPaymentsProfile(params, direct=True)
        except PayPalFailure:
            return None
        return nvp_obj

class ConfirmForm(forms.Form):
    """Hidden form used by ExpressPay flow to keep track of payer information."""
    token = forms.CharField(max_length=255, widget=forms.HiddenInput())
    payerid = forms.CharField(max_length=255, widget=forms.HiddenInput())

class ExpressPaymentForm(ConfirmForm):
    def process(self, ipaddress, user, item):
        """Process a PayPal ExpressCheckout payment."""
        from paypal.pro.helpers import PayPalWPP
        wpp = PayPalWPP(ipaddress, user)
        params = self.cleaned_data
        params.update(item)

        try:
            # Create single payment:
            if 'billingperiod' not in params:
                nvp_obj = wpp.doExpressCheckoutPayment(params)
            # Create recurring payment:
            else:
                nvp_obj = wpp.createRecurringPaymentsProfile(params)
        except PayPalFailure:
            return None
        return nvp_obj
