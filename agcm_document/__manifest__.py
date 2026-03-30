# AG CM Document Management Module
{
    "name": "AG CM Documents",
    "technical_name": "agcm_document",
    "version": "1.0.0",
    "summary": "Project document management with folder hierarchy",
    "description": """
# AG CM Documents

Document management system for construction projects.

## Features

- **Folders**: Hierarchical folder structure per project
- **Documents**: Upload, organize, and track project documents
- **Types**: Blueprint, contract, permit, specification, etc.
- **Status Workflow**: Draft → Under Review → Approved/Rejected → Archived
- **Revisions**: Track document revision numbers
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
        "views/documents.vue",
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
            "name": "Documents",
            "path": "/agcm/documents",
            "parent": "agcm",
            "icon": "lucide:file-text",
            "sequence": 25,
            "viewName": "documents",
        },
    ],

    "permissions": [
        "agcm_document.document.view",
        "agcm_document.document.create",
        "agcm_document.document.edit",
        "agcm_document.document.delete",
        "agcm_document.folder.manage",
    ],

    "access_rights": [
        {
            "name": "agcm_document.manager",
            "model": "agcm_document.agcm_project_documents",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_document.user",
            "model": "agcm_document.agcm_project_documents",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
