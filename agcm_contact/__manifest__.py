{
    "name": "AG CM Contacts & Vendors",
    "technical_name": "agcm_contact",
    "version": "1.0.0",
    "summary": "Centralized vendor, client, and subcontractor directory",
    "description": """
# AG CM Contacts & Vendors

Centralized directory for vendors, clients, subcontractors, and suppliers.
Replaces denormalized vendor_name strings across POs, Bills, Subcontracts, Invoices.

## Features
- Company-wide vendor directory with type classification
- Contact info: email, phone, address, tax ID
- Vendor search and filtering
- Prequalification tracking (payment terms, status)
    """,
    "author": "FastVue",
    "license": "MIT",
    "category": "Construction",
    "application": False,
    "installable": True,
    "auto_install": False,
    "depends": ["agcm"],
    "external_dependencies": {"python": [], "bin": []},
    "models": ["models"],
    "api": ["api"],
    "services": ["services"],
    "data": [],
    "demo": [],
    "views": [
        "views/vendors.vue",
    ],
    "assets": {
        "routes": None,
        "stores": [],
        "components": [],
        "views": [],
        "styles": [],
        "locales": [],
        "assets": [],
    },
    "menus": [
        {
            "name": "Contacts",
            "path": "/agcm/contacts",
            "icon": "lucide:contact",
            "sequence": 15,
            "children": [
                {
                    "name": "Vendors & Contacts",
                    "path": "/agcm/contacts/vendors",
                    "icon": "lucide:building-2",
                    "sequence": 1,
                    "viewName": "vendors",
                },
            ],
        },
    ],
    "permissions": [
        "agcm_contact.vendor.view",
        "agcm_contact.vendor.create",
        "agcm_contact.vendor.edit",
        "agcm_contact.vendor.delete",
    ],
    "access_rights": [
        {
            "name": "agcm_contact.manager",
            "model": "agcm_contact.agcm_vendors",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_contact.user",
            "model": "agcm_contact.agcm_vendors",
            "permissions": {"read": True, "write": False, "create": False, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
