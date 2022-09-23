import json
import requests

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

		return response.json()

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
		response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

		return response.json()