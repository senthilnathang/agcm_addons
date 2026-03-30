# AG CM Procurement - Purchase Orders, Subcontracts, Vendor Bills
{
    "name": "AG CM Procurement",
    "technical_name": "agcm_procurement",
    "version": "1.0.0",
    "summary": "Procurement management for construction projects",
    "description": """
# AG CM Procurement

Procurement management for construction projects.

## Features

- **Purchase Orders**: PO creation, approval, line items, delivery tracking
- **Subcontracts**: Contract management, AIA G702/G703 SOV tracking, compliance docs
- **Vendor Bills**: Enhanced bills with line items, payments, OCR, PO matching, duplicate detection
    """,
    "author": "FastVue",
    "license": "MIT",
    "category": "Construction",

    "application": False,
    "installable": True,
    "auto_install": False,

    "depends": ["agcm"],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },

    "models": ["models"],
    "api": ["api"],
    "services": ["services"],
    "data": [],
    "demo": [],

    "views": [
        "views/purchase-orders.vue",
        "views/po-detail.vue",
        "views/subcontracts.vue",
        "views/subcontract-detail.vue",
        "views/vendor-bills.vue",
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
            "name": "Procurement",
            "path": "/agcm/procurement",
            "parent": "agcm",
            "icon": "lucide:shopping-cart",
            "sequence": 34,
            "children": [
                {
                    "name": "Purchase Orders",
                    "path": "/agcm/procurement/purchase-orders",
                    "icon": "lucide:file-text",
                    "sequence": 1,
                    "viewName": "purchase-orders",
                },
                {
                    "name": "Subcontracts",
                    "path": "/agcm/procurement/subcontracts",
                    "icon": "lucide:handshake",
                    "sequence": 2,
                    "viewName": "subcontracts",
                },
                {
                    "name": "Vendor Bills",
                    "path": "/agcm/procurement/vendor-bills",
                    "icon": "lucide:receipt",
                    "sequence": 3,
                    "viewName": "vendor-bills",
                },
            ],
        },
        {
            "name": "PO Detail",
            "path": "/agcm/procurement/purchase-orders/detail",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "po-detail",
            "sequence": 116,
        },
        {
            "name": "Subcontract Detail",
            "path": "/agcm/procurement/subcontracts/detail",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "subcontract-detail",
            "sequence": 117,
        },
    ],

    "permissions": [
        "agcm_procurement.po.view",
        "agcm_procurement.po.create",
        "agcm_procurement.po.edit",
        "agcm_procurement.po.delete",
        "agcm_procurement.po.approve",
        "agcm_procurement.subcontract.view",
        "agcm_procurement.subcontract.create",
        "agcm_procurement.subcontract.edit",
        "agcm_procurement.subcontract.delete",
        "agcm_procurement.subcontract.approve",
        "agcm_procurement.vendor_bill.view",
        "agcm_procurement.vendor_bill.create",
        "agcm_procurement.vendor_bill.edit",
        "agcm_procurement.vendor_bill.delete",
        "agcm_procurement.vendor_bill.approve",
    ],

    "access_rights": [
        {
            "name": "agcm_procurement.manager",
            "model": "agcm_procurement.agcm_purchase_orders",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_procurement.user",
            "model": "agcm_procurement.agcm_purchase_orders",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
