# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AdobeSignWebhook(Document):
	def after_insert(self):
		self.handle_event()

	def handle_event(self):
		data = frappe.parse_json(self.data)

		if data.get("eventResourceType") == "agreement":
			if agreement_id := data.get("agreement", {}).get("id"):
				if frappe.db.exists("Adobe Sign Agreement", dict(agreement_id=agreement_id)):
					agreement = frappe.get_doc("Adobe Sign Agreement", dict(agreement_id=agreement_id))
					if data.get("agreement", {}).get("status") and agreement.status != data.get("agreement", {}).get("status"):
						frappe.db.set_value("Adobe Sign Agreement", agreement.name, "status", data.get("agreement", {}).get("status"))