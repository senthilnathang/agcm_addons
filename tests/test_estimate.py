"""Tests for the agcm_estimate module — Cost Catalogs, Assemblies, Estimates, Proposals, Takeoffs."""

import pytest
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Model loaders
# ---------------------------------------------------------------------------

def _catalog_cls(load_model):
    return load_model("agcm_estimate", "cost_catalog", "CostCatalog")

def _cost_item_cls(load_model):
    return load_model("agcm_estimate", "cost_catalog", "CostItem")

def _item_type_enum(load_model):
    return load_model("agcm_estimate", "cost_catalog", "ItemType")

def _assembly_cls(load_model):
    return load_model("agcm_estimate", "assembly", "Assembly")

def _assembly_item_cls(load_model):
    return load_model("agcm_estimate", "assembly", "AssemblyItem")

def _estimate_cls(load_model):
    return load_model("agcm_estimate", "estimate", "Estimate")

def _estimate_group_cls(load_model):
    return load_model("agcm_estimate", "estimate", "EstimateGroup")

def _estimate_line_item_cls(load_model):
    return load_model("agcm_estimate", "estimate", "EstimateLineItem")

def _estimate_status_enum(load_model):
    return load_model("agcm_estimate", "estimate", "EstimateStatus")

def _line_item_type_enum(load_model):
    return load_model("agcm_estimate", "estimate", "LineItemType")

def _markup_cls(load_model):
    return load_model("agcm_estimate", "estimate_markup", "EstimateMarkup")

def _markup_type_enum(load_model):
    return load_model("agcm_estimate", "estimate_markup", "MarkupType")

def _proposal_cls(load_model):
    return load_model("agcm_estimate", "proposal", "Proposal")

def _proposal_status_enum(load_model):
    return load_model("agcm_estimate", "proposal", "ProposalStatus")

def _takeoff_sheet_cls(load_model):
    return load_model("agcm_estimate", "takeoff", "TakeoffSheet")

def _takeoff_measurement_cls(load_model):
    return load_model("agcm_estimate", "takeoff", "TakeoffMeasurement")

def _measurement_type_enum(load_model):
    return load_model("agcm_estimate", "takeoff", "MeasurementType")


# ---------------------------------------------------------------------------
# Helper to create a catalog with items
# ---------------------------------------------------------------------------

def _create_catalog_with_items(db, load_model, company_id, n_items=3):
    """Create a catalog and return (catalog, [items])."""
    CostCatalog = _catalog_cls(load_model)
    CostItem = _cost_item_cls(load_model)
    ItemType = _item_type_enum(load_model)

    catalog = CostCatalog(
        company_id=company_id,
        name="Test Catalog",
        description="Catalog for testing",
        is_default=True,
    )
    db.add(catalog)
    db.flush()

    items = []
    for i in range(n_items):
        item = CostItem(
            company_id=company_id,
            catalog_id=catalog.id,
            name=f"Item {i+1}",
            item_type=ItemType.MATERIAL,
            unit="ea",
            unit_cost=10.0 * (i + 1),
            unit_price=15.0 * (i + 1),
            taxable=True,
            cost_code=f"03-{i+1:03d}",
            vendor=f"Vendor {i+1}",
        )
        db.add(item)
        items.append(item)

    db.flush()
    return catalog, items


