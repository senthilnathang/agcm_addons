"""AG CM BIM Schemas"""

from addons.agcm_bim.schemas.bim import (
    # Model schemas
    BIMModelCreate,
    BIMModelUpdate,
    BIMModelResponse,
    BIMModelDetail,
    # Viewpoint schemas
    BIMViewpointCreate,
    BIMViewpointUpdate,
    BIMViewpointResponse,
    # Clash Test schemas
    ClashTestCreate,
    ClashTestUpdate,
    ClashTestResponse,
    ClashTestDetail,
    # Clash Result schemas
    ClashResultUpdate,
    ClashResultResponse,
    ClashResultResolve,
    ClashResultAssign,
    # Element schemas
    BIMElementResponse,
    BIMModelSummary,
)

__all__ = [
    "BIMModelCreate",
    "BIMModelUpdate",
    "BIMModelResponse",
    "BIMModelDetail",
    "BIMViewpointCreate",
    "BIMViewpointUpdate",
    "BIMViewpointResponse",
    "ClashTestCreate",
    "ClashTestUpdate",
    "ClashTestResponse",
    "ClashTestDetail",
    "ClashResultUpdate",
    "ClashResultResponse",
    "ClashResultResolve",
    "ClashResultAssign",
    "BIMElementResponse",
    "BIMModelSummary",
]
