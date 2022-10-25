# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from esignature.api.base import AdobeBase
from esignature.api.webhook import Webhook

_SCOPES = [
	"agreement_read:account",
	"agreement_write:account",
	"agreement_send:account",
	"webhook_read:account",
	"webhook_write:account"
]

AGREEMENT_ALL = [
	"AGREEMENT_ALL"
]
AGREEMENT_WEBHOOK_URL = "/api/method/esignature.api.webhook.adobe_webhooks"

class AdobeSettings(Document):
	def validate(self):
		if not self.enable_adobe_sign:
			return

		self.update_endpoints()
		self.update_connected_app()

	def update_connected_app(self):
		connected_app = frappe.get_doc("Connected App", self.connected_application) if self.connected_application else frappe.new_doc("Connected App")

		parameters = {
			"provider_name": "Adobe Sign",
			"client_id": self.application_code,
			"client_secret": self.get_password("application_secret", raise_exception=False),
			"scopes": [],
			"authorization_uri": f"{self.api_access_point}/public/oauth/v2",
			"token_uri": f"{self.api_access_point}/oauth/v2/token"
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
	def update_endpoints(self):
		connection = AdobeBase()
		connection.url = self.base_uri + "/api/rest/v6/baseUris"
		endpoints = connection.get_access_endpoints()

		if self.api_access_point != endpoints.get("apiAccessPoint"):
			self.api_access_point = endpoints.get("apiAccessPoint")
			self.db_set("api_access_point", endpoints.get("apiAccessPoint"))

		if self.web_access_point != endpoints.get("webAccessPoint"):
			self.web_access_point = endpoints.get("webAccessPoint")
			self.db_set("web_access_point", endpoints.get("webAccessPoint"))


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