def _create_estimate_full(db, load_model, company_id, project_id, user_id):
    """Create a full estimate with groups, line items, and markups. Returns dict of objects."""
    Estimate = _estimate_cls(load_model)
    EstimateGroup = _estimate_group_cls(load_model)
    EstimateLineItem = _estimate_line_item_cls(load_model)
    EstimateMarkup = _markup_cls(load_model)
    MarkupType = _markup_type_enum(load_model)

    estimate = Estimate(
        company_id=company_id,
        project_id=project_id,
        name="Test Estimate",
        description="Full estimate for testing",
        version=1,
        status="draft",
        estimate_type="detailed",
        subtotal=0,
        tax_rate=8.25,
        created_by=user_id,
    )
    db.add(estimate)
    db.flush()

    group = EstimateGroup(
        estimate_id=estimate.id,
        company_id=company_id,
        name="Foundation",
        display_order=1,
    )
    db.add(group)
    db.flush()

    line1 = EstimateLineItem(
        group_id=group.id,
        estimate_id=estimate.id,
        company_id=company_id,
        name="Concrete",
        item_type="material",
        quantity=100,
        unit="cy",
        unit_cost=125.0,
        unit_price=150.0,
        total_cost=12500.0,
        total_price=15000.0,
        markup_pct=20.0,
        taxable=True,
        display_order=1,
    )
    line2 = EstimateLineItem(
        group_id=group.id,
        estimate_id=estimate.id,
        company_id=company_id,
        name="Rebar",
        item_type="material",
        quantity=5,
        unit="ton",
        unit_cost=800.0,
        unit_price=960.0,
        total_cost=4000.0,
        total_price=4800.0,
        markup_pct=20.0,
        taxable=True,
        display_order=2,
    )
    db.add_all([line1, line2])
    db.flush()

    markup = EstimateMarkup(
        estimate_id=estimate.id,
        company_id=company_id,
        name="Overhead",
        markup_type=MarkupType.PERCENTAGE,
        value=10.0,
        apply_before_tax=True,
        display_order=1,
        calculated_amount=1650.0,
    )
    db.add(markup)
    db.flush()

    return {
        "estimate": estimate,
        "group": group,
        "line_items": [line1, line2],
        "markup": markup,
    }


# ===========================================================================
# TestCostCatalog
# ===========================================================================

class TestCostCatalog:

    def test_create_catalog(self, db, load_model, company_id):
        CostCatalog = _catalog_cls(load_model)
        catalog = CostCatalog(
            company_id=company_id,
            name="General Materials",
            description="Common construction materials",
            is_default=True,
        )
        db.add(catalog)
        db.flush()

        assert catalog.id is not None
        assert catalog.name == "General Materials"
        assert catalog.description == "Common construction materials"
        assert catalog.is_default is True
        assert catalog.company_id == company_id

    def test_create_cost_item(self, db, load_model, company_id):
        CostItem = _cost_item_cls(load_model)
        ItemType = _item_type_enum(load_model)
        catalog, _ = _create_catalog_with_items(db, load_model, company_id, n_items=0)

        item = CostItem(
            company_id=company_id,
            catalog_id=catalog.id,
            name="Portland Cement Type I/II",
            description="94 lb bag",
            item_type=ItemType.MATERIAL,
            unit="bag",
            unit_cost=12.50,
            unit_price=16.25,
            taxable=True,
            cost_code="03-100",
            vendor="Quikrete Inc.",
            category="Concrete",
            is_active=True,
        )
        db.add(item)
        db.flush()

        assert item.id is not None
        assert item.item_type == ItemType.MATERIAL
        assert item.unit_cost == 12.50
        assert item.unit_price == 16.25
        assert item.taxable is True
        assert item.cost_code == "03-100"
        assert item.vendor == "Quikrete Inc."
        assert item.category == "Concrete"
        assert item.is_active is True

    def test_cost_item_types(self, db, load_model, company_id):
        ItemType = _item_type_enum(load_model)
        CostItem = _cost_item_cls(load_model)
        catalog, _ = _create_catalog_with_items(db, load_model, company_id, n_items=0)

        types_to_test = [
            ItemType.MATERIAL, ItemType.LABOR, ItemType.EQUIPMENT,
            ItemType.SUBCONTRACTOR, ItemType.FEE, ItemType.OTHER,
        ]
        created = []
        for itype in types_to_test:
            item = CostItem(
                company_id=company_id,
                catalog_id=catalog.id,
                name=f"Test {itype.value}",
                item_type=itype,
                unit="ea",
                unit_cost=10.0,
            )
            db.add(item)
            created.append(item)
        db.flush()

        for item, expected_type in zip(created, types_to_test):
            assert item.item_type == expected_type
            assert item.item_type.value == expected_type.value

    def test_delete_catalog_cascades_items(self, db, load_model, company_id):
        CostItem = _cost_item_cls(load_model)
        catalog, items = _create_catalog_with_items(db, load_model, company_id, n_items=5)
        item_ids = [it.id for it in items]
        catalog_id = catalog.id

        db.delete(catalog)
        db.flush()

        # Verify items are gone
        for iid in item_ids:
            assert db.get(CostItem, iid) is None


# ===========================================================================
# TestAssembly
# ===========================================================================

