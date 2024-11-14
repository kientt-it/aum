from odoo import models, fields, _
from odoo.exceptions import ValidationError
import logging
import socket
import requests
from datetime import datetime, timedelta
from werkzeug import urls

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"
    BASE_URL = "https://mtf.onepay.vn/paygate/vpcpay.op?"

    onepay_query_status = fields.Boolean(string="OnePay Query Status", default=False)
    onepay_query_start_time = fields.Datetime(string="OnePay Query Start Time")

    def _get_specific_rendering_values(self, processing_values):
        self.ensure_one()
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "onepay":
            return res

        base_url = self.provider_id.get_base_url().replace("http://", "https://", 1)
        int_amount = int(self.amount)

        ip_address = socket.gethostbyname(socket.gethostname())
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        vpc_ticket_no = f"{ip_address}-{timestamp}"

        from odoo.addons.onepay_payment.controllers.main import OnePayController
        params = {
            "vpc_Version": "2",
            "vpc_Command": "pay",
            "vpc_AccessCode": self.provider_id.onepay_access_code,
            "vpc_Merchant": self.provider_id.onepay_merchant_id,
            "vpc_Amount": int_amount * 100,
            "vpc_Currency": "VND",
            "vpc_ReturnURL": urls.url_join(base_url, OnePayController._return_url),
            "vpc_OrderInfo": f"Order: {self.reference}",
            "vpc_MerchTxnRef": self.reference,
            "vpc_Locale": "en",
            "vpc_TicketNo": vpc_ticket_no,
            "AgainLink": urls.url_join(base_url, "/shop/payment"),
            "Title": "Trip Payment",
            "vpc_CallbackURL": urls.url_join(base_url, OnePayController._callback_url),
        }

        _logger.info(f"Callback URL: {params['vpc_CallbackURL']}")

        payment_link_data = self.provider_id._get_payment_url(
            params=params, secret_key=self.provider_id.onepay_secret_key
        )

        return {
            'api_url': payment_link_data
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "onepay" or len(tx) == 1:
            return tx

        reference = notification_data.get("vpc_MerchTxnRef")
        if not reference:
            raise ValidationError("OnePay: " + _("Received data with missing reference."))

        tx = self.search([("reference", "=", reference), ("provider_code", "=", "onepay")])
        if not tx:
            raise ValidationError("OnePay: " + _("No transaction found matching reference %s.", reference))
        return tx

    def _process_notification_data(self, notification_data):
        self.ensure_one()
        super()._process_notification_data(notification_data)
        if self.provider_code != "onepay":
            return

        if not notification_data:
            self._set_canceled(state_message=_("The customer left the payment page."))
            return

        amount = notification_data.get("vpc_Amount")
        assert amount, "OnePay: missing amount"
        assert self.currency_id.compare_amounts(float(amount) / 100, self.amount) == 0, "OnePay: mismatching amounts"

        vpc_txn_ref = notification_data.get("vpc_MerchTxnRef")
        if not vpc_txn_ref:
            raise ValidationError("OnePay: " + _("Received data with missing reference."))
        self.provider_reference = vpc_txn_ref

    def _cron_query_onepay_transaction_status(self):
        fifteen_minutes_ago = fields.Datetime.now() - timedelta(minutes=15)

        transactions = self.search([
            ('provider_code', '=', 'onepay'),
            ('state', '=', 'pending'),
            ('onepay_query_status', '=', False),
            ('onepay_query_start_time', '>=', fifteen_minutes_ago),
        ])

        for tx in transactions:
            tx._query_onepay_transaction_status()

    def _query_onepay_transaction_status(self):
        self.ensure_one()
        max_wait_time = timedelta(minutes=15)

        if fields.Datetime.now() > self.onepay_query_start_time + max_wait_time:
            self._set_error("OnePay: Transaction timed out")
            self.onepay_query_status = True
            return

        params = {
            'vpc_Command': 'queryDR',
            'vpc_Version': '2',
            'vpc_MerchTxnRef': self.reference,
            'vpc_Merchant': self.provider_id.onepay_merchant_id,
            'vpc_AccessCode': self.provider_id.onepay_access_code,
            "vpc_Password": "admin@123456",
            "vpc_User": "Administrator",
        }

        from payment.onepay_payment.models.payment_provider import PaymentProviderOnePay
        params_sorted = PaymentProviderOnePay.sort_param(params)
        string_to_hash = PaymentProviderOnePay.generate_string_to_hash(params_sorted)
        params['vpc_SecureHash'] = PaymentProviderOnePay.generate_secure_hash(string_to_hash, self.provider_id.onepay_secret_key)

        response = requests.post(
            "https://mtf.onepay.vn/msp/api/v1/vpc/invoices/queries",
            data=params,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if response.status_code == 200:
            response_data = response.json()
            response_code = response_data.get("vpc_TxnResponseCode")

            if response_code == "0":
                self._set_done()
                self.onepay_query_status = True
            else:
                error_message = self.provider_id._get_error_message(response_code)
                self._set_error(f"OnePay: {error_message}")
