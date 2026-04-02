# AG CM RFI - Request for Information Module
{
    "name": "AG CM RFI",
    "technical_name": "agcm_rfi",
    "version": "1.0.0",
    "summary": "Request for Information workflow for construction projects",
    "description": """
# AG CM RFI

Request for Information (RFI) management for construction projects.

## Features

- **RFI Workflow**: Draft → Open → In Progress → Answered → Closed
- **Threaded Responses**: Nested response threads with official response marking
- **Assignees**: Multi-user assignment per RFI
- **Labels**: Custom color-coded labels for categorization
- **Impact Tracking**: Schedule impact (days) and cost impact ($)
- **Priority**: Low / Medium / High priority levels
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
        "views/rfis.vue",
        "views/rfi-form.vue",
        "views/rfi-detail.vue",
        "views/settings-rfi-labels.vue",
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
            "name": "RFI",
            "path": "/agcm/rfi",
            "icon": "lucide:message-circle-question",
            "sequence": 35,
            "children": [
                {
                    "name": "RFIs",
                    "path": "/agcm/rfi/rfis",
                    "icon": "lucide:message-circle-question",
                    "sequence": 1,
                    "viewName": "rfis",
                },
                {
                    "name": "RFI Labels",
                    "path": "/agcm/rfi/labels",
                    "icon": "lucide:tags",
                    "sequence": 2,
                    "viewName": "settings-rfi-labels",
                },
            ],
        },
        {
            "name": "RFI Form",
            "path": "/agcm/rfi/form",
            "parent": "/agcm/rfi",
            "hideInMenu": True,
            "viewName": "rfi-form",
            "sequence": 105,
        },
        {
            "name": "RFI Detail",
            "path": "/agcm/rfi/detail",
            "parent": "/agcm/rfi",
            "hideInMenu": True,
            "viewName": "rfi-detail",
            "sequence": 106,
        },
    ],
    "permissions": [
        "agcm_rfi.rfi.view",
        "agcm_rfi.rfi.create",
        "agcm_rfi.rfi.edit",
        "agcm_rfi.rfi.delete",
        "agcm_rfi.settings.manage",
    ],
    "access_rights": [
        {
            "name": "agcm_rfi.manager",
            "model": "agcm_rfi.agcm_rfis",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_rfi.user",
            "model": "agcm_rfi.agcm_rfis",
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
