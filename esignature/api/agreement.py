import json
import requests

import frappe
from frappe import _

from esignature.api.base import AdobeBase

class Agreement(AdobeBase):
	def __init__(self, user=None):
		super(Agreement, self).__init__(user)

		self.url = self.api_url + "/api/rest/v6/agreements"
		self.headers.update({
			'Content-Type': 'application/json'
		})

	def get(self, id=None):
		url = f"{self.url}/{id}" if id else self.url
		response = requests.get(url, headers=self.headers)

		if response.status_code in [200, 201]:
			return response.json()
		else:
			frappe.throw(title=response.json().get("code"), msg=response.json().get("message"))

	def post(self, data):
		"""
		example:
		{
			"id": "<an-adobe-sign-generated-id>",
			"name": "MyTestAgreement",
			"participantSetsInfo": [{
				"memberInfos": [{
				"email": "signer@somecompany.com",
				"securityOption": {
					"authenticationMethod": "NONE"
				}
				}],
				"role": "SIGNER",
				"order": 1
			}],
			"senderEmail": "sender@somecompany.com",
			"createdDate": "2018-07-23T08:13:16Z",
			"signatureType": "ESIGN",
			"locale": "en_US",
			"status": "OUT_FOR_SIGNATURE",
			"documentVisibilityEnabled": false
		}
		"""

		if self.settings.x_api_user:
			self.headers.update({
				'x-api-user': f'email: {self.user or frappe.session.user}'
			})

		response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

		if response.status_code in [200, 201]:
			return response.json()
		else:
			frappe.throw(title=_("Agreement creation issue"), msg=response.text)

	def get_combined_documents(self, id) -> bytes:
		import shutil
		import io
		url = f"{self.url}/{id}/combinedDocument"
		with requests.get(url, headers=self.headers, stream=True) as r:
			buffer = io.BytesIO()
			shutil.copyfileobj(r.raw, buffer)

		buffer.seek(0)
		return buffer

	def get_combined_documents_url(self, id):
		url = f"{self.url}/{id}/combinedDocument/url"
		response = requests.get(url, headers=self.headers)
		return response.json()

	def get_signing_urls(self, id):
		url = f"{self.url}/{id}/signingUrls"
		response = requests.get(url, headers=self.headers)
		return response.json()

	def get_events(self, id):
		url = f"{self.url}/{id}/events"
		response = requests.get(url, headers=self.headers)
		return response.json()