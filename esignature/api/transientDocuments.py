import requests
from mimetypes import guess_type

import frappe
from frappe import _

from esignature.api.base import AdobeBase

class transientDocuments(AdobeBase):
	def post(self, file):
		"""
		files: a File document
		"""

		file_type = guess_type(file.file_name)
		if not file_type[0]:
			frappe.throw(_("Invalid file"))

		files = {
			"File": (file.file_name, open(file.get_full_path(),'rb'), file_type[0])
		}

		self.headers.update({
			'Content-Disposition': f'form-data; name=";File"; filename={file.file_name}'
		})

		url = self.api_url + "api/rest/v6/transientDocuments"
		response = requests.post(
			url,
			headers=self.headers,
			files=files
		)

		return response.json()