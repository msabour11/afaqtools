import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, get_formatted_email, today


def set_customer_series_on_create(doc, method):
    """
    Set customer series when a new customer is created.
    """

    if not doc.custom_customer_series and doc.customer:
        # Get the last used series for this customer
        last = frappe.db.get_value(
            "Sales Invoice",
            {"customer": doc.customer, "custom_customer_series": ["!=", ""]},
            "custom_customer_series",
            order_by="creation desc",
        )

        if last:
            # Extract number and increment
            try:
                num = int(last.split("-")[-1])
                new_num = f"{num + 1:04}"
            except:
                new_num = "0001"
        else:
            new_num = "0001"

        # Set the new series
        doc.custom_customer_series = f"{doc.customer[:4].upper()}-{new_num}"


# SI advance payment validation
def validate_advance_payment(doc, method):
    """
    Validate that advance payment is allocated before submitting the Sales Invoice.
    """
    if doc.custom_is_mandatory_payment and doc.total_advance <= 0:

        frappe.throw(
            _(
                "You must allocate an advance payment before submitting this Sales Invoice."
            ),
            title=_("Advance Payment Required"),
        )


@frappe.whitelist()
def get_customer_outstanding(
    customer, company, ignore_outstanding_sales_order=False, cost_center=None
):
    # Outstanding based on GL Entries
    cond = ""
    if cost_center:
        lft, rgt = frappe.get_cached_value("Cost Center", cost_center, ["lft", "rgt"])

        cond = f""" and cost_center in (select name from `tabCost Center` where
			lft >= {lft} and rgt <= {rgt})"""

    outstanding_based_on_gle = frappe.db.sql(
        f"""
		select sum(debit) - sum(credit)
		from `tabGL Entry` where party_type = 'Customer'
		and is_cancelled = 0 and party = %s
		and company=%s {cond}""",
        (customer, company),
    )

    outstanding_based_on_gle = (
        flt(outstanding_based_on_gle[0][0]) if outstanding_based_on_gle else 0
    )

    # Outstanding based on Sales Order
    outstanding_based_on_so = 0

    # if credit limit check is bypassed at sales order level,
    # we should not consider outstanding Sales Orders, when customer credit balance report is run
    if not ignore_outstanding_sales_order:
        outstanding_based_on_so = frappe.db.sql(
            """
			select sum(base_grand_total*(100 - per_billed)/100)
			from `tabSales Order`
			where customer=%s and docstatus = 1 and company=%s
			and per_billed < 100 and status != 'Closed'""",
            (customer, company),
        )

        outstanding_based_on_so = (
            flt(outstanding_based_on_so[0][0]) if outstanding_based_on_so else 0
        )

    # Outstanding based on Delivery Note, which are not created against Sales Order
    outstanding_based_on_dn = 0

    unmarked_delivery_note_items = frappe.db.sql(
        """select
			dn_item.name, dn_item.amount, dn.base_net_total, dn.base_grand_total
		from `tabDelivery Note` dn, `tabDelivery Note Item` dn_item
		where
			dn.name = dn_item.parent
			and dn.customer=%s and dn.company=%s
			and dn.docstatus = 1 and dn.status not in ('Closed', 'Stopped')
			and ifnull(dn_item.against_sales_order, '') = ''
			and ifnull(dn_item.against_sales_invoice, '') = ''
		""",
        (customer, company),
        as_dict=True,
    )

    if not unmarked_delivery_note_items:
        return outstanding_based_on_gle + outstanding_based_on_so

    si_amounts = frappe.db.sql(
        """
		SELECT
			dn_detail, sum(amount) from `tabSales Invoice Item`
		WHERE
			docstatus = 1
			and dn_detail in ({})
		GROUP BY dn_detail""".format(
            ", ".join(
                frappe.db.escape(dn_item.name)
                for dn_item in unmarked_delivery_note_items
            )
        )
    )

    si_amounts = {si_item[0]: si_item[1] for si_item in si_amounts}

    for dn_item in unmarked_delivery_note_items:
        dn_amount = flt(dn_item.amount)
        si_amount = flt(si_amounts.get(dn_item.name))

        if dn_amount > si_amount and dn_item.base_net_total:
            outstanding_based_on_dn += (
                (dn_amount - si_amount) / dn_item.base_net_total
            ) * dn_item.base_grand_total

    return outstanding_based_on_gle + outstanding_based_on_so + outstanding_based_on_dn
