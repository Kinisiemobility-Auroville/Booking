from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import add_days, date_diff

from booking.booking.doctype.booking_desk_reservation.booking_desk_reservation import get_desk_booked

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		dict(label=_("Desk Type"), fieldname="desk_type"),
		dict(label=_("Desk Booked"), fieldtype="Int")
	]
	return columns

def get_data(filters):
	out = []
	for desk_type in frappe.get_all('Booking Desk Type'):
		total_booked = 0
		for i in range(date_diff(filters.to_date, filters.from_date)):
			day = add_days(filters.from_date, i)
			total_booked += get_desk_booked(desk_type.name, day)

		out.append([desk_type.name, total_booked])

	return out