frappe.ui.form.on("Payment Entry", {
	refresh: function (frm) {},
	party: function (frm) {
		if (frm.doc.party_type === "Customer" && frm.doc.party) {
			frappe.db.get_value("Customer", frm.doc.party, "custom_mode_of_payment", (r) => {
				if (r && r.custom_mode_of_payment) {
					frm.set_value("mode_of_payment", r.custom_mode_of_payment);
				}
			});
		}
	},
});
