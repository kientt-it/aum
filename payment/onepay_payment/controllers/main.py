from werkzeug.exceptions import Forbidden

from odoo import _, http
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.onepay_payment.models.payment_provider import PaymentProviderOnePay
import logging
import pprint
import hmac

_logger = logging.getLogger(__name__)


class OnePayController(http.Controller):
    _return_url = "/payment/onepay/return"
    _ipn_url = "/payment/onepay/webhook"
    _callback_url = "/payment/onepay/callback"

    @http.route(['/payment/onepay/return'], type='http', auth='public', csrf=False)
    def onepay_return(self, **post):
        """
        Xử lý khi người dùng được chuyển hướng lại từ OnePay.
        """
        txn_response_code = post.get('vpc_TxnResponseCode')
        message = post.get('vpc_Message', 'Unknown error')

        # Ghi log thông tin phản hồi từ OnePay
        _logger.info("Received response from OnePay: %s", post)

        # Kiểm tra mã phản hồi trạng thái giao dịch
        if txn_response_code == "0":
            # Nếu giao dịch thành công
            _logger.info("Transaction successful.")
            return request.redirect('/payment/success')
        else:
            # Nếu giao dịch thất bại
            error_message = f"Giao dịch thất bại: {message}"
            _logger.warning("Transaction failed with message: %s", error_message)
            return request.redirect('/payment/error')
            # return request.render('onepay_payment.payment_error_template', {
            #     'error_message': error_message
            # })

    @http.route(_callback_url, type="http", methods=["POST"], auth="public", csrf=False, save_session=False)
    def onepay_callback(self, **data):
        _logger.info("Callback received from OnePay with data:\n%s", pprint.pformat(data))

        try:
            tx_sudo = request.env["payment.transaction"].sudo()._get_tx_from_notification_data("onepay", data)
            self._verify_notification_signature(data, tx_sudo)
            tx_sudo._handle_notification_data("onepay", data)
        except Forbidden:
            _logger.warning("Forbidden error during signature verification", exc_info=True)
            return request.make_json_response({"RspCode": "97", "Message": "Invalid Checksum"})
        except ValidationError:
            _logger.warning("Validation error during callback data processing", exc_info=True)
            return request.make_json_response({"RspCode": "01", "Message": "Order Not Found"})

        if tx_sudo.state in ["done", "cancel", "error"]:
            return request.make_json_response({"RspCode": "02", "Message": "Order already confirmed"})

        response_code = data.get("vpc_TxnResponseCode")
        _logger.info("Transaction response code: %s", response_code)

        if response_code == "0":
            tx_sudo._set_done()
        else:
            error_message = self._get_error_message(response_code)
            tx_sudo._set_error(f"OnePay: {error_message}")

        return request.make_json_response({"RspCode": "00", "Message": "Callback Success"})

    @staticmethod
    def _verify_notification_signature(data, tx_sudo):
        received_signature = data.pop("vpc_SecureHash", None)
        if not received_signature:
            _logger.warning("Received notification with missing signature.")
            raise Forbidden()

        merchant_hash_code = tx_sudo.provider_id.onepay_secret_key
        sorted_data = PaymentProviderOnePay.sort_param(data)
        signing_string = PaymentProviderOnePay.generate_string_to_hash(sorted_data)
        expected_signature = PaymentProviderOnePay.generate_secure_hash(signing_string, merchant_hash_code)

        _logger.info("Received signature: %s", received_signature)
        _logger.info("Expected signature: %s", expected_signature)

        if not hmac.compare_digest(received_signature.upper(), expected_signature):
            _logger.warning("Received notification with invalid signature.")
            raise Forbidden()

    @staticmethod
    def _get_error_message(response_code):
        error_messages = {
            "1": _("Unspecified failure in authorization."),
            "2": _("Card Issuer declined to authorize the transaction."),
            # Add other error codes and their corresponding messages as needed
        }
        return error_messages.get(response_code, _("Unspecified failure."))

    @http.route(_ipn_url, type="http", auth="public", methods=["POST"], csrf=False, save_session=False)
    def onepay_webhook(self, **data):
        _logger.info("Notification received from OnePay with data:\n%s", pprint.pformat(data))

        try:
            tx_sudo = request.env["payment.transaction"].sudo()._get_tx_from_notification_data("onepay", data)
            self._verify_notification_signature(data, tx_sudo)
            tx_sudo._handle_notification_data("onepay", data)
        except Forbidden:
            _logger.warning("Forbidden error during signature verification", exc_info=True)
            tx_sudo._set_error("OnePay: " + _("Received data with invalid signature."))
            return request.make_json_response({"RspCode": "97", "Message": "Invalid Checksum"})
        except AssertionError:
            _logger.warning("Assertion error during notification handling", exc_info=True)
            tx_sudo._set_error("OnePay: " + _("Received data with invalid amount."))
            return request.make_json_response({"RspCode": "04", "Message": "Invalid amount"})
        except ValidationError:
            _logger.warning("Unable to handle the notification data", exc_info=True)
            return request.make_json_response({"RspCode": "01", "Message": "Order Not Found"})

        if tx_sudo.state in ["done", "cancel", "error"]:
            return request.make_json_response({"RspCode": "02", "Message": "Order already confirmed"})

        response_code = data.get("vpc_TxnResponseCode")
        _logger.info("Transaction response code: %s", response_code)

        if response_code == "0":
            tx_sudo._set_done()
        else:
            error_message = self._get_error_message(response_code)
            tx_sudo._set_error(f"OnePay: {error_message}")

        return request.make_json_response({"RspCode": "00", "Message": "Callback Success"})
