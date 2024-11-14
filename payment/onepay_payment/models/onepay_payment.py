from odoo import api, fields, models
import hashlib
import urllib.parse

from odoo.exceptions import ValidationError


class PaymentAcquirerOnepay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('onepay', 'OnePay')], ondelete={'onepay': 'set default'})
    onepay_merchant_id = fields.Char(string="Merchant ID", required_if_provider='onepay', help="Merchant ID provided by OnePay")
    onepay_access_code = fields.Char(string="Access Code", required_if_provider='onepay')
    onepay_secret = fields.Char(string="Secure Secret", required_if_provider='onepay')
    onepay_url = fields.Char(string="Payment URL", default="https://mtf.onepay.vn/onecomm-pay/vpc.op")

    def _get_onepay_url(self, values):
        """ Generate the OnePay payment URL """
        params = {
            'vpc_Merchant': self.onepay_merchant_id,
            'vpc_AccessCode': self.onepay_access_code,
            'vpc_Amount': str(int(values['amount'] * 100)),
            'vpc_MerchTxnRef': values['reference'],
            'vpc_OrderInfo': values['reference'],
            'vpc_ReturnURL': values['return_url'],
            'vpc_Version': '2',
            'vpc_Command': 'pay',
            'vpc_Locale': 'en',
            'vpc_Currency': 'VND'
        }

        # Tạo mã hash bảo mật
        secure_hash = self._generate_secure_hash(params)
        params['vpc_SecureHash'] = secure_hash

        # Tạo URL từ các tham số
        return f"{self.onepay_url}?{urllib.parse.urlencode(params)}"

    def _generate_secure_hash(self, params):
        """ Generate secure hash using the provided secret key """
        secret = self.onepay_secret
        sorted_params = sorted(params.items())
        hash_str = '&'.join(f"{k}={v}" for k, v in sorted_params)
        hash_str = f"{secret}&{hash_str}"
        return hashlib.sha256(hash_str.encode('utf-8')).hexdigest()

    def onepay_form_generate_values(self, values):
        """ Create values for payment """
        self.ensure_one()
        onepay_values = {
            'amount': values['amount'],
            'reference': values['reference'],
            'return_url': values['return_url']
        }
        payment_url = self._get_onepay_url(onepay_values)
        return {
            'onepay_url': payment_url
        }
    
    def onepay_get_form_action_url(self):
        return '/payment/onepay/redirect'

class PaymentTransactionOnepay(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _onepay_form_get_tx_from_data(self, data):
        """ Retrieve transaction based on OnePay response """
        reference = data.get('vpc_MerchTxnRef')
        if not reference:
            raise ValidationError("OnePay: No reference found in payment response")

        tx = self.search([('reference', '=', reference)])
        if not tx:
            raise ValidationError(f"OnePay: Transaction not found for reference {reference}")
        return tx

    def _onepay_form_validate(self, data):
        """ Validate payment transaction based on OnePay response """
        status = data.get('vpc_TxnResponseCode')
        if status == '0':
            self._set_transaction_done()
            return True
        else:
            self._set_transaction_cancel()
            return False
