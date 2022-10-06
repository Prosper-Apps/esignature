# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from esignature.api.base import AdobeBase
from esignature.api.webhook import Webhook

_SCOPES = [
	"user_read:account",
	"user_write:account",
	"user_login:account",
	"agreement_read:account",
	"agreement_write:account",
	"agreement_send:account",
	"widget_read:account",
	"widget_write:account",
	"library_read:account",
	"library_write:account",
	"workflow_read:account",
	"workflow_write:account",
	"webhook_read:account",
	"webhook_write:account"
]

# TODO: Register api_access_point and web_access_point returned during authorization flow

AGREEMENT_ALL = [
	"AGREEMENT_ALL"
]
AGREEMENT_WEBHOOK_URL = "/api/method/esignature.api.webhook.adobe_webhooks"

class AdobeSettings(Document):
	def validate(self):
		connected_app = frappe.get_doc("Connected App", self.connected_application) if self.connected_application else frappe.new_doc("Connected App")


		parameters = {
			"provider_name": "Adobe Sign",
			"client_id": self.application_code,
			"client_secret": self.get_password("application_secret", raise_exception=False),
			"scopes": [],
			"authorization_uri": f"{self.base_uri}/public/oauth/v2",
			"token_uri": f"{self.base_uri}/oauth/v2/token"
		}

		connected_app.update(parameters)

		for scope in _SCOPES:
			connected_app.append("scopes", {
				"scope": scope
			})

		connected_app.save()

		if not self.connected_application:
			self.connected_application = connected_app.name

		self.redirect_uri = connected_app.redirect_uri


	@frappe.whitelist()
	def create_webhooks(self):
		# "problemNotificationEmails": frappe.session.user if frappe.session.user != "Administrator" else "",
		data = {
			"name": "dokos_esignature_all_agreement_webhook",
			"scope": "ACCOUNT",
			"state": "ACTIVE",
			"webhookSubscriptionEvents": AGREEMENT_ALL,
			"webhookUrlInfo": {
				"url": frappe.utils.get_url(AGREEMENT_WEBHOOK_URL)
			},
			"applicationDisplayName": frappe.get_website_settings("app_name") or "Dokos eSignature",
			"applicationName": "dokos_esignature",
		}

		adobe_webhook = Webhook()
		return adobe_webhook.create(data)

	@frappe.whitelist()
	def revoke_token(self):
		connection = AdobeBase()
		return connection.revoke_access_token()