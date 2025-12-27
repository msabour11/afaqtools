frappe.ui.form.on("Customer", {
	refresh: function (frm) {
		calculate_outstanding_amount(frm);

		frm.set_query("custom_cost_center", function () {
			return {
				filters: {
					company: frm.doc.custom_branch,
					is_group: 0,
				},
			};
		});

		frm.set_query("custom_default_warehouse", function () {
			return {
				filters: {
					company: frm.doc.custom_branch,
					is_group: 0,
				},
			};
		});
		frm.set_query("custom_mode_of_payment", function () {
			return {
				filters: {
					company: frm.doc.custom_branch,
				},
			};
		});
	},
});

function calculate_outstanding_amount(frm) {
	frappe.call({
		method: "afaqtools.overrides.api.get_customer_outstanding",
		args: {
			customer: frm.doc.name,
			company: frm.doc.custom_branch || frappe.defaults.get_default("company"),
		},
		callback: (r) => {
			frm.doc.custom_outstanding_amount = r.message;
			frm.set_value("custom_outstanding_amount", r.message);
			frm.refresh_field("custom_outstanding_amount");
			console.log("Outstanding Amount:", r.message);
			frm.refresh_field("credit_limit");
			calculate_outstanding_amount_from_credit_limit(frm, r.message);
		},
	});
}

//////////////////////
function calculate_outstanding_amount_from_credit_limit(frm, total_outstanding) {
	if (!frm.doc.credit_limits || !frm.doc.credit_limits.length) return;

	frm.doc.credit_limits.forEach((row) => {
		let credit_limit = flt(row.credit_limit) || 0;

		if (!credit_limit) return;

		let outstanding_amount = (total_outstanding / credit_limit) * 100;

		frappe.model.set_value(
			row.doctype,
			row.name,
			"custom_credit_limit_percent",
			outstanding_amount
		);
	});
	frm.save();

	frm.refresh_field("credit_limits");
}
