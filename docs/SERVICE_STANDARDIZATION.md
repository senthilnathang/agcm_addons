"""
Service Return Type Standardization Guide
=========================================

This document defines the standardized return types for all AGCM services.

## Return Type Patterns

### 1. List Methods
Return paginated results with consistent structure:

```python
def list_items(
    self,
    page: int = 1,
    page_size: int = 20,
    **filters,
) -> dict:
    return {
        "items": List[Model],      # ORM objects for API serialization
        "total": int,              # Total count (without pagination)
        "page": int,               # Current page
        "page_size": int,           # Items per page
        "pages": int,               # Total pages (computed)
    }
```

### 2. Get Methods
Return single record or None:

```python
def get_item(self, item_id: int) -> Optional[Model]:
    """Get single item by ID. Returns None if not found."""
    ...

def get_item_detail(self, item_id: int) -> Optional[dict]:
    """Get item with related data. Returns None if not found."""
    ...
```

### 3. Create Methods
Return created object:

```python
def create_item(self, data: SchemaCreate) -> Model:
    """Create new item. Commits transaction internally."""
    ...

def create_item_with_relations(self, data: SchemaCreate) -> dict:
    """Create item with related data. Returns full detail dict."""
    ...
```

### 4. Update Methods
Return updated object or None:

```python
def update_item(self, item_id: int, data: SchemaUpdate) -> Optional[Model]:
    """Update item. Returns None if not found."""
    ...
```

### 5. Delete Methods
Return boolean:

```python
def delete_item(self, item_id: int) -> bool:
    """Soft delete item. Returns True if deleted, False if not found."""
    ...

def hard_delete_item(self, item_id: int) -> bool:
    """Hard delete item. Returns True if deleted, False if not found."""
    ...
```

### 6. Restore Methods
Return restored object or None:

```python
def restore_item(self, item_id: int) -> Optional[Model]:
    """Restore soft-deleted item. Returns None if not found or not deleted."""
    ...
```

### 7. Action Methods
Return updated object or None:

```python
def close_item(self, item_id: int) -> Optional[Model]:
    """Close/archive item. Returns None if not found."""
    ...

def approve_item(self, item_id: int) -> Optional[Model]:
    """Approve item. Returns None if not found."""
    ...
```

## Implementation Checklist

When standardizing a service:

- [ ] All list methods return `dict` with `items`, `total`, `page`, `page_size`
- [ ] All get methods return `Optional[Model]` (not dict) for single records
- [ ] All get_detail methods return `Optional[dict]` for related data
- [ ] All create methods return `Model` (not dict)
- [ ] All update methods return `Optional[Model]`
- [ ] All delete methods return `bool`
- [ ] All restore methods return `Optional[Model]`
- [ ] Action methods (close, approve, etc.) return `Optional[Model]`
- [ ] Service commits internally (no external transaction management)
- [ ] Service invalidates cache on mutations
- [ ] Service logs activities on mutations
- [ ] Service validates data before commit

## Current Status

### Standardized Services (All Complete):
- [x] agcm/services/project_service.py
- [x] agcm_rfi/services/rfi_service.py
- [x] agcm_schedule/services/schedule_service.py
- [x] agcm_change_order/services/change_order_service.py
- [x] agcm_finance/services/finance_service.py
- [x] agcm_estimate/services/estimate_service.py
- [x] agcm_procurement/services/procurement_service.py
- [x] agcm_document/services/document_service.py
- [x] agcm_safety/services/safety_service.py
- [x] agcm_progress/services/progress_service.py
- [x] agcm_portal/services/portal_service.py
- [x] agcm_reporting/services/reporting_service.py
- [x] agcm_bim/services/bim_service.py

## Frontend Activity Tab Updates

Views with ActivityThread integration:
- [x] agcm/static/views/project-detail.vue
- [x] agcm_rfi/static/views/rfi-detail.vue
- [x] agcm_change_order/static/views/change-order-detail.vue
- [x] agcm_estimate/static/views/estimate-detail.vue
- [x] agcm_procurement/static/views/subcontract-detail.vue
- [x] agcm_procurement/static/views/po-detail.vue
- [x] agcm_submittal/static/views/submittal-detail.vue
- [x] agcm_bim/static/views/bim-model-detail.vue

## Models with ActivityMixin

All key entities have ActivityMixin for audit trail:
- agcm/models/project.py
- agcm_rfi/models/rfi.py
- agcm_schedule/models/task.py
- agcm_change_order/models/change_order.py
- agcm_finance/models/budget.py, expense.py, invoice.py, bill.py
- agcm_estimate/models/estimate.py, proposal.py
- agcm_procurement/models/purchase_order.py, subcontract.py, vendor_bill.py
- agcm_document/models/document.py
- agcm_safety/models/incident.py, punch_list.py
- agcm_progress/models/issue.py, milestone.py, project_image.py, scurve.py, estimation.py
- agcm_bim/models/bim_model.py, bim_viewpoint.py, clash_detection.py
- agcm_portal/models/selection.py, bid.py, portal_config.py
- agcm_submittal/models/submittal.py
"""
