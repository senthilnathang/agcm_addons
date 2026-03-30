# AG CM Finance - Construction Financial Management Module
{
    "name": "AG CM Finance",
    "technical_name": "agcm_finance",
    "version": "1.0.0",
    "summary": "Financial management for construction projects",
    "description": """
# AG CM Finance

Financial management for construction projects.

## Features

- **Cost Codes**: Hierarchical cost code structure per project
- **Budgets**: Budget planning with planned, actual, and committed amounts
- **Expenses**: Project expense tracking with line items
- **Invoices**: Customer invoice management with payment tracking
- **Bills**: Vendor bill management with payment tracking
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
        "views/cost-codes.vue",
        "views/budget.vue",
        "views/expenses.vue",
        "views/expense-form.vue",
        "views/invoices.vue",
        "views/invoice-form.vue",
        "views/bills.vue",
        "views/bill-form.vue",
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
            "name": "Finance",
            "path": "/agcm/finance",
            "parent": "agcm",
            "icon": "lucide:wallet",
            "sequence": 40,
            "children": [
                {
                    "name": "Budget",
                    "path": "/agcm/finance/budget",
                    "icon": "lucide:calculator",
                    "sequence": 1,
                    "viewName": "budget",
                },
                {
                    "name": "Cost Codes",
                    "path": "/agcm/finance/cost-codes",
                    "icon": "lucide:list-tree",
                    "sequence": 2,
                    "viewName": "cost-codes",
                },
                {
                    "name": "Expenses",
                    "path": "/agcm/finance/expenses",
                    "icon": "lucide:receipt",
                    "sequence": 3,
                    "viewName": "expenses",
                },
                {
                    "name": "Invoices",
                    "path": "/agcm/finance/invoices",
                    "icon": "lucide:file-text",
                    "sequence": 4,
                    "viewName": "invoices",
                },
                {
                    "name": "Bills",
                    "path": "/agcm/finance/bills",
                    "icon": "lucide:file-minus",
                    "sequence": 5,
                    "viewName": "bills",
                },
            ],
        },
        {
            "name": "Expense Form",
            "path": "/agcm/finance/expenses/form",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "expense-form",
            "sequence": 140,
        },
        {
            "name": "Invoice Form",
            "path": "/agcm/finance/invoices/form",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "invoice-form",
            "sequence": 141,
        },
        {
            "name": "Bill Form",
            "path": "/agcm/finance/bills/form",
            "parent": "agcm",
            "hideInMenu": True,
            "viewName": "bill-form",
            "sequence": 142,
        },
    ],

    "permissions": [
        "agcm_finance.budget.view",
        "agcm_finance.budget.create",
        "agcm_finance.budget.edit",
        "agcm_finance.budget.delete",
        "agcm_finance.expense.view",
        "agcm_finance.expense.create",
        "agcm_finance.expense.edit",
        "agcm_finance.expense.delete",
        "agcm_finance.invoice.view",
        "agcm_finance.invoice.create",
        "agcm_finance.invoice.edit",
        "agcm_finance.invoice.delete",
        "agcm_finance.bill.view",
        "agcm_finance.bill.create",
        "agcm_finance.bill.edit",
        "agcm_finance.bill.delete",
    ],

    "access_rights": [
        {
            "name": "agcm_finance.manager",
            "model": "agcm_finance.agcm_budgets",
            "permissions": {"read": True, "write": True, "create": True, "delete": True},
            "groups": ["base.group_manager"],
        },
        {
            "name": "agcm_finance.user",
            "model": "agcm_finance.agcm_budgets",
            "permissions": {"read": True, "write": True, "create": True, "delete": False},
            "groups": ["base.group_user"],
        },
    ],
}
