# AGCM Reporting - Executive Dashboards & Custom Reports
{
    "name": "AGCM Reporting",
    "technical_name": "agcm_reporting",
    "version": "1.0.0",
    "summary": "Executive dashboards and custom report builder",
    "description": """
# AGCM Reporting

Executive dashboards and custom report builder for construction management.

## Features

- **Report Builder**: Create custom reports with column/filter configuration
- **Report Schedules**: Scheduled report delivery via email
- **Dashboard Layouts**: Configurable widget-based dashboards
- **Portfolio KPIs**: Company-wide project metrics
- **Project KPIs**: Per-project safety, schedule, and activity metrics
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
        "views/reports.vue",
        "views/report-builder.vue",
        "views/dashboards.vue",
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
            "name": "Reporting",
            "path": "/agcm/reporting",
            "icon": "lucide:bar-chart-big",
            "sequence": 45,
            "parent": "agcm",
            "children": [
                {
                    "name": "Reports",
                    "path": "/agcm/reporting/reports",
                    "icon": "lucide:file-bar-chart-2",
                    "sequence": 1,
                    "viewName": "reports",
                },
                {
                    "name": "Dashboards",
                    "path": "/agcm/reporting/dashboards",
                    "icon": "lucide:layout-dashboard",
                    "sequence": 2,
                    "viewName": "dashboards",
                },
                # Hidden route for report builder
                {
                    "name": "Report Builder",
                    "path": "/agcm/reporting/report-builder",
                    "hideInMenu": True,
                    "viewName": "report-builder",
                    "sequence": 120,
                },
            ],
        },
    ],

    "permissions": [
        "agcm_reporting.report.view",
        "agcm_reporting.report.create",
        "agcm_reporting.report.edit",
        "agcm_reporting.report.delete",
        "agcm_reporting.dashboard.view",
        "agcm_reporting.dashboard.create",
        "agcm_reporting.dashboard.edit",
        "agcm_reporting.dashboard.delete",
    ],

    "access_rights": [
        {
            "name": "agcm_reporting.manager",
            "model": "agcm_reporting.agcm_report_definitions",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_reporting.user",
            "model": "agcm_reporting.agcm_report_definitions",
            "permissions": {"read": True, "write": False, "create": False, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
