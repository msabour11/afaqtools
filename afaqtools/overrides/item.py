import frappe
from frappe.model.naming import make_autoname


def autoname_item(doc, method=None):
    if not doc.custom_item_group_id:
        frappe.throw("Custom Item Group ID is required")

    group_id = str(doc.custom_item_group_id)

    # Prefix
    prefix = f"{group_id}_"

    #  last item for this group
    last_item = frappe.db.sql(
        """
        SELECT name
        FROM `tabItem`
        WHERE name LIKE %s
        ORDER BY name DESC
        LIMIT 1
        """,
        (prefix + "%",),
        as_dict=True,
    )

    if last_item:
        last_number = int(last_item[0]["name"].split("_")[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    doc.name = f"{prefix}{str(new_number).zfill(3)}"
