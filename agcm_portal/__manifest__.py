# AGCM Portal - Client & Subcontractor Portals
{
    "name": "AGCM Portal",
    "technical_name": "agcm_portal",
    "version": "1.0.0",
    "summary": "Client and subcontractor portal management",
    "description": """
# AGCM Portal

Client and subcontractor portal for construction projects.

## Features

- **Selections**: Material/finish choices for client approval
- **Bid Packages**: Bid requests and submission management
- **Portal Settings**: Per-project portal visibility configuration
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
        "views/selections.vue",
        "views/bids.vue",
        "views/portal-settings.vue",
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
            "name": "Portals",
            "path": "/agcm/portals",
            "icon": "lucide:door-open",
            "sequence": 44,
            "parent": "agcm",
            "children": [
                {
                    "name": "Selections",
                    "path": "/agcm/portals/selections",
                    "icon": "lucide:palette",
                    "sequence": 1,
                    "viewName": "selections",
                },
                {
                    "name": "Bid Packages",
                    "path": "/agcm/portals/bids",
                    "icon": "lucide:file-signature",
                    "sequence": 2,
                    "viewName": "bids",
                },
                {
                    "name": "Portal Settings",
                    "path": "/agcm/portals/settings",
                    "icon": "lucide:settings-2",
                    "sequence": 3,
                    "viewName": "portal-settings",
                },
            ],
        },
    ],

    "permissions": [
        "agcm_portal.selection.view",
        "agcm_portal.selection.create",
        "agcm_portal.selection.edit",
        "agcm_portal.selection.delete",
        "agcm_portal.bid.view",
        "agcm_portal.bid.create",
        "agcm_portal.bid.edit",
        "agcm_portal.bid.delete",
        "agcm_portal.config.manage",
    ],

    "access_rights": [
        {
            "name": "agcm_portal.manager",
            "model": "agcm_portal.agcm_selections",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_portal.user",
            "model": "agcm_portal.agcm_selections",
            "permissions": {"read": True, "write": False, "create": False, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
