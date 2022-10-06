class ESignatureMenu {
	constructor(opts) {
		$.extend(this, opts)
		this.made = false

		// TODO: remove superfluous calls to frappe.model.with_doctype
		frappe.model.with_doctype("File")
		frappe.model.with_doctype("User")
		frappe.model.with_doctype("Adobe Sign Agreement Users")

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

		const item_names = this.frm.attachments.get_attachments().map(a => a.name)
		const signed_items = await this.list_signed_items_for(item_names)

		// Remove previous buttons
		this.$menu.find(".esignature-menu--signed-item").remove()

		// List all signed files as buttons
		signed_items.forEach(f => {
			const label = f.file_name
			const $btn = frappe.get_data_pill(label, null, null, null)
				.wrap("<li></li>").parent()
				.addClass("esignature-menu--signed-item")
				.insertBefore(this.$btn_request_esignature.parent())
		})
	}

	async list_signed_items_for(file_names) {
		// file_names: list of names (string) of File documents
		const args = {
			docname: this.frm.docname,
			attachments: file_names,
		}
		console.log("finding signed files for:", { args })
		// const res = await frappe.xcall('esignature.esignature.api.list_signed_items', args)

		// TODO: remove mockup code
		const res = this.frm.attachments.get_attachments().flatMap(a => ([
			{
				file_name: "signed_" + a.file_name,
				file_url: a.file_url,
				name: "12345678",
			}, {
				file_name: "hash_" + a.file_name,
				file_url: a.file_url,
				name: "12345678",
			}
		]))

		return res
	}

	open_request_modal() {
		const attachments = this.frm.attachments.get_attachments()
		const title = __("Request eSignature")
		const fields = this.get_modal_fields()
		const primary_action = (values) => {
			this.create_an_agreement(values)
		}
		const primary_action_label = __("Request eSignature")
		const dialog = new frappe.ui.Dialog({
			title,
			fields,
			primary_action,
			primary_action_label,
		})
		this.dialog = dialog
		this.setup_multiselect_queries(dialog)

		dialog.show()
	}

	get_modal_fields() {
		const me = this

		return [
			{
				label: __("Agreement Name"),
				fieldname: "agreement_name",
				fieldtype: "Data",
				reqd: 1,
			},
			{ fieldtype: "Section Break" },
			{
				label: __("Files"),
				fieldname: "files",
				fieldtype: "MultiCheck",
				reqd: 1,
				options: this.frm.attachments.get_attachments().map(a => ({
					label: a.file_name,
					value: a.name,
				})),
				// TODO: make all checkboxes checked by default
				// IDEA: add "Un/Check all" buttons? => Yes
				// IDEA: add a third button: Upload a file
			},
			/* {
				label: __("Files"),
				fieldname: "files2",
				fieldtype: "Table MultiSelect",
				reqd: 1,
				options: "File",
				only_select: true, // disable creation of docs
				get_query() {
					return { filters: { attached_to_name: ['=', me.frm.docname] } }
				},
			}, */
			{ fieldtype: "Section Break" },
			{
				label: __("Signers"),
				fieldname: "signers",
				fieldtype: "Table",
				reqd: 1,
				options: "Adobe Sign Agreement Users",
				fields: frappe.meta.get_docfields("Adobe Sign Agreement Users")
					.filter(df => df.fieldname === "email" || df.fieldname === "role"),

				// IDEA: add a button 'select a user' OR  add autocompletion on email addresses
				// TODO: Make SIGNER role default (a bug in the framework ?)
			},
		]
	}

	setup_multiselect_queries(dialog) {
		["signers"].forEach((field) => {
			this.dialog.fields_dict[field].get_data = () => {
				const data = this.dialog.fields_dict[field].get_value();
				const txt = data.match(/[^,\s*]*$/)[0] || "";

				frappe.call({
					method: "frappe.email.get_contact_list",
					args: { txt },
					callback: (r) => {
						this.dialog.fields_dict[field].set_data(r.message);
					},
				});
			};
		});
	}

	create_an_agreement(values) {
		console.log(values)
		return frappe.call({
			method: "frappe.client.insert",
			args: {
				doc: {
					doctype: "Adobe Sign Agreement",
					agreement_name: values.agreement_name,
					user: frappe.session.user,
					files: values.files.map(f => {
						return {
							file: f
						}
					}),
					users: values.signers
				}
			},
		}).then(() => {
			this.dialog.hide()
			frappe.show_alert({
				message: __("eSignature Request sent. Please check your email Inbox."),
				indicator: 'green'
			})
		})
	}
}

$(document).ready(() => {
	class ESignatureSidebar extends frappe.ui.form.Sidebar {
		make_attachments() {
			super.make_attachments()

			if (frappe.boot.adobe_sign_enabled == "1") {
				this.frm.esignature_menu = new ESignatureMenu({
					frm: this.frm,
					sidebar: this.sidebar,
				})
			}
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

	frappe.ui.form.Sidebar = ESignatureSidebar
})
