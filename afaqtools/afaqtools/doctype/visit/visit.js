// Copyright (c) 2025, Mohamed AbdElsabour and contributors
// For license information, please see license.txt

frappe.ui.form.on("Visit", {
	refresh(frm) {},
});

frappe.ui.form.on("Visit Schedule", {
	from_time(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		validate_from_to(frm, cdt, cdn);
		calculate_visit_duration(frm, cdt, cdn);
	},
	to_time(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		validate_from_to(frm, cdt, cdn);
		if (row.from_time && row.to_time) {
			calculate_visit_duration(frm, cdt, cdn);
		}
	},
});

function validate_from_to(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (row.from_time >= row.to_time) {
		frappe.msgprint(__("To Time must be greater than From Time"));
		row.to_time = null;
		frm.refresh_field("visit_schedule");
	}
}
function calculate_visit_duration(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (row.from_time && row.to_time) {
		let today = frappe.datetime.get_today();
		let from_datetime = today + " " + row.from_time;
		let to_datetime = today + " " + row.to_time;

		//  difference in minutes
		let duration_minutes = frappe.datetime.get_minute_diff(to_datetime, from_datetime);

		// format as HH:MM
		let hours = Math.floor(duration_minutes / 60);
		let minutes = duration_minutes % 60;
		let visit_duration = hours + ":" + (minutes < 10 ? "0" + minutes : minutes);

		frappe.model.set_value(cdt, cdn, "visit_duration", visit_duration);
		frm.refresh_field("visit_schedule");
	}
}
