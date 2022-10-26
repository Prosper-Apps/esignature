# Copyright (c) 2022, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.workflow import apply_workflow, get_workflow_name
from frappe.utils import cint

from esignature.api.agreement import Agreement
from esignature.api.transientDocuments import transientDocuments

from frappe.workflow.doctype.workflow_action.workflow_action import (  # isort:skip
	get_allowed_roles,
	get_doc_workflow_state,
	get_next_possible_transitions,
)


# Keep for translations
# _('Signer'), _('Approver'), _('Acceptor'), _('Certified Recipient'), _('Form Filler')
# _('Delegate to Signer'), _('Delegate to Approver'), _('Delegate to Acceptor'), _('Delegate to Certified Recipient')
# _('Delegate to Form Filler'), _('Share'), _('Notary Signer'), _('Electronic Sealer')

ROLES = {
	"Signer": "SIGNER",
	"Approver": "APPROVER",
	"Acceptor": "ACCEPTOR",
	"Certified Recipient": "CERTIFIED_RECIPIENT",
	"Form Filler": "FORM_FILLER",
	"Delegate to Signer": "DELEGATE_TO_SIGNER",
	"Delegate to Approver": "DELEGATE_TO_APPROVER",
	"Delegate to Acceptor": "DELEGATE_TO_ACCEPTOR",
	"Delegate to Certified Recipient": "DELEGATE_TO_CERTIFIED_RECIPIENT",
	"Delegate to Form Filler": "DELEGATE_TO_FORM_FILLER",
	"Share": "SHARE",
	"Notary Signer": "NOTARY_SIGNER",
	"Electronic Sealer": "ELECTRONIC_SEALER",
}


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
		# TODO: Handle different status, signature types and security
		agreement_data = {
			"name": self.agreement_name,
			"senderEmail": self.user,
			"fileInfos": [],
			"participantSetsInfo": [],
			"state": self.status,
			"signatureType": "ESIGN",
		}

		for file in self.files:
			if file.transient_documents_id:
				agreement_data["fileInfos"].append(
					{"transientDocumentId": file.transient_documents_id}
				)

		if not agreement_data["fileInfos"]:
			return

		for user in self.users:
			agreement_data["participantSetsInfo"].append(
				{
					"memberInfos": [
						{"email": user.email, "securityOption": {"authenticationMethod": "NONE"}}
					],
					"role": ROLES.get(user.role),
					"order": cint(self.signing_order),
				}
			)

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
		if data.get("status") and data.get("status") != self.status:
			self.db_set("status", data.get("status"))

	@frappe.whitelist()
	def get_signed_document(self):
		if self.status != "SIGNED":
			return

		file_name = f"{frappe.scrub(self.agreement_name)}.pdf"
		if not frappe.db.exists(
			"File",
			dict(
				file_name=file_name, attached_to_doctype=self.doctype, attached_to_name=self.name
			),
		):
			client = Agreement(self.user)
			buffer = client.get_combined_documents(self.agreement_id)

			_file = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": file_name,
					"attached_to_doctype": self.doctype,
					"attached_to_name": self.name,
					"is_private": True,
					"content": buffer.getbuffer().tobytes(),
				}
			)
			_file.insert(ignore_permissions=True)

			return _file.name

		else:
			return frappe.db.get_value(
				"File",
				dict(
					file_name=file_name, attached_to_doctype=self.doctype, attached_to_name=self.name
				),
			)

	@frappe.whitelist()
	def get_signed_document_url(self):
		if self.status != "SIGNED":
			return

		client = Agreement(self.user)
		response = client.get_combined_documents_url(self.agreement_id)
		self.db_set("signed_agreement_url", response.get("url"))

		return response.get("url")

	def get_all_roles(self):
		return ROLES.keys()

	def get_signing_urls(self):
		doc_signing_urls = frappe.parse_json(self.signing_urls) or {}
		if doc_signing_urls:
			if not doc_signing_urls.get("code"):
				return doc_signing_urls

		client = Agreement(self.user)
		signing_urls = client.get_signing_urls(self.agreement_id)
		self.db_set("signing_urls", frappe.as_json(signing_urls))
		return signing_urls

	def check_user_status(self, user=None):
		if all(user.get("status") == "COMPLETED" for user in self.get("users")):
			return

		client = Agreement(self.user)
		members = client.get_members(self.agreement_id)

		for participantSets in members.get("participantSets"):
			for memberInfo in participantSets.get("memberInfos"):
				for user in self.get("users"):
					if user.email == memberInfo.get("email") and user.status != participantSets.get(
						"status"
					):
						user.status = participantSets.get("status")
						user.db_set("status", participantSets.get("status"))

		self.run_method("apply_workflow")
		self.run_method("before_validate")

	def apply_workflow(self):
		references = list(
			set((f.reference_doctype, f.reference_docname) for f in self.get("files"))
		)
		references_docs = [frappe.get_doc(f[0], f[1]) for f in references]

		def _apply_workflow(user):
			for ref_doc in references_docs:
				try:
					workflow = get_workflow_name(ref_doc.doctype)
					workflow_state = get_doc_workflow_state(ref_doc)
					for next_possible_transition in get_next_possible_transitions(
						workflow, workflow_state, ref_doc
					):
						if get_allowed_roles(
							user.email, workflow, next_possible_transition.get("next_state")
						):
							frappe.enqueue(
								apply_workflow_for_user,
								agreement=self,
								doc=ref_doc,
								action=next_possible_transition.get("action"),
								user=user.email,
								now=True,
							)

				except Exception:
					continue

		for user in self.get("users"):
			if cint(user.workflow_validation) and user.status in (
				"WAITING_FOR_OTHERS",
				"COMPLETED",
			):
				if frappe.db.exists("User", user.email):
					_apply_workflow(user)


