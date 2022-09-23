# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

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
	"workflow_write:account"
]

# TODO: Register api_access_point and web_access_point returned during authorization flow

class AdobeSettings(Document):
	def on_update(self):
		connected_app = frappe.get_doc("Connected App", self.connected_application) if self.connected_application else frappe.new_doc("Connected App")


		parameters = {
			"provider_name": "Adobe Sign",
			"client_id": self.application_code,
			"client_secret": self.get_password("application_secret"),
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
			self.db_set("connected_application", connected_app.name)
		self.db_set("redirect_uri", connected_app.redirect_uri)