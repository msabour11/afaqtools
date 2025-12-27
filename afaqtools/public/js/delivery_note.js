frappe.ui.form.on("Delivery Note", {
	customer: function (frm) {
		if (!frm.doc.customer) return;

		frappe.db.get_value("Customer", frm.doc.customer, "custom_cost_center", (r) => {
			if (r && r.custom_cost_center) {
				frm.set_value("cost_center", r.custom_cost_center);
			} else {
				frappe.throw(
					__("Please set Custom Cost Center for the Customer.") +
						` <a href="/app/customer/${frm.doc.customer}">Go to Customer</a>`
				);
			}
		});
		frappe.db.get_value("Customer", frm.doc.customer, "custom_default_warehouse", (r) => {
			if (r && r.custom_default_warehouse) {
				frm.set_value("set_warehouse", r.custom_default_warehouse);
			} else {
				frappe.throw(
					__("Please set Custom Default Warehouse for the Customer.") +
						` <a href="/app/customer/${frm.doc.customer}">Go to Customer</a>`
				);
			}
		});
	},
});
