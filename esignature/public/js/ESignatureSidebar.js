class ESignatureMenu {
	constructor(opts) {
		$.extend(this, opts)
		this.made = false

		this.doctype_agreement = "Adobe Sign Agreement"
		this.doctype_users = "Adobe Sign Agreement Users"

		frappe.model.with_doctype(this.doctype_agreement)
		frappe.model.with_doctype(this.doctype_users)

		if (this.can_be_shown()) {
			this.make()
		}
	}

	can_be_shown() {
		return !this.frm.doc.__islocal
	}

	make() {
		if (this.made) { return }
		this.made = true

		// Initialize content with HTML template
		const html = frappe.render_template("esignature_menu", {})
		this.$menu = $(html)

		// Retrieve elements
		this.$btn_request_esignature = this.$menu.find(".esignature-menu--request-btn")
		this.$header = this.$menu.find(".esignature-menu--header")

		// Add event listeners to buttons
		this.$btn_request_esignature.click(() => this.open_request_modal())

		// Insert after the attachments sidebar menu.
		const $attachments = this.frm.attachments?.parent
		if ($attachments) {
			this.$menu.insertAfter($attachments)
		} else {
			this.sidebar.append(this.$menu)
		}

		// Finish initialization by adding buttons for signed files.
		this.refresh()
	}

	destroy() {
		if (!this.made) { return }
		this.$menu.remove()
		this.made = false
	}

	async refresh() {
		if (!this.made) { return }
		if (!this.can_be_shown()) {
			this.destroy()
		}
		// Update agreement URL
		// 1. Get URL
		const attachments = this.frm.attachments.get_attachments().map(a => a.name)
		const signed_agreements = await this.get_signed_agreement_url(attachments)

		// 2. Remove previous URL
		this.$menu.find(".esignature-menu--agreement-url").remove()

		// 3. Show the new URL
		signed_agreements.map((signed_agreement) => {
			const pill_icon = ["SIGNED", "PENDING"].includes(signed_agreement.status) ? "milestone" : "edit"
			const pill_color = this.get_pill_color(signed_agreement.status)

			const link_to_signed_agreement = signed_agreement.signed_agreement ?
				encodeURI(signed_agreement.signed_agreement).replace(/#/g, "%23") :
				signed_agreement.signed_agreement_url
			const icon = `<a href="${link_to_signed_agreement}" target="_blank">
				${frappe.utils.icon(pill_icon, "sm ml-0")}
			</a>`;

			$(`<li class="esignature-menu--agreement-url">`)
			.append(
				frappe.get_data_pill(
					`<a href=${signed_agreement.signed_agreement_url} target="_blank" title="${signed_agreement.agreement_name}">${signed_agreement.agreement_name}</a>`,
					null,
					null,
					icon
				)
			)
			.insertAfter(this.$header)
			.addClass(pill_color);
		})

		// 2. Remove previous buttons
		this.$menu.find(".esignature-menu--signed-item").remove()
	}

	get_pill_color(status) {
		switch(status) {
			case "PENDING":
				return "green-pill"
			case "ERROR":
				return "red-pill"
			case "SIGNED":
				return "blue-pill"
			default:
				return "yellow-pill"
		}
	}

	async get_signed_agreement_url(attachments) {
		return await frappe.xcall("esignature.esignature.doctype.adobe_sign_agreement.adobe_sign_agreement.get_agreements_for_attachments",
			{attachments: attachments}
		)
	}

	async open_request_modal() {
		const title = __("Request an eSignature")
		const fields = this.get_modal_fields()
		const primary_action = (values) => {
			this.create_an_agreement(values)
		}
		const primary_action_label = __("Request an eSignature")
		this.dialog = new frappe.ui.Dialog({
			title,
			fields,
			primary_action,
			primary_action_label,
		})
		await this.dialog.show()
		this.setup_attach_file_button()
	}

	get_modal_fields() {
		const me = this
		const attachments = this.frm.attachments.get_attachments()
		let modal_fields = ["email", "role"]
		if (frappe.workflow.get_state_fieldname(this.frm.doctype)) {
			modal_fields.push("workflow_validation")
		}

		return [
			{
				fieldname: "add-file-btn",
				fieldtype: "Button",
				label: __("Attach File"),
				click: () => me.ask_and_add_new_file(),
			},
			{
				label: __("Files"),
				fieldname: "files",
				fieldtype: "MultiCheck",
				reqd: 1,
				select_all: 1, // add buttons to (un)check all
				options: attachments.map(a => ({
					label: a.file_name,
					value: a.name,
					checked: true, // checked by default
				})),
			},
			{ fieldtype: "Section Break" },
			{
				label: __("Signing order must be respected"),
				fieldname: "signing_order",
				fieldtype: "Check",
				default: 1,
			},
			{
				label: __("Signers"),
				fieldname: "users",
				fieldtype: "Table",
				reqd: 1,
				options: this.doctype_users,
				fields: frappe.meta.get_docfields(this.doctype_users)
					.filter(df => modal_fields.includes(df.fieldname))
					.map(df => {
						if (df.fieldname === "email") {
							return {
								...df,
								fieldtype: "Autocomplete",
								get_query: "frappe.email.get_contact_list",
							}
						} else {
							return df
						}
					}),
			},
			{ fieldtype: "Section Break" },
			{
				label: __("Agreement Name"),
				fieldname: "agreement_name",
				fieldtype: "Data",
				reqd: 1,
			},
		]
	}

	setup_attach_file_button() {
		const control = this.dialog.get_field("files")
		const oldButton = this.dialog.get_field("add-file-btn")
		if (oldButton && control.df.select_all && control.$select_buttons) {
			oldButton.hide()
			this.$add_file_button = $(`
				<button class="btn btn-xs btn-default add-file-btn">
					${frappe.utils.icon("add", "xs")}
					${oldButton.df.label}
				</button>
			`).click(oldButton.df.click).prependTo(control.$select_buttons)
		}
	}

	create_an_agreement(values) {
		this.dialog.disable_primary_action()
		return frappe.call({
			method: "frappe.client.insert",
			args: {
				doc: {
					user: frappe.session.user,
					doctype: this.doctype_agreement,
					agreement_name: values.agreement_name,
					files: values.files.map(f => {
						return {
							file: f
						}
					}),
					users: values.users,
					signing_order: values.signing_order
				}
			},
		}).then(() => {
			this.dialog.enable_primary_action()
			this.dialog.hide()
			frappe.show_alert({
				message: __("eSignature Request sent. Please check your email Inbox."),
				indicator: "green"
			})
			this.frm.sidebar.reload_docinfo();
		}).catch(() => {
			this.dialog.enable_primary_action()
		})
	}

	ask_for_new_file() {
		return new Promise((callback, emitError) => {
			// frappe/frappe/public/js/frappe/file_uploader/index.js
			new frappe.ui.FileUploader({
				doctype: this.frm.doctype,
				docname: this.frm.docname,
				frm: this.frm,
				folder: frappe.boot.attachments_folder,
				make_attachments_public: false,
				allow_multiple: false,
				on_success: (file_doc) => {
					// NOTE: callback is called for each file
					callback(file_doc)
				}
			})
		})
	}

	async ask_and_add_new_file() {
		const file_doc = await this.ask_for_new_file()
		this.add_file_option({
			value: file_doc.name,
			label: file_doc.file_name,
			checked: true,
		})
	}

	add_file_option(option) {
		const control = this.dialog.get_field("files")
		control.df.options.push(option)
		control.refresh()
	}
}

const extendFormSidebarWithESignature = (baseClass) => class ESignatureSidebar extends baseClass {
	make_attachments() {
		super.make_attachments()

		this.frm.esignature_menu = new ESignatureMenu({
			frm: this.frm,
			sidebar: this.sidebar,
		})
	}

	reload_docinfo(callback) {
		const cb = (...args) => {
			callback && callback(...args)
			this.frm.esignature_menu && this.frm.esignature_menu.refresh()
		}
		return super.reload_docinfo(cb)
	}

	refresh() {
		super.refresh()
		this.frm.esignature_menu && this.frm.esignature_menu.refresh()
	}
}

$(document).ready(() => {
	if (cint(frappe.boot.adobe_sign_enabled)) {
		frappe.ui.form.Sidebar = extendFormSidebarWithESignature(frappe.ui.form.Sidebar)

		frappe.realtime.on("agreement_update", () => {
			cur_frm && cur_frm.sidebar && cur_frm.sidebar.refresh()
		})

		frappe.realtime.on("workflow_update_after_signature", () => {
			cur_frm && cur_frm.refresh()
		})
	}
})
