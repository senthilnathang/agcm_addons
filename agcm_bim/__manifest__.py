# AG CM BIM - Building Information Modeling Module
{
    "name": "AG CM BIM",
    "technical_name": "agcm_bim",
    "version": "1.0.0",
    "summary": "3D model management, viewpoints, and clash detection for construction projects",
    "description": """
# AG CM BIM

Building Information Modeling module for construction projects.

## Features

- **3D Models**: Upload and manage IFC, RVT, NWD, FBX, GLB, OBJ model files
- **Model Versioning**: Version chain with parent model tracking
- **Element Extraction**: Parse IFC elements with type, material, level, bounding box
- **BCF Viewpoints**: Save camera positions, section planes, annotations per model
- **Clash Detection**: AABB-based clash detection between model pairs
- **Clash Resolution**: Severity classification, assignment, and resolution workflow
- **Model Summary**: Element counts by type, level, material, discipline
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
        "views/bim-models.vue",
        "views/bim-viewer.vue",
        "views/clash-tests.vue",
        "views/clash-results.vue",
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
            "name": "BIM",
            "path": "/agcm/bim",
            "parent": "agcm",
            "icon": "lucide:box",
            "sequence": 46,
            "children": [
                {
                    "name": "3D Models",
                    "path": "/agcm/bim/models",
                    "icon": "lucide:boxes",
                    "sequence": 1,
                    "viewName": "bim-models",
                },
                {
                    "name": "Clash Detection",
                    "path": "/agcm/bim/clash-tests",
                    "icon": "lucide:git-compare",
                    "sequence": 2,
                    "viewName": "clash-tests",
                },
            ],
        },
        {
            "name": "BIM Viewer",
            "path": "/agcm/bim/viewer",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "bim-viewer",
            "sequence": 121,
        },
        {
            "name": "Clash Results",
            "path": "/agcm/bim/clash-results",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "clash-results",
            "sequence": 122,
        },
    ],

    "permissions": [
        "agcm_bim.model.view",
        "agcm_bim.model.create",
        "agcm_bim.model.edit",
        "agcm_bim.model.delete",
        "agcm_bim.clash.view",
        "agcm_bim.clash.create",
        "agcm_bim.clash.run",
        "agcm_bim.clash.resolve",
    ],

    "access_rights": [
        {
            "name": "agcm_bim.manager",
            "model": "agcm_bim.agcm_bim_models",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_bim.user",
            "model": "agcm_bim.agcm_bim_models",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
        {
            "name": "agcm_bim.clash.manager",
            "model": "agcm_bim.agcm_clash_tests",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_bim.clash.user",
            "model": "agcm_bim.agcm_clash_tests",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
