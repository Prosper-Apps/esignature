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
		const signed_agreement_url = await this.get_signed_agreement_url()

		// 2. Remove previous URL
		this.$menu.find(".esignature-menu--agreement-url").remove()

		// 3. Show the new URL
		this.$agreement_url = $("<a>")
			.attr("href", signed_agreement_url)
			.css("word-break", "break-all")
			.text(signed_agreement_url)
			.wrap("<li></li>").parent()
			.addClass("esignature-menu--agreement-url")
			.addClass("pb-4")
			.insertAfter(this.$header)


		// Update signed items
		// 1. Get all signed items
		const item_names = this.frm.attachments.get_attachments().map(a => a.name)
		const signed_items = await this.list_signed_items_for(item_names)

		// 2. Remove previous buttons
		this.$menu.find(".esignature-menu--signed-item").remove()

		// 3. List all signed files as buttons
		signed_items.forEach(f => {
			const label = f.file_name
			const $btn = frappe.get_data_pill(label, null, null, null)
				.wrap("<li></li>").parent()
				.addClass("esignature-menu--signed-item")
				.insertAfter(this.$header)
		})
	}

	async get_signed_agreement_url() {
		// const args = {
		// 	doctype: this.frm.doctype,
		// 	docname: this.frm.docname,
		// }
		// const agreement = await frappe.xcall("esignature.esignature.api.get_agreement_for_doc", args)
		// return agreement.signed_agreement_url
		return "https://example.com/lorem-ipsum-dolor-sit-amet-consectetur-adipiscing-elit"
	}

	async list_signed_items_for(file_names) {
		return []

		// const args = {
		// 	docname: this.frm.docname,
		// 	attachments: file_names,
		// }
		// console.log("finding signed files for:", { args })
		// const res = await frappe.xcall("esignature.esignature.api.list_signed_items", args)

		// TODO: remove mockup code
		// return this.frm.attachments.get_attachments().flatMap(a => ([
		// 	{
		// 		file_name: "signed_" + a.file_name,
		// 		file_url: a.file_url,
		// 		name: "12345678",
		// 	}, {
		// 		file_name: "hash_" + a.file_name,
		// 		file_url: a.file_url,
		// 		name: "12345678",
		// 	}
		// ]))
	}

	async open_request_modal() {
		const attachments = this.frm.attachments.get_attachments()
		const title = __("Request eSignature")
		const fields = this.get_modal_fields()
		const primary_action = (values) => {
			this.create_an_agreement(values)
		}
		const primary_action_label = __("Request eSignature")
		this.dialog = new frappe.ui.Dialog({
			title,
			fields,
			primary_action,
			primary_action_label,
			// TODO: frappe.confirm before closing modal (not possible with dialog.onhide?)
		})
		await this.dialog.show()
		this.setup_attach_file_button()
	}

	get_modal_fields() {
		const me = this
		const attachments = this.frm.attachments.get_attachments()

		return [
			{
				label: __("Agreement Name"),
				fieldname: "agreement_name",
				fieldtype: "Data",
				reqd: 1,
			},
			{ fieldtype: "Section Break" },
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
				label: __("Signers"),
				fieldname: "users",
				fieldtype: "Table",
				reqd: 1,
				options: this.doctype_users,
				fields: frappe.meta.get_docfields(this.doctype_users)
					.filter(df => df.fieldname === "email" || df.fieldname === "role")
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
		console.log(values)
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
					users: values.users
				}
			},
		}).then(() => {
			this.dialog.hide()
			frappe.show_alert({
				message: __("eSignature Request sent. Please check your email Inbox."),
				indicator: "green"
			})
		})
	}

	ask_for_new_file() {
		return new Promise((callback, emitError) => {
			// frappe/frappe/public/js/frappe/file_uploader/index.js
			const file_uploader = new frappe.ui.FileUploader({
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
			callback(...args)
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
	}
})
