// Copyright (c) 2022, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Adobe Sign Agreement', {
	refresh: function(frm) {
		if (frm.doc.agreement_id) {
			frm.add_custom_button(__("Update Status"), () => {
				frappe.show_alert({
					indicator: "orange",
					message: __("Status update in progress")
				})
				frappe.call({
					method: "update_status",
					doc: frm.doc
				}).then(() => {
					frm.refresh_fields("status")
					frappe.show_alert({
						indicator: "green",
						message: __("Status updated")
					})
				})
			}, __("Actions"))
		}

		if (frm.doc.status == "SIGNED") {
			frm.add_custom_button(__("Download the agreement"), () => {
				frappe.show_alert({
					indicator: "orange",
					message: __("Download started")
				})
				frappe.call({
					method: "get_signed_document",
					doc: frm.doc
				}).then(() => {
					frappe.show_alert({
						indicator: "green",
						message: __("Download completed")
					})
					frm.refresh()
				})
			}, __("Actions"))

			frm.add_custom_button(__("Get the signed agreement URL"), () => {
				frappe.call({
					method: "get_signed_document_url",
					doc: frm.doc
				}).then(() => {
					frappe.show_alert({
						indicator: "green",
						message: __("URL Updated")
					})
					frm.refresh()
				})
			}, __("Actions"))
		}
	}
});
