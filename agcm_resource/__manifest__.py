# AG CM Resource - Construction Resource Management Module
{
    "name": "AG CM Resource",
    "technical_name": "agcm_resource",
    "version": "1.0.0",
    "summary": "Construction workforce, equipment, and timesheet management",
    "description": """
# AG Construction Resource Management

Resource tracking for construction projects.

## Features

- **Workers**: Workforce roster with trade, skill level, certifications
- **Equipment**: Equipment register with maintenance tracking
- **Timesheets**: Daily time entries with cost calculations
- **Equipment Assignments**: Track equipment allocation to projects
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
        "views/workers.vue",
        "views/equipment.vue",
        "views/timesheets.vue",
        "views/equipment-assignments.vue",
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
            "name": "Resources",
            "path": "/agcm/resources",
            "icon": "lucide:users",
            "sequence": 42,
            "children": [
                {
                    "name": "Workers",
                    "path": "/agcm/resources/workers",
                    "icon": "lucide:hard-hat",
                    "sequence": 1,
                    "viewName": "workers",
                },
                {
                    "name": "Equipment",
                    "path": "/agcm/resources/equipment",
                    "icon": "lucide:truck",
                    "sequence": 2,
                    "viewName": "equipment",
                },
                {
                    "name": "Timesheets",
                    "path": "/agcm/resources/timesheets",
                    "icon": "lucide:clock",
                    "sequence": 3,
                    "viewName": "timesheets",
                },
                {
                    "name": "Equipment Assignments",
                    "path": "/agcm/resources/equipment-assignments",
                    "icon": "lucide:link",
                    "sequence": 4,
                    "viewName": "equipment-assignments",
                },
            ],
        },
    ],
    "permissions": [
        "agcm_resource.worker.view",
        "agcm_resource.worker.create",
        "agcm_resource.worker.edit",
        "agcm_resource.worker.delete",
        "agcm_resource.equipment.view",
        "agcm_resource.equipment.create",
        "agcm_resource.equipment.edit",
        "agcm_resource.equipment.delete",
        "agcm_resource.timesheet.view",
        "agcm_resource.timesheet.create",
        "agcm_resource.timesheet.edit",
        "agcm_resource.timesheet.delete",
        "agcm_resource.timesheet.approve",
    ],
    "access_rights": [
        {
            "name": "agcm_resource.manager",
            "model": "agcm_resource.agcm_workers",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_resource.user",
            "model": "agcm_resource.agcm_workers",
            "permissions": {
                "read": True,
                "write": False,
                "create": False,
                "delete": False,
            },
            "groups": ["base.group_user"],
        },
        {
            "name": "agcm_resource.equipment.manager",
            "model": "agcm_resource.agcm_equipment",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_resource.timesheet.manager",
            "model": "agcm_resource.agcm_timesheets",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_resource.timesheet.user",
            "model": "agcm_resource.agcm_timesheets",
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
