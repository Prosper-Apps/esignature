# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from esignature.api.transientDocuments import transientDocuments
from esignature.api.agreement import Agreement

class AdobeSignAgreement(Document):
	def after_insert(self):
		self.get_transient_documents()
		self.create_agreement()

	def get_transient_documents(self):
		# TODO: add exception handler, especially for external links
		client = transientDocuments(self.user)

		transient_files = []
		for file in self.files:
			content = frappe.get_doc("File", file.file).get_content()
			if content:
				transient_files.append(
					("File", content)
				)
		response = client.post(transient_files)

		if response.get("transientDocumentId"):
			self.db_set("transient_documents_id", response.get("transientDocumentId"))

	def create_agreement(self):
		agreement_data = {
			"name": self.agreement_name,
			"senderEmail": self.user,
			"fileInfos": [{
				"transientDocumentId": self.transient_documents_id
			}],
			"participantSetsInfo": [],
			"state": "AUTHORING",
			"signatureType": "ESIGN"
		}

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

		client = Agreement(self.user)
		response = client.post(agreement_data)

		if response.get("id"):
			self.db_set("agreement_id", response.get("id"))

	def get_agreement(self):
		client = Agreement(self.user)
		response = client.get(self.agreement_id)

		print("get_agreement", response)