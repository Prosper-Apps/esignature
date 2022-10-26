# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class AdobeSignWebhook(Document):
	@staticmethod
	def clear_old_logs(days=60):
		table = frappe.qb.DocType("Adobe Sign Webhook")
		frappe.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))

	def after_insert(self):
		self.handle_event()

	def handle_event(self):
		try:
			data = frappe.parse_json(self.data)

			if data.get("eventResourceType") == "agreement":
				AgreementWebhookHandler(data)

			self.db_set("status", "Completed")
		except Exception:
			self.db_set("error", frappe.get_traceback())
			self.db_set("status", "Failed")

	@frappe.whitelist()
	def retry_webhook(self):
		self.db_set("error", None)
		self.db_set("status", "Pending")
		return self.handle_event()


class AgreementWebhookHandler:
	def __init__(self, data):
		self.data = data
		if agreement_id := data.get("agreement", {}).get("id"):
			if frappe.db.exists("Adobe Sign Agreement", dict(agreement_id=agreement_id)):
				self.agreement = frappe.get_doc(
					"Adobe Sign Agreement", dict(agreement_id=agreement_id)
				)
				self.update_status()
				self.handle_event()

	def update_status(self):
		if self.data.get("agreement", {}).get(
			"status"
		) and self.agreement.status != self.data.get("agreement", {}).get("status"):
			self.agreement.run_method("update_status")

	def handle_event(self):
		if self.data.get("event") == "AGREEMENT_ACTION_COMPLETED":
			self.handle_agreement_action_completed()

		for file in self.agreement.get("files"):
			if file.reference_doctype and file.reference_docname:
				frappe.publish_realtime(
					"agreement_update",
					doctype=file.reference_doctype,
					docname=file.reference_docname,
					after_commit=True,
				)

	def handle_agreement_action_completed(self):
		self.agreement.run_method("check_user_status")
