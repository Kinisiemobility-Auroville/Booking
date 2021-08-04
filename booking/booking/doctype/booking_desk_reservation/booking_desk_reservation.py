# Copyright (c) 2021, Booking and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe import _
from frappe.utils import date_diff, add_days, flt

class BookingDeskUnavailableError(frappe.ValidationError): pass
class BookingDeskPricingNotSetError(frappe.ValidationError): pass

class BookingDeskReservation(Document):
	def validate(self):
		self.total_desk = {}
		self.set_rates()
		self.validate_availability()

	def validate_availability(self):
		for i in range(date_diff(self.to_date, self.from_date)):
			day = add_days(self.from_date, i)
			self.desk_booked = {}

			for d in self.items:
				if not d.item in self.desk_booked:
					self.desk_booked[d.item] = 0

				desk_type = frappe.db.get_value("Booking Desk Package",
					d.item, 'booking_desk_type')
				desk_booked = get_desk_booked(desk_type, day, exclude_reservation=self.name) \
					+ d.qty + self.desk_booked.get(d.item)
				print(d.item)
				total_desk = self.get_total_desk(d.item)
				print("####")
				print(total_desk,desk_booked)
				if total_desk < desk_booked:
					frappe.throw(_("Booking Desk of type {0} are unavailable on {1}").format(d.item,
						frappe.format(day, dict(fieldtype="Date"))), exc=BookingDeskUnavailableError)

				self.desk_booked[d.item] += desk_booked

	def get_total_desk(self, item):
		print("*****")
		print(item)
		if not item in self.total_desk:
			self.total_desk[item] = frappe.db.sql("""
				select count(*)
				from
					`tabBooking Desk Package` package
				inner join
					`tabBooking Desk` desk on package.booking_desk_type = desk.booking_desk_type
				where
					package.item = %s""", item)[0][0] or 0

		return self.total_desk[item]

	def set_rates(self):
		self.net_total = 0
		for d in self.items:
			net_rate = 0.0
			for i in range(date_diff(self.to_date, self.from_date)):
				day = add_days(self.from_date, i)
				if not d.item:
					continue
				day_rate = frappe.db.sql("""
					select
						item.rate
					from
						`tabBooking Desk Pricing Item` item,
						`tabBooking Desk Pricing` pricing
					where
						item.parent = pricing.name
						and item.item = %s
						and %s between pricing.from_date
							and pricing.to_date""", (d.item, day))

				if day_rate:
					net_rate += day_rate[0][0]
				else:
					frappe.throw(
						_("Please set Booking Desk Rate on {}").format(
							frappe.format(day, dict(fieldtype="Date"))), exc=BookingDeskPricingNotSetError)
			d.rate = net_rate
			d.amount = net_rate * flt(d.qty)
			self.net_total += d.amount

@frappe.whitelist()
def get_desk_rate(booking_desk_reservation):
	"""Calculate rate for each day as it may belong to different Booking Desk Pricing Item"""
	doc = frappe.get_doc(json.loads(booking_desk_reservation))
	doc.set_rates()
	return doc.as_dict()

def get_desk_booked(desk_type, day, exclude_reservation=None):
	exclude_condition = ''
	if exclude_reservation:
		exclude_condition = 'and reservation.name != {0}'.format(frappe.db.escape(exclude_reservation))

	return frappe.db.sql("""
		select sum(item.qty)
		from
			`tabBooking Desk Package` desk_package,
			`tabBooking Desk Reservation Item` item,
			`tabBooking Desk Reservation` reservation
		where
			item.parent = reservation.name
			and desk_package.item = item.item
			and desk_package.booking_desk_type = %s
			and reservation.docstatus = 1
			{exclude_condition}
			and %s between reservation.from_date
				and reservation.to_date""".format(exclude_condition=exclude_condition),
				(desk_type, day))[0][0] or 0

	
