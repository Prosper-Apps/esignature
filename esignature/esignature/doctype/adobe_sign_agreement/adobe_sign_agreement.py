# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from esignature.api.transientDocuments import transientDocuments
from esignature.api.agreement import Agreement

class AdobeSignAgreement(Document):
	def after_insert(self):
		transient_document = self.get_transient_documents()
		if transient_document:
			self.status = "IN_PROCESS"
			self.db_set("status", "IN_PROCESS")
		self.create_agreement()

	def get_transient_documents(self):
		# TODO: add exception handler, especially for external links
		client = transientDocuments(self.user)

		transient_documents_created = []
		for file in self.files:
			file_doc = frappe.get_doc("File", file.file)
			response = client.post(file_doc)
			if response.get("transientDocumentId"):
				file.db_set("transient_documents_id", response.get("transientDocumentId"))

			transient_documents_created.append(response.get("transientDocumentId"))

		return all(transient_documents_created)

	def create_agreement(self):
		agreement_data = {
			"name": self.agreement_name,
			"senderEmail": self.user,
			"fileInfos": [],
			"participantSetsInfo": [],
			"state": self.status,
			"signatureType": "ESIGN"
		}

		for file in self.files:
			if file.transient_documents_id:
				agreement_data["fileInfos"].append({
					"transientDocumentId": file.transient_documents_id
				})

		if not agreement_data["fileInfos"]:
			return

		for user in self.users:
			agreement_data["participantSetsInfo"].append({
				"memberInfos": [{
					"email": user.email,
					"securityOption": {
						"authenticationMethod": "NONE"
					}
				}],
				"role": user.role,
				"order": 1
			})

		if not agreement_data["participantSetsInfo"]:
			return

		client = Agreement(self.user)
		response = client.post(agreement_data)

		if response.get("id"):
			self.db_set("agreement_id", response.get("id"))

	def get_agreement(self):
		client = Agreement(self.user)
		response = client.get(self.agreement_id)
		return response

	@frappe.whitelist()
	def update_status(self):
		data = self.get_agreement()
		if data.get("status"):
			self.db_set("status", data.get("status"))

	@frappe.whitelist()
	def get_signed_document(self):
		client = Agreement(self.user)
		response = client.get_combined_documents_url(self.agreement_id)
		self.db_set("signed_agreement_url", response.get("url"))