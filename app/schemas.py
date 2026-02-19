from pydantic import BaseModel, Field as PyField, ConfigDict # Rename Field here
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
# Import your models normally
from .models import User, ScheduledTask

class CropTypeEnum(str, Enum):
    coconut = "coconut"
    corn = "corn"
    rice = "rice"

class OperationTypeEnum(str, Enum):
    land_preparation = "land_preparation"
    planting = "planting"
    fertilization = "fertilization"
    irrigation = "irrigation"
    pest_control = "pest_control"
    harvesting = "harvesting"

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    farm_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Farm Schemas ---
class FarmBase(BaseModel):
    name: str
    area_hectares: Optional[float] = None
    soil_type: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None

class FarmCreate(FarmBase):
    pass

class Farm(FarmBase):
    id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Field Schemas ---
class FieldBase(BaseModel):
    name: str
    area_hectares: float
    crop_type: CropTypeEnum
    planting_date: Optional[datetime] = None

class FieldCreate(FieldBase):
    farm_id: int

class Field(FieldBase):
    id: int
    farm_id: int
    current_stage: str
    expected_harvest_date: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Inventory Schemas ---
class InventoryBase(BaseModel):
    item_name: str
    category: str
    quantity: float
    unit: str
    unit_cost: float

class InventoryCreate(InventoryBase):
    farm_id: int

class Inventory(InventoryBase):
    id: int
    farm_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Financial Record Schemas ---
class FinancialRecordBase(BaseModel):
    transaction_type: str
    category: str
    amount: float
    description: Optional[str] = None
    field_id: Optional[int] = None

class FinancialRecordCreate(FinancialRecordBase):
    pass

class FinancialRecord(FinancialRecordBase):
    id: int
    owner_id: int
    date: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Scheduled Task Schemas ---
class ScheduledTaskBase(BaseModel):    
    task_type: str
    task_name: str
    description: Optional[str] = None
    scheduled_date: datetime
    estimated_cost: float
    requires_dry_weather: bool = True
    priority: int = PyField(default=1, ge=1, le=5) 
    status: Optional[str] = None  # Crucial for changing "pending" to "completed"
    actual_cost: Optional[float] = None
    field_id: int

    model_config = ConfigDict(from_attributes=True)

class ScheduledTaskCreate(ScheduledTaskBase):
    pass # Removed field_id here because it's already in the Base

class ScheduledTask(ScheduledTaskBase):
    id: int
    user_id: int
    status: str
    actual_cost: Optional[float] = None
    decision_tree_recommendation: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

    # --- Add this to app/schemas.py ---

class ScheduledTaskUpdate(BaseModel):
    task_type: Optional[str] = None
    task_name: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    requires_dry_weather: Optional[bool] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    actual_cost: Optional[float] = None
    field_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

# --- Weather Data Schemas ---
class WeatherDataBase(BaseModel):
    location_lat: float
    location_lon: float
    date: datetime

class WeatherForecastRequest(BaseModel):
    # Ensure there is a COLON (:) and an EQUALS (=)
    latitude: float = PyField(..., ge=-90, le=90)
    longitude: float = PyField(..., ge=-180, le=180)
    days: int = PyField(default=7, ge=1, le=14) # Open-Meteo free tier limit

class WeatherForecastResponse(BaseModel):
    latitude: float
    longitude: float
    hourly_data: List[Dict[str, Any]]
    daily_data: List[Dict[str, Any]]
    retrieved_at: datetime

# --- Decision Tree Schemas ---
class DecisionTreeRequest(BaseModel):
    field_id: int
    operation_type: OperationTypeEnum
    budget_constraint: Optional[float] = None

class DecisionTreeResponse(BaseModel):
    recommended_date: datetime
    confidence_score: float
    estimated_cost: float
    weather_risk: str
    net_financial_return: Optional[float] = None
    recommendation_reason: str

# --- Optimization Request/Response ---
class OptimizationRequest(BaseModel):
    field_id: int
    operation_type: OperationTypeEnum
    current_budget: float

class OptimizationResponse(BaseModel):
    optimal_date: datetime
    predicted_yield_value: float
    total_projected_cost: float
    net_financial_return: float
    weather_conditions: Dict[str, Any]
    budget_constraint_satisfied: bool
    recommendation: str

# --- Partial Budgeting Schemas ---
class PartialBudgetingInput(BaseModel):
    added_returns: float = 0
    reduced_costs: float = 0
    added_costs: float = 0
    reduced_returns: float = 0

class PartialBudgetingResponse(BaseModel):
    net_benefit: float
    is_profitable: bool
    recommendation: str

# --- Token and Authentication ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None