def apply_workflow_for_user(agreement, doc, action, user):
	connected_user = frappe.session.user
	try:
		frappe.set_user(user)
		apply_workflow(doc, action)
		agreement.reload()
		agreement.run_method("apply_workflow")
		doc.run_method("notify_update")
	except Exception:
		pass
	finally:
		frappe.set_user(connected_user)


@frappe.whitelist()
def get_agreements_for_attachments(attachments):
	agreements = frappe.get_list(
		"Adobe Sign Agreement",
		filters=[
			["Adobe Sign Agreement Files", "file", "in", frappe.parse_json(attachments)]
		],
		fields=["name", "agreement_name", "signed_agreement_url", "status"],
		distinct=1,
	)

	filtered_agreements = []
	for agreement in agreements:
		doc = frappe.get_doc("Adobe Sign Agreement", agreement.name)
		agreement["signed_agreement"] = None
		agreement["signed_agreement_url"] = doc.get_signed_document_url()
		signed_agreement = doc.get_signed_document()
		doc.check_user_status()

		if signed_agreement:
			agreement["signed_agreement"] = frappe.db.get_value(
				"File", signed_agreement, "file_url"
			)
			filtered_agreements.append(agreement)
			continue

		if signing_urls := doc.get_signing_urls():
			for setinfos in signing_urls.get("signingUrlSetInfos", []):
				for urlset in setinfos.get("signingUrls", []):
					if (
						frappe.session.user == "Administrator"
						or urlset.get("email") == frappe.session.user
					):
						agreement_copy = agreement.copy()
						agreement_copy["signed_agreement_url"] = urlset.get("esignUrl")
						if frappe.session.user == "Administrator":
							agreement_copy[
								"agreement_name"
							] = f'{agreement["agreement_name"]} - {urlset.get("email")}'

						if agreement_copy["status"] != "SIGNED":
							for user in doc.get("users"):
								if urlset.get("email") == user.email and user.status == "WAITING_FOR_OTHERS":
									agreement_copy["status"] = "PENDING"

						filtered_agreements.append(agreement_copy)

			else:
				if signing_urls.get("code"):
					agreement["status"] = "ERROR"
					agreement["error"] = signing_urls.get("message")
					agreement["signed_agreement_url"] = frappe.utils.get_url_to_form(
						"Adobe Sign Agreement", agreement.name
					)
					filtered_agreements.append(agreement)

	return filtered_agreements
