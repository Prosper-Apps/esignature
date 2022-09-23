import json
import requests
from esignature.api.base import AdobeBase

class Widget(AdobeBase):
	def __init__(self):
		super(Widget, self).__init__()


		self.url = self.api_url + "/api/rest/v6/widgets"
		self.headers.update({
			'Content-Type': 'application/json'
		})

	def post(self, data):
		"""
		Example:
		data = {
			"name": "DokosTestWidget",
			"FileInfo": {
				"transientDocumentId": "3AAABLblqZhByIA4JUgog_tgZeI9NxAssNC4dR0ip3Zg0tDNM3Dy7AR_oCj3ANjh1PRehizzuxw83BSUspaCkCgzAznoa05mUkldC2N-WfnxFkm4PKadf6PQ0VO7bRirnMygeGdCS4Ign7kjD_u5eQD4Ee8fwZL9Ci10YGEP2y1i4IR00fckVAMS_nSy43EKOMSv1_ZYFFDPa9L4tW9y-_FHEmxU60GlEwAARsuUCvJ9cHfrH2XZcunZL_uT8LWE2XOOKvSkiwHaP0RyVtdHdM6oADkjamRgSalh1dTdgRX4rN4Apck2dJkqVP9JVyw8LZzUdJww0aHw*"
			},
			"widgetParticipantSetInfo": {},
			"state": "DRAFT"
		}
		"""

		response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

		return response.json()

	def get_widget(self, id):
		self.url = f"{self.url}/{id}"
		response = requests.get(self.url, headers=self.headers)

		return response.json()

	def get_agreements(self):
		pass