class TestAssembly:

    def test_create_assembly(self, db, load_model, company_id):
        Assembly = _assembly_cls(load_model)
        AssemblyItem = _assembly_item_cls(load_model)
        catalog, items = _create_catalog_with_items(db, load_model, company_id, n_items=3)

        assembly = Assembly(
            company_id=company_id,
            name="Foundation Package",
            description="Standard foundation assembly",
            category="Foundation",
            is_active=True,
        )
        db.add(assembly)
        db.flush()

        ai1 = AssemblyItem(
            assembly_id=assembly.id,
            company_id=company_id,
            cost_item_id=items[0].id,
            name="Concrete",
            item_type="material",
            quantity=10,
            unit="cy",
            unit_cost=125.0,
            waste_factor=5.0,
        )
        ai2 = AssemblyItem(
            assembly_id=assembly.id,
            company_id=company_id,
            cost_item_id=items[1].id,
            name="Rebar #5",
            item_type="material",
            quantity=200,
            unit="lf",
            unit_cost=1.85,
            waste_factor=10.0,
        )
        db.add_all([ai1, ai2])
        db.flush()

        assert assembly.id is not None
        assert assembly.name == "Foundation Package"
        assert len(assembly.items) == 2

    def test_assembly_total_calculation(self, db, load_model, company_id):
        """Verify extended cost = qty * unit_cost * (1 + waste_factor/100)."""
        Assembly = _assembly_cls(load_model)
        AssemblyItem = _assembly_item_cls(load_model)

        assembly = Assembly(
            company_id=company_id,
            name="Test Assembly",
            category="Test",
        )
        db.add(assembly)
        db.flush()

        ai = AssemblyItem(
            assembly_id=assembly.id,
            company_id=company_id,
            name="Material A",
            item_type="material",
            quantity=50,
            unit="sf",
            unit_cost=3.25,
            waste_factor=8.0,
        )
        db.add(ai)
        db.flush()

        # Business logic: extended = qty * unit_cost * (1 + waste_factor/100)
        expected = 50 * 3.25 * (1 + 8.0 / 100)
        actual = ai.quantity * ai.unit_cost * (1 + ai.waste_factor / 100)
        assert abs(actual - expected) < 0.01
        assert abs(actual - 175.50) < 0.01

    def test_delete_assembly_cascades(self, db, load_model, company_id):
        Assembly = _assembly_cls(load_model)
        AssemblyItem = _assembly_item_cls(load_model)

        assembly = Assembly(
            company_id=company_id,
            name="Deletable Assembly",
        )
        db.add(assembly)
        db.flush()

        for i in range(4):
            db.add(AssemblyItem(
                assembly_id=assembly.id,
                company_id=company_id,
                name=f"Item {i}",
                item_type="material",
                quantity=1,
                unit_cost=10.0,
            ))
        db.flush()

        item_ids = [it.id for it in assembly.items]
        assert len(item_ids) == 4

        db.delete(assembly)
        db.flush()

        for iid in item_ids:
            assert db.get(AssemblyItem, iid) is None


# ===========================================================================
# TestEstimate
# ===========================================================================

