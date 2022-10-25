import frappe


def get_bootinfo(bootinfo):
	bootinfo.adobe_sign_enabled = frappe.db.get_single_value(
		"Adobe Settings", "enable_adobe_sign"
	)
