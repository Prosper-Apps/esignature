import frappe


def after_install():
	log_settings = frappe.get_doc("Log Settings")
	log_settings.register_doctype("Adobe Sign Webhook", 60)
	log_settings.save()