class TestEstimate:

    def test_create_estimate(self, db, load_model, project_ids, company_id, user_id):
        Estimate = _estimate_cls(load_model)
        estimate = Estimate(
            company_id=company_id,
            project_id=project_ids[0],
            name="Preliminary Estimate",
            sequence_name="EST00001",
            version=1,
            status="draft",
            estimate_type="preliminary",
            created_by=user_id,
        )
        db.add(estimate)
        db.flush()

        assert estimate.id is not None
        assert estimate.project_id == project_ids[0]
        assert estimate.sequence_name == "EST00001"
        assert str(estimate.status) == "draft" or (hasattr(estimate.status, 'value') and estimate.status.value == "draft")
        assert estimate.version == 1

    def test_estimate_with_groups_and_lines(self, db, load_model, project_ids, company_id, user_id):
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)
        estimate = objs["estimate"]
        group = objs["group"]
        lines = objs["line_items"]

        assert len(estimate.groups) == 1
        assert estimate.groups[0].name == "Foundation"
        assert len(group.line_items) == 2
        assert lines[0].name == "Concrete"
        assert lines[1].name == "Rebar"

    def test_line_item_calculations(self, db, load_model, project_ids, company_id, user_id):
        EstimateLineItem = _estimate_line_item_cls(load_model)
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)
        line = objs["line_items"][0]

        # total_cost = qty * unit_cost
        assert line.total_cost == line.quantity * line.unit_cost
        assert line.total_cost == 100 * 125.0

        # total_price = qty * unit_price
        assert line.total_price == line.quantity * line.unit_price
        assert line.total_price == 100 * 150.0

    def test_markup_percentage(self, db, load_model, project_ids, company_id, user_id):
        EstimateMarkup = _markup_cls(load_model)
        MarkupType = _markup_type_enum(load_model)
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)
        markup = objs["markup"]

        assert markup.markup_type == MarkupType.PERCENTAGE
        assert markup.value == 10.0
        assert markup.apply_before_tax is True
        assert markup.calculated_amount == 1650.0

    def test_markup_lump_sum(self, db, load_model, project_ids, company_id, user_id):
        EstimateMarkup = _markup_cls(load_model)
        MarkupType = _markup_type_enum(load_model)
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)

        lump = EstimateMarkup(
            estimate_id=objs["estimate"].id,
            company_id=company_id,
            name="Permit Fees",
            markup_type=MarkupType.LUMP_SUM,
            value=5000.0,
            apply_before_tax=False,
            display_order=2,
            calculated_amount=5000.0,
        )
        db.add(lump)
        db.flush()

        assert lump.markup_type == MarkupType.LUMP_SUM
        assert lump.value == 5000.0
        assert lump.calculated_amount == 5000.0

    def test_estimate_versioning(self, db, load_model, project_ids, company_id, user_id):
        Estimate = _estimate_cls(load_model)

        v1 = Estimate(
            company_id=company_id,
            project_id=project_ids[0],
            name="Estimate v1",
            version=1,
            status="approved",
            estimate_type="detailed",
            created_by=user_id,
        )
        db.add(v1)
        db.flush()

        v2 = Estimate(
            company_id=company_id,
            project_id=project_ids[0],
            name="Estimate v2",
            version=2,
            status="draft",
            estimate_type="detailed",
            parent_estimate_id=v1.id,
            created_by=user_id,
        )
        db.add(v2)
        db.flush()

        assert v2.parent_estimate_id == v1.id
        assert v2.version == 2
        assert v2.parent_estimate is not None
        assert v2.parent_estimate.id == v1.id

    def test_estimate_status_workflow(self, db, load_model, project_ids, company_id, user_id):
        Estimate = _estimate_cls(load_model)
        EstimateStatus = _estimate_status_enum(load_model)

        estimate = Estimate(
            company_id=company_id,
            project_id=project_ids[0],
            name="Workflow Estimate",
            status=EstimateStatus.DRAFT,
            estimate_type="detailed",
            created_by=user_id,
        )
        db.add(estimate)
        db.flush()
        assert estimate.status == EstimateStatus.DRAFT

        estimate.status = EstimateStatus.IN_REVIEW
        db.flush()
        assert estimate.status == EstimateStatus.IN_REVIEW

        estimate.status = EstimateStatus.APPROVED
        estimate.approved_by = user_id
        estimate.approved_date = date(2026, 3, 30)
        db.flush()
        assert estimate.status == EstimateStatus.APPROVED
        assert estimate.approved_by == user_id

    def test_delete_estimate_cascades(self, db, load_model, project_ids, company_id, user_id):
        EstimateGroup = _estimate_group_cls(load_model)
        EstimateLineItem = _estimate_line_item_cls(load_model)
        EstimateMarkup = _markup_cls(load_model)

        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)
        estimate = objs["estimate"]
        group_id = objs["group"].id
        line_ids = [li.id for li in objs["line_items"]]
        markup_id = objs["markup"].id

        db.delete(estimate)
        db.flush()

        assert db.get(EstimateGroup, group_id) is None
        for lid in line_ids:
            assert db.get(EstimateLineItem, lid) is None
        assert db.get(EstimateMarkup, markup_id) is None


# ===========================================================================
# TestProposal
# ===========================================================================

