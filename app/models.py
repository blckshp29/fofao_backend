from app.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum


class CropType(str, enum.Enum):
    COCONUT = "coconut"
    CORN = "corn"
    RICE = "rice"

class OperationType(str, enum.Enum):
    LAND_PREPARATION = "land_preparation"
    PLANTING = "planting"
    FERTILIZATION = "fertilization"
    IRRIGATION = "irrigation"
    PEST_CONTROL = "pest_control"
    HARVESTING = "harvesting"
 
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    farm_name = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    farms = relationship("Farm", back_populates="owner")
    
    # FIX: foreign_keys must be INSIDE the relationship function
    financial_records = relationship(
        "FinancialRecord", 
        back_populates="owner",
        foreign_keys="FinancialRecord.owner_id"
    )
    
    # FIX: Corrected the typo "SchficeduledTask" to "ScheduledTask"
    scheduled_tasks = relationship("ScheduledTask", back_populates="user")

class Farm(Base):
    __tablename__ = "farms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    area_hectares = Column(Float)
    soil_type = Column(String)
    location_lat = Column(Float)
    location_lon = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="farms")
    fields = relationship("Field", back_populates="farm")
    inventory = relationship("Inventory", back_populates="farm") 

class Field(Base):
    __tablename__ = "fields"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    area_hectares = Column(Float)
    crop_type = Column(Enum(CropType))
    planting_date = Column(DateTime)
    expected_harvest_date = Column(DateTime)
    current_stage = Column(String, default="land_preparation")
    farm_id = Column(Integer, ForeignKey("farms.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    farm = relationship("Farm", back_populates="fields")
    scheduled_tasks = relationship("ScheduledTask", back_populates="field")

class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    category = Column(String)  # seeds, fertilizer, equipment, etc.
    quantity = Column(Float)
    unit = Column(String)  # kg, liters, pieces, etc.
    unit_cost = Column(Float)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    farm = relationship("Farm", back_populates="inventory")

class FinancialRecord(Base):
    __tablename__ = "financial_records"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String, nullable=False)  # income or expense
    category = Column(String)  # labor, fertilizer, seeds, harvest_sale, etc.
    amount = Column(Float, nullable=False)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    field_id = Column(Integer, ForeignKey("fields.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    
    # Relationships
    owner = relationship("User", back_populates="financial_records",
                          foreign_keys=[owner_id])
    field = relationship("Field")

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(Enum(OperationType), nullable=False)
    task_name = Column(String, nullable=False)
    description = Column(Text)
    scheduled_date = Column(DateTime, nullable=False)
    estimated_cost = Column(Float)
    actual_cost = Column(Float, nullable=True)
    status = Column(String, default="pending")  # pending, completed, cancelled, rescheduled
    requires_dry_weather = Column(Boolean, default=False)
    priority = Column(Integer, default=1)  # 1-5 scale
    user_id = Column(Integer, ForeignKey("users.id"))
    field_id = Column(Integer, ForeignKey("fields.id"))
    decision_tree_recommendation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="scheduled_tasks")
    field = relationship("Field", back_populates="scheduled_tasks")

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    location_lat = Column(Float, nullable=False)
    location_lon = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    temperature_2m = Column(Float)
    relative_humidity_2m = Column(Float)
    precipitation = Column(Float)
    rain = Column(Float)
    snowfall = Column(Float)
    soil_moisture_0_1cm = Column(Float)
    soil_moisture_1_3cm = Column(Float)
    soil_moisture_3_9cm = Column(Float)
    soil_moisture_9_27cm = Column(Float)
    soil_moisture_27_81cm = Column(Float)
    weather_code = Column(Integer)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

class WeatherCache(Base):
    __tablename__ = "weather_cache"
    id = Column(Integer, primary_key=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    json_data = Column(String)  # We save the API result here as text
    updated_at = Column(DateTime, default=datetime.utcnow)

class DecisionTreeModel(Base):
    __tablename__ = "decision_tree_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    crop_type = Column(Enum(CropType), nullable=False)
    accuracy = Column(Float)
    parameters = Column(Text)  # JSON string of model parameters
    feature_importance = Column(Text)  # JSON string
    trained_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)