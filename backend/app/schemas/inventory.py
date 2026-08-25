"""Pydantic v2 schemas for Inventory API contracts."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from app.models.inventory import ItemCategory


class InventoryCreateRequest(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=200, examples=["Paracetamol 500mg"])
    sku: str | None = Field(None, max_length=100)
    category: ItemCategory = ItemCategory.OTHER
    description: str | None = None
    quantity: float = Field(..., ge=0.0, examples=[500.0])
    unit: str = Field("units", max_length=50)
    unit_value: float = Field(0.0, ge=0.0, description="Value per unit in INR")
    is_perishable: bool = False
    is_hazardous: bool = False
    evacuation_priority: int = Field(3, ge=1, le=5, description="1=highest priority")
    storage_location: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def compute_total_value(self) -> "InventoryCreateRequest":
        # total_value is computed on the model side, but we pre-validate here
        return self

    model_config = {"from_attributes": True}


class InventoryUpdateRequest(BaseModel):
    item_name: str | None = Field(None, min_length=1, max_length=200)
    category: ItemCategory | None = None
    description: str | None = None
    quantity: float | None = Field(None, ge=0.0)
    unit: str | None = None
    unit_value: float | None = Field(None, ge=0.0)
    is_perishable: bool | None = None
    is_hazardous: bool | None = None
    evacuation_priority: int | None = Field(None, ge=1, le=5)
    storage_location: str | None = None

    model_config = {"from_attributes": True}


class InventoryResponse(BaseModel):
    id: int
    business_id: int
    item_name: str
    sku: str | None
    category: ItemCategory
    description: str | None
    quantity: float
    unit: str
    unit_value: float
    total_value: float
    is_perishable: bool
    is_hazardous: bool
    evacuation_priority: int
    storage_location: str | None
    last_audited_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InventoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InventoryResponse]


class StockAdjustRequest(BaseModel):
    """Adjust quantity up or down without a full update."""
    delta: float = Field(..., description="Positive to add, negative to subtract")
    reason: str | None = Field(None, max_length=300)
