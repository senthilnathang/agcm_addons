# AGCM Progress - Construction Progress Tracking Module
{
    "name": "AGCM Progress",
    "technical_name": "agcm_progress",
    "version": "1.0.0",
    "summary": "Construction progress tracking, issues, estimation, milestones, and S-curve",
    "description": """
# AGCM Progress

Progress tracking module for construction projects.

## Features

- **Milestones**: Track project milestones with planned/actual dates
- **Issues**: Issue tracking with severity, status, priority workflow
- **Estimation**: Hierarchical cost estimation with rollup totals
- **S-Curve**: Periodic progress snapshots with chart visualization
- **Project Images**: Progress photo gallery with metadata
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
        "views/milestones.vue",
        "views/issues.vue",
        "views/issue-form.vue",
        "views/estimation.vue",
        "views/scurve.vue",
        "views/project-images.vue",
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
            "name": "Issues",
            "path": "/agcm/issues",
            "parent": "agcm",
            "icon": "lucide:alert-circle",
            "sequence": 39,
            "viewName": "issues",
        },
        {
            "name": "Progress",
            "path": "/agcm/progress",
            "parent": "agcm",
            "icon": "lucide:trending-up",
            "sequence": 41,
            "children": [
                {
                    "name": "S-Curve",
                    "path": "/agcm/progress/scurve",
                    "icon": "lucide:line-chart",
                    "sequence": 1,
                    "viewName": "scurve",
                },
                {
                    "name": "Milestones",
                    "path": "/agcm/progress/milestones",
                    "icon": "lucide:flag",
                    "sequence": 2,
                    "viewName": "milestones",
                },
                {
                    "name": "Estimation",
                    "path": "/agcm/progress/estimation",
                    "icon": "lucide:calculator",
                    "sequence": 3,
                    "viewName": "estimation",
                },
                {
                    "name": "Project Images",
                    "path": "/agcm/progress/project-images",
                    "icon": "lucide:image",
                    "sequence": 4,
                    "viewName": "project-images",
                },
            ],
        },
        {
            "name": "Issue Form",
            "path": "/agcm/issues/form",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "issue-form",
            "sequence": 109,
        },
    ],

    "permissions": [
        "agcm_progress.issue.view",
        "agcm_progress.issue.create",
        "agcm_progress.issue.edit",
        "agcm_progress.issue.delete",
        "agcm_progress.milestone.view",
        "agcm_progress.milestone.create",
        "agcm_progress.milestone.edit",
        "agcm_progress.milestone.delete",
        "agcm_progress.estimation.view",
        "agcm_progress.estimation.create",
        "agcm_progress.estimation.edit",
        "agcm_progress.estimation.delete",
        "agcm_progress.scurve.view",
        "agcm_progress.scurve.create",
        "agcm_progress.scurve.edit",
        "agcm_progress.scurve.delete",
        "agcm_progress.image.view",
        "agcm_progress.image.create",
        "agcm_progress.image.edit",
        "agcm_progress.image.delete",
    ],

    "access_rights": [
        {
            "name": "agcm_progress.manager",
            "model": "agcm_progress.agcm_milestones",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_progress.user",
            "model": "agcm_progress.agcm_milestones",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
