import frappe
import requests
from werkzeug.wrappers import Response

from esignature.api.base import AdobeBase


class Webhook(AdobeBase):
	def __init__(self, user=None):
		super(Webhook, self).__init__(user)

		self.url = self.api_url + "/api/rest/v6/webhooks"
		self.headers.update({"Content-Type": "application/json"})

	def create(self, webhook_info):
		response = requests.post(
			self.url, headers=self.headers, data=frappe.as_json(webhook_info)
		)
		return response.json()


@frappe.whitelist(allow_guest=True)
def adobe_webhooks():
	validation_header = frappe.get_request_header("X-AdobeSign-ClientId") or ""
	if validation_header and validation_header == frappe.db.get_single_value(
		"Adobe Settings", "application_code"
	):
		response = Response()
		response.headers.add("X-AdobeSign-ClientId", validation_header)
		response.http_status_code = 200

		if frappe.form_dict and frappe.form_dict.get("webhookNotificationId"):
			frappe.get_doc(
				{
					"doctype": "Adobe Sign Webhook",
					"webhook_id": frappe.form_dict.get("webhookNotificationId"),
					"data": frappe.form_dict,
				}
			).insert(ignore_permissions=True, ignore_if_duplicate=True)

		return response
