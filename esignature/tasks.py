import frappe


def daily_long():
	for agreement in frappe.get_all(
		"Adobe Sign Agreement", filters={"status": ("not in", ["SIGNED", "CANCELLED"])}
	):
		doc = frappe.get_doc("Adobe Sign Agreement", agreement.name)
		doc.run_method("update_status")
		doc.run_method("check_user_status")
