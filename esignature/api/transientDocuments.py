import requests

from esignature.api.base import AdobeBase

class transientDocuments(AdobeBase):
	def __init__(self):
		super(transientDocuments, self).__init__()

		self.headers.update({
			'Content-Disposition': 'form-data; name=";File"; filename=testfile.pdf',
		})

	def post(self, files):
		"""
		files: [("File", frappe.get_doc("File", filename).get_content())]
		"""
		url = self.api_url + "/api/rest/v6/transientDocuments"
		response = requests.post(url, headers=self.headers, files=files)

		return response.json()