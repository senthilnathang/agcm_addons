# AG CM Change Order - Construction Change Order Management Module
{
    "name": "AG CM Change Order",
    "technical_name": "agcm_change_order",
    "version": "1.0.0",
    "summary": "Change order management for construction projects",
    "description": """
# AG CM Change Order

Change order management for construction projects.

## Features

- **Change Order Workflow**: Draft → Pending → Approved / Rejected / Void
- **Line Items**: Itemized cost breakdown per change order
- **Impact Tracking**: Schedule impact (days) and cost impact ($)
- **Approval Workflow**: Approve/reject with audit trail
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
        "views/change-orders.vue",
        "views/change-order-form.vue",
        "views/change-order-detail.vue",
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
            "name": "Change Orders",
            "path": "/agcm/change-orders",
            "icon": "lucide:file-diff",
            "sequence": 37,
            "children": [
                {
                    "name": "Change Orders",
                    "path": "/agcm/change-orders/list",
                    "icon": "lucide:file-diff",
                    "sequence": 1,
                    "viewName": "change-orders",
                },
            ],
        },
        {
            "name": "Change Order Form",
            "path": "/agcm/change-orders/form",
            "parent": "/agcm/change-orders",
            "hideInMenu": True,
            "viewName": "change-order-form",
            "sequence": 107,
        },
        {
            "name": "Change Order Detail",
            "path": "/agcm/change-orders/detail",
            "parent": "/agcm/change-orders",
            "hideInMenu": True,
            "viewName": "change-order-detail",
            "sequence": 108,
        },
    ],
    "permissions": [
        "agcm_change_order.changeorder.view",
        "agcm_change_order.changeorder.create",
        "agcm_change_order.changeorder.edit",
        "agcm_change_order.changeorder.delete",
    ],
    "access_rights": [
        {
            "name": "agcm_change_order.manager",
            "model": "agcm_change_order.agcm_change_orders",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_change_order.user",
            "model": "agcm_change_order.agcm_change_orders",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": False,
            },
            "groups": ["base.group_user"],
        },
    ],
}
