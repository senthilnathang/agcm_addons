# AG CM Estimating & Takeoff Module — Procore/Buildern-inspired
{
    "name": "AG CM Estimating",
    "technical_name": "agcm_estimate",
    "version": "1.0.0",
    "summary": "Construction estimating with cost catalogs, assemblies, takeoff, and proposals",
    "description": """
# AG CM Estimating & Takeoff

Full construction estimating platform inspired by Procore and Buildern.

## Features

- **Cost Catalog**: Company-wide reusable material, labor, equipment, subcontractor pricing
- **Assemblies**: Grouped cost templates (e.g., "Foundation Package", "Interior Wall")
- **Estimates**: Multi-group line-item estimates with markup, tax, and versioning
- **Markups**: Overhead, profit, contingency — percentage or lump sum, compounding
- **Proposals**: Client-facing proposals from estimates with branded PDF export
- **Takeoff**: Plan upload with linear, area, count measurements linked to estimates
- **Budget Integration**: Send estimate to budget (creates agcm_finance budget lines)
- **Versioning**: Create new versions from existing estimates, compare versions
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
        "views/estimates.vue",
        "views/estimate-detail.vue",
        "views/cost-catalog.vue",
        "views/assemblies.vue",
        "views/proposals.vue",
        "views/takeoff-sheets.vue",
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
            "name": "Estimate",
            "path": "/agcm/estimate",
            "icon": "lucide:calculator",
            "sequence": 32,
            "children": [
                {
                    "name": "Estimates",
                    "path": "/agcm/estimate/estimates",
                    "icon": "lucide:file-spreadsheet",
                    "sequence": 1,
                    "viewName": "estimates",
                },
                {
                    "name": "Cost Catalog",
                    "path": "/agcm/estimate/cost-catalog",
                    "icon": "lucide:library",
                    "sequence": 2,
                    "viewName": "cost-catalog",
                },
                {
                    "name": "Assemblies",
                    "path": "/agcm/estimate/assemblies",
                    "icon": "lucide:boxes",
                    "sequence": 3,
                    "viewName": "assemblies",
                },
                {
                    "name": "Proposals",
                    "path": "/agcm/estimate/proposals",
                    "icon": "lucide:file-signature",
                    "sequence": 4,
                    "viewName": "proposals",
                },
                {
                    "name": "Takeoff Sheets",
                    "path": "/agcm/estimate/takeoffs",
                    "icon": "lucide:ruler",
                    "sequence": 5,
                    "viewName": "takeoff-sheets",
                },
            ],
        },
        {
            "name": "Estimate Detail",
            "path": "/agcm/estimate/estimates/detail",
            "parent": "agcm_estimate.agcm.estimate",
            "hideInMenu": True,
            "viewName": "estimate-detail",
            "sequence": 115,
        },
    ],
    "permissions": [
        "agcm_estimate.estimate.view",
        "agcm_estimate.estimate.create",
        "agcm_estimate.estimate.edit",
        "agcm_estimate.estimate.delete",
        "agcm_estimate.estimate.approve",
        "agcm_estimate.catalog.view",
        "agcm_estimate.catalog.manage",
        "agcm_estimate.assembly.view",
        "agcm_estimate.assembly.manage",
        "agcm_estimate.proposal.view",
        "agcm_estimate.proposal.create",
        "agcm_estimate.proposal.send",
        "agcm_estimate.takeoff.view",
        "agcm_estimate.takeoff.manage",
    ],
    "access_rights": [
        {
            "name": "agcm_estimate.manager",
            "model": "agcm_estimate.agcm_estimates",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_estimate.user",
            "model": "agcm_estimate.agcm_estimates",
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
