import frappe

def daily_long():
	for agreement in frappe.get_all("Adobe Sign Agreement", filters={"status": ("!=", "SIGNED")}):
		frappe.get_doc("Adobe Sign Agreement", agreement.name).run_method("update_status")