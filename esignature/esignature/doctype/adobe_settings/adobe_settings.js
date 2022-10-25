// Copyright (c) 2022, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Adobe Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__("Create webhooks"), () => {
			frm.call({
				method: "create_webhooks",
				doc: frm.doc
			}).then((r) => {
				if (r.message.id) {
					frappe.show_alert({
						indicator: "green",
						message: __("Webhook created successfully")
					})
				} else {
					frappe.show_alert({
						indicator: "orange",
						message: __("An error prevented creating the webhooks correctly")
					})
				}
			})
		}, __("Actions"))

		frm.add_custom_button(__("Update endpoints"), () => {
			frm.call({
				method: "update_endpoints",
				doc: frm.doc
			}).then((r) => {
				console.log(r)
			})
		}, __("Actions"))

		if (frm.doc.enable_adobe_sign && frm.doc.connected_application) {
			frm.add_custom_button(__("Connect to Adobe"), () => {
				frappe.model.with_doc("Connected App", frm.doc.connected_application, () => {
					const doc = frappe.get_doc("Connected App", frm.doc.connected_application)
					console.log(doc)
					frappe.call({
						method: "initiate_web_application_flow",
						doc: doc
					}).then((r) => {
						window.open(r.message, "_blank");
					})
				})
			}, __("Token management"))

			frm.add_custom_button(__("Revoke access token"), () => {
				frm.call({
					method: "revoke_token",
					doc: frm.doc
				}).then((r) => {
					frappe.show_alert({
						indicator: "green",
						message: __("Token revoked")
					})
				})
			}, __("Token management"))
		}
	}
});
