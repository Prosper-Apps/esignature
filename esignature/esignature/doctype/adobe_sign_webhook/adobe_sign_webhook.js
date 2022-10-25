// Copyright (c) 2022, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Adobe Sign Webhook', {
	refresh: function(frm) {
		if (frm.doc.status != "Completed") {
			frm.add_custom_button(__("Retry Webhook"), () => {
				frappe.call({
					method: "retry_webhook",
					doc: frm.doc
				}).then(() => {
					frm.refresh()
				})
			}, __("Actions"))
		}
	}
});
