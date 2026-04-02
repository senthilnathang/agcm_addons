# AG CM Safety - Quality & Safety Management Module
{
    "name": "AG CM Safety",
    "technical_name": "agcm_safety",
    "version": "1.0.0",
    "summary": "Quality and safety management for construction projects",
    "description": """
# AG CM Safety

Quality and safety management for construction projects.

## Features

- **Checklist Templates**: Reusable inspection checklist templates with configurable items
- **Inspections**: Scheduled inspections with checklist-based item tracking
- **Punch List**: Track deficiencies with status, priority, and assignment workflow
- **Incident Reports**: Safety incident reporting with severity, investigation, and OSHA tracking
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
        "views/checklists.vue",
        "views/inspections.vue",
        "views/punch-list.vue",
        "views/incidents.vue",
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
            "name": "Quality & Safety",
            "path": "/agcm/safety",
            "icon": "lucide:shield-check",
            "sequence": 43,
            "children": [
                {
                    "name": "Checklists",
                    "path": "/agcm/safety/checklists",
                    "icon": "lucide:list-checks",
                    "sequence": 1,
                    "viewName": "checklists",
                },
                {
                    "name": "Inspections",
                    "path": "/agcm/safety/inspections",
                    "icon": "lucide:clipboard-check",
                    "sequence": 2,
                    "viewName": "inspections",
                },
                {
                    "name": "Punch List",
                    "path": "/agcm/safety/punch-list",
                    "icon": "lucide:list-todo",
                    "sequence": 3,
                    "viewName": "punch-list",
                },
                {
                    "name": "Incidents",
                    "path": "/agcm/safety/incidents",
                    "icon": "lucide:alert-triangle",
                    "sequence": 4,
                    "viewName": "incidents",
                },
            ],
        },
    ],
    "permissions": [
        "agcm_safety.checklist.view",
        "agcm_safety.checklist.manage",
        "agcm_safety.inspection.view",
        "agcm_safety.inspection.create",
        "agcm_safety.inspection.edit",
        "agcm_safety.punch_list.view",
        "agcm_safety.punch_list.manage",
        "agcm_safety.incident.view",
        "agcm_safety.incident.manage",
    ],
    "access_rights": [
        {
            "name": "agcm_safety.manager",
            "model": "agcm_safety.agcm_inspections_v2",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_safety.user",
            "model": "agcm_safety.agcm_inspections_v2",
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
