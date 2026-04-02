# AG CM - Construction Management Module
{
    "name": "AG CM",
    "technical_name": "agcm",
    "version": "1.0.0",
    "summary": "Construction project daily log management",
    "description": """
# AG Construction Management

Daily activity logging system for construction projects.

## Features

- **Projects**: Track construction projects with location, contractors, trades
- **Daily Logs**: Per-project daily activity records
- **Weather**: Auto-fetch weather data from weather.gov / open-meteo
- **Manpower**: Track workers, hours, contractors per day
- **Inspections**: Third-party inspection tracking
- **Safety**: Accident reporting and safety violation observations
- **Visitors**: Visitor log with entry/exit times
- **Delays**: Delay tracking with contractor and reason
- **Deficiencies**: Deficiency reporting
- **Photos**: Photo documentation with albums
    """,
    "author": "FastVue",
    "license": "MIT",
    "category": "Projects",

    "application": True,
    "installable": True,
    "auto_install": False,

    "depends": ["base"],
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
        "views/dashboard-overview.vue",
        "views/dashboard-project.vue",
        "views/dashboard-dailylog.vue",
        "views/projects.vue",
        "views/project-form.vue",
        "views/project-detail.vue",
        "views/daily-logs.vue",
        "views/daily-log-form.vue",
        "views/daily-log-detail.vue",
        "views/daily-log-copy.vue",
        "views/periodic-report.vue",
        "views/settings-trades.vue",
        "views/settings-inspection-types.vue",
        "views/settings-accident-types.vue",
        "views/settings-violation-types.vue",
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
            "name": "Projects",
            "path": "/agcm",
            "icon": "lucide:hard-hat",
            "sequence": 1,
            "children": [
                {
					"name": "Dashboard",
					"path": "/agcm/dashboard/overview",
					"icon": "lucide:bar-chart-3",
					"sequence": 1,
					"viewName": "dashboard-overview",
				},
				{
					"name": "Project Analytics",
					"path": "/agcm/dashboard/project",
					"icon": "lucide:trending-up",
					"sequence": 2,
					"viewName": "dashboard-project",
				},
				{
					"name": "Daily Log Analytics",
					"path": "/agcm/dashboard/dailylog",
					"icon": "lucide:pie-chart",
					"sequence": 3,
					"viewName": "dashboard-dailylog",
				},
				{
                    "name": "Periodic Project Report",
                    "path": "/agcm/periodic-report",
                    "icon": "lucide:file-bar-chart",
                    "sequence": 4,
                    "viewName": "periodic-report",
                },
                {
                    "name": "Projects",
                    "path": "/agcm/projects",
                    "icon": "lucide:building-2",
                    "sequence": 10,
                    "viewName": "projects",
                },
                {
                    "name": "Daily Logs",
                    "path": "/agcm/daily-logs",
                    "icon": "lucide:clipboard-list",
                    "sequence": 20,
                    "viewName": "daily-logs",
                },
               
                # Hidden routes for forms/details
                {
                    "name": "Project Form",
                    "path": "/agcm/projects/form",
                    "hideInMenu": True,
                    "viewName": "project-form",
                    "sequence": 100,
                },
                {
                    "name": "Project Detail",
                    "path": "/agcm/projects/detail",
                    "hideInMenu": True,
                    "viewName": "project-detail",
                    "sequence": 101,
                },
                {
                    "name": "Daily Log Form",
                    "path": "/agcm/daily-logs/form",
                    "hideInMenu": True,
                    "viewName": "daily-log-form",
                    "sequence": 102,
                },
                {
                    "name": "Daily Log Detail",
                    "path": "/agcm/daily-logs/detail",
                    "hideInMenu": True,
                    "viewName": "daily-log-detail",
                    "sequence": 103,
                },
                {
                    "name": "Copy Daily Log",
                    "path": "/agcm/daily-logs/copy",
                    "hideInMenu": True,
                    "viewName": "daily-log-copy",
                    "sequence": 104,
                },
                {
                    "name": "Settings",
                    "path": "/agcm/settings",
                    "icon": "lucide:settings",
                    "sequence": 99,
                    "children": [
                        {
                            "name": "Trades",
                            "path": "/agcm/settings/trades",
                            "icon": "lucide:wrench",
                            "sequence": 1,
                            "viewName": "settings-trades",
                        },
                        {
                            "name": "Inspection Types",
                            "path": "/agcm/settings/inspection-types",
                            "icon": "lucide:search-check",
                            "sequence": 2,
                            "viewName": "settings-inspection-types",
                        },
                        {
                            "name": "Accident Types",
                            "path": "/agcm/settings/accident-types",
                            "icon": "lucide:alert-triangle",
                            "sequence": 3,
                            "viewName": "settings-accident-types",
                        },
                        {
                            "name": "Violation Types",
                            "path": "/agcm/settings/violation-types",
                            "icon": "lucide:shield-alert",
                            "sequence": 4,
                            "viewName": "settings-violation-types",
                        },
                    ],
                },
            ],
        },
    ],

    "permissions": [
        "agcm.project.view",
        "agcm.project.create",
        "agcm.project.edit",
        "agcm.project.delete",
        "agcm.dailylog.view",
        "agcm.dailylog.create",
        "agcm.dailylog.edit",
        "agcm.dailylog.delete",
        "agcm.settings.manage",
    ],

    "access_rights": [
        {
            "name": "agcm.manager",
            "model": "agcm.agcm_projects",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm.user",
            "model": "agcm.agcm_projects",
            "permissions": {"read": True, "write": False, "create": False, "delete": False},
            "groups": ["base.group_user"],
            "domain": "[('user_ids', 'contains', user.id)]",
        },
        {
            "name": "agcm.dailylog.manager",
            "model": "agcm.agcm_daily_activity_logs",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm.dailylog.user",
            "model": "agcm.agcm_daily_activity_logs",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_user"],
        },
    ],
}
