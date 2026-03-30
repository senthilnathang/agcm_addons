# AG CM Submittal - Construction Submittal Management Module
{
    "name": "AG CM Submittals",
    "technical_name": "agcm_submittal",
    "version": "1.0.0",
    "summary": "Construction submittal management with multi-step approval workflow",
    "description": """
# AG Construction Submittal Management

Manage construction submittals with approval workflows.

## Features

- **Submittals**: Track submittals with status, priority, revision history
- **Approval Chain**: Multi-step approval workflow with sequence ordering
- **Packages**: Group related submittals into packages
- **Types**: Classify submittals (product data, shop drawings, samples, etc.)
- **Labels**: Color-coded labels for categorization
    """,
    "author": "FastVue",
    "license": "MIT",
    "category": "Construction",

    "application": True,
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
        "views/submittals.vue",
        "views/submittal-form.vue",
        "views/submittal-detail.vue",
        "views/settings-submittal-types.vue",
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
            "name": "Submittals",
            "path": "/agcm/submittals",
            "parent": "agcm",
            "icon": "lucide:file-check-2",
            "sequence": 36,
            "viewName": "submittals",
        },
        {
            "name": "Submittal Form",
            "path": "/agcm/submittals/form",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "submittal-form",
            "sequence": 110,
        },
        {
            "name": "Submittal Detail",
            "path": "/agcm/submittals/detail",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "submittal-detail",
            "sequence": 111,
        },
        {
            "name": "Submittal Types",
            "path": "/agcm/settings/submittal-types",
            "parent": "agcm.settings",
            "icon": "lucide:file-type",
            "sequence": 6,
            "viewName": "settings-submittal-types",
        },
    ],

    "permissions": [
        "agcm_submittal.submittal.view",
        "agcm_submittal.submittal.create",
        "agcm_submittal.submittal.edit",
        "agcm_submittal.submittal.delete",
        "agcm_submittal.settings.manage",
    ],

    "access_rights": [
        {
            "name": "agcm_submittal.manager",
            "model": "agcm_submittal.agcm_submittals",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_submittal.user",
            "model": "agcm_submittal.agcm_submittals",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
