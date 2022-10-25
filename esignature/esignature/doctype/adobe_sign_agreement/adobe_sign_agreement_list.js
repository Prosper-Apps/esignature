frappe.listview_settings["Adobe Sign Agreement"] = {
	get_indicator: function (doc) {
		if (doc.status == "SIGNED") {
			return [__("Signed"), "green", "status,=,Signed"];
		} else {
			return [__("Pending"), "orange", `status,=,${doc.status}`];
		}
	},
};
