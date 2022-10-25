import requests

import frappe
from frappe import _

class AdobeBase:
	def __init__(self, user=None):
		self.settings = frappe.get_single("Adobe Settings")
		self.api_url = self.settings.api_access_point or self.settings.base_uri

		self.user = user or frappe.session.user

		connected_app_name = self.settings.connected_application
		connected_app = frappe.get_doc("Connected App", connected_app_name)
		self.client_id = connected_app.client_id

		oauth_session = connected_app.get_oauth2_session(self.user)

		auto_refresh_kwargs = {"client_id": connected_app.client_id, "client_secret": connected_app.get_password("client_secret")}

		self.user_token = oauth_session.refresh_token(f"{self.api_url}/oauth/v2/refresh", **auto_refresh_kwargs)

		if not self.user_token.get("access_token"):
			frappe.throw(_("You are not authorized to make a request on behalf of this user"))

		self.headers = {
			'Authorization': f'Bearer {self.user_token.get("access_token")}'
		}

	def revoke_access_token(self):
		self.url = self.api_url + "/oauth/v2/revoke"
		response = requests.post(self.url, headers=self.headers, data={
			"token": self.user_token.get("access_token")
		})
		return response.status_code

	def get_access_endpoints(self):
		response = requests.get(self.url, headers=self.headers)
		return response.json()