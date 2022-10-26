frappe.listview_settings["Adobe Sign Webhook"] = {
	onload: function (listview) {
		listview.page.add_menu_item(__("Clear Error Logs"), function () {
			frappe.call({
				method: "frappe.core.doctype.error_log.error_log.clear_error_logs",
				callback: function () {
					listview.refresh();
				},
			});
		});

		frappe.require("logtypes.bundle.js", () => {
			frappe.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};