import frappe
from frappe import _

class AdobeBase:
	def __init__(self, user=None):
		self.api_url = "https://api.eu1.adobesign.com/"

		connected_app_name = frappe.db.get_single_value("Adobe Settings", "connected_application")
		connected_app = frappe.get_doc("Connected App", connected_app_name)
		user_token_cache = connected_app.get_token_cache(user or frappe.session.user)

		if not user_token_cache:
			frappe.throw(_("You are not authorized to make a request on behalf of this user"))

		self.headers = {
			'Authorization': f'Bearer {user_token_cache.get_password("access_token")}'
		}