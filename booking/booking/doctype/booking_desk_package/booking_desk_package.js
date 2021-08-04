// Copyright (c) 2021, Booking and contributors
// For license information, please see license.txt

frappe.ui.form.on('Booking Desk Package', {
	booking_desk_type: function(frm) {
		if (frm.doc.booking_desk_type) {
			frappe.model.with_doc('Booking Desk Type', frm.doc.booking_desk_type, () => {
				let booking_desk_type = frappe.get_doc('Booking Desk Type', frm.doc.booking_desk_type);

				// reset the amenities
				frm.doc.amenities = [];

				for (let amenity of booking_desk_type.amenities) {
					let d = frm.add_child('amenities');
					d.item = amenity.item;
					d.billable = amenity.billable;
				}

				frm.refresh();
			});
		}
	}
});
