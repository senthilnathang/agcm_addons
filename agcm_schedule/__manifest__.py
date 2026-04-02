# AGCM Schedule - Construction Project Scheduling Module
{
    "name": "AGCM Schedule",
    "technical_name": "agcm_schedule",
    "version": "1.0.0",
    "summary": "Construction project scheduling with tasks, WBS, and dependencies",
    "description": """
# AGCM Schedule

Project scheduling system for construction management.

## Features

- **Schedules**: Baseline, revised, and current schedule versions per project
- **WBS**: Hierarchical work breakdown structure
- **Tasks**: Task management with types, statuses, progress tracking
- **Dependencies**: Task dependency relationships (FS, SS, FF, SF)
- **Gantt Chart**: Visual timeline with progress bars and dependency arrows
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
        "views/task-schedule.vue",
        "views/schedules.vue",
        "views/task-form.vue",
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
            "name": "Schedule",
            "path": "/agcm/schedule",
            "icon": "lucide:gantt-chart",
            "sequence": 38,
            "children": [
                {
                    "name": "Task Schedule",
                    "path": "/agcm/schedule/task-schedule",
                    "icon": "lucide:gantt-chart",
                    "sequence": 1,
                    "viewName": "task-schedule",
                },
            ],
        },
        {
            "name": "Task Form",
            "path": "/agcm/schedule/tasks/form",
            "parent": "/agcm/schedule",
            "hideInMenu": True,
            "viewName": "task-form",
            "sequence": 107,
        },
    ],
    "permissions": [
        "agcm_schedule.schedule.view",
        "agcm_schedule.schedule.create",
        "agcm_schedule.schedule.edit",
        "agcm_schedule.schedule.delete",
        "agcm_schedule.task.view",
        "agcm_schedule.task.create",
        "agcm_schedule.task.edit",
        "agcm_schedule.task.delete",
    ],
    "access_rights": [
        {
            "name": "agcm_schedule.manager",
            "model": "agcm_schedule.agcm_schedules",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_schedule.user",
            "model": "agcm_schedule.agcm_schedules",
            "permissions": {
                "read": True,
                "write": False,
                "create": False,
                "delete": False,
            },
            "groups": ["base.group_user"],
        },
        {
            "name": "agcm_schedule.task.manager",
            "model": "agcm_schedule.agcm_tasks",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_schedule.task.user",
            "model": "agcm_schedule.agcm_tasks",
            "permissions": {
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
            },
            "groups": ["base.group_user"],
        },
    ],
}