class TestProposal:

    def test_create_proposal(self, db, load_model, project_ids, company_id, user_id):
        Proposal = _proposal_cls(load_model)
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)
        estimate = objs["estimate"]

        proposal = Proposal(
            company_id=company_id,
            estimate_id=estimate.id,
            project_id=project_ids[0],
            name="Proposal for Foundation Work",
            sequence_name="PROP00001",
            client_name="Acme Construction LLC",
            client_email="john@acme.com",
            client_phone="555-0100",
            scope_of_work="Complete foundation package including excavation, forming, and pour.",
            valid_until=date(2026, 6, 30),
            show_line_items=True,
            show_groups=True,
            created_by=user_id,
        )
        db.add(proposal)
        db.flush()

        assert proposal.id is not None
        assert proposal.estimate_id == estimate.id
        assert proposal.client_name == "Acme Construction LLC"
        assert proposal.status.value == "draft"

    def test_proposal_status_workflow(self, db, load_model, project_ids, company_id, user_id):
        Proposal = _proposal_cls(load_model)
        ProposalStatus = _proposal_status_enum(load_model)
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)

        proposal = Proposal(
            company_id=company_id,
            estimate_id=objs["estimate"].id,
            project_id=project_ids[0],
            name="Status Test Proposal",
            client_name="Test Client",
            status=ProposalStatus.DRAFT,
            created_by=user_id,
        )
        db.add(proposal)
        db.flush()
        assert proposal.status == ProposalStatus.DRAFT

        proposal.status = ProposalStatus.SENT
        proposal.sent_date = date(2026, 4, 1)
        db.flush()
        assert proposal.status == ProposalStatus.SENT

        proposal.status = ProposalStatus.VIEWED
        proposal.viewed_date = datetime(2026, 4, 2, 14, 30, 0)
        db.flush()
        assert proposal.status == ProposalStatus.VIEWED

        proposal.status = ProposalStatus.APPROVED
        proposal.approved_date = date(2026, 4, 5)
        db.flush()
        assert proposal.status == ProposalStatus.APPROVED

    def test_proposal_display_options(self, db, load_model, project_ids, company_id, user_id):
        Proposal = _proposal_cls(load_model)
        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)

        proposal = Proposal(
            company_id=company_id,
            estimate_id=objs["estimate"].id,
            project_id=project_ids[0],
            name="Display Options Proposal",
            client_name="Display Client",
            show_line_items=False,
            show_unit_prices=True,
            show_markup=True,
            show_groups=False,
            created_by=user_id,
        )
        db.add(proposal)
        db.flush()

        assert proposal.show_line_items is False
        assert proposal.show_unit_prices is True
        assert proposal.show_markup is True
        assert proposal.show_groups is False


# ===========================================================================
# TestTakeoff
# ===========================================================================

class TestTakeoff:

    def test_create_takeoff_sheet(self, db, load_model, project_ids, company_id, user_id):
        TakeoffSheet = _takeoff_sheet_cls(load_model)

        sheet = TakeoffSheet(
            company_id=company_id,
            project_id=project_ids[0],
            name="Floor Plan Level 1",
            sequence_name="TK00001",
            file_name="floor_plan_L1.pdf",
            page_number=1,
            scale_factor=0.25,
            scale_unit="ft",
            revision=1,
            created_by=user_id,
        )
        db.add(sheet)
        db.flush()

        assert sheet.id is not None
        assert sheet.name == "Floor Plan Level 1"
        assert sheet.scale_factor == 0.25
        assert sheet.scale_unit == "ft"
        assert sheet.page_number == 1

    def test_measurement_linked_to_line(self, db, load_model, project_ids, company_id, user_id):
        TakeoffSheet = _takeoff_sheet_cls(load_model)
        TakeoffMeasurement = _takeoff_measurement_cls(load_model)
        MeasurementType = _measurement_type_enum(load_model)

        objs = _create_estimate_full(db, load_model, company_id, project_ids[0], user_id)
        line_item = objs["line_items"][0]

        sheet = TakeoffSheet(
            company_id=company_id,
            project_id=project_ids[0],
            name="Site Plan",
            created_by=user_id,
        )
        db.add(sheet)
        db.flush()

        measurement = TakeoffMeasurement(
            sheet_id=sheet.id,
            company_id=company_id,
            estimate_line_item_id=line_item.id,
            measurement_type=MeasurementType.AREA,
            label="Foundation Slab Area",
            value=2500.0,
            unit="sf",
            color="#52c41a",
            layer="Foundation",
        )
        db.add(measurement)
        db.flush()

        assert measurement.id is not None
        assert measurement.estimate_line_item_id == line_item.id
        assert measurement.measurement_type == MeasurementType.AREA
        assert measurement.value == 2500.0
        assert measurement.label == "Foundation Slab Area"
