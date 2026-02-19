from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import pandas as pd

# Renamed 'Field' to 'FarmField' to avoid conflict with pydantic.Field
from ..models import Field as FarmField, ScheduledTask, WeatherData 
from ..schemas import ScheduledTaskCreate
from ..weather.service import WeatherService
from ..decision_tree.engine import DecisionTreeEngine

class SchedulingService:
    def __init__(self):
        self.weather_service = WeatherService()
        self.decision_tree = DecisionTreeEngine()
    
    def create_scheduled_task(self, db: Session, task_data: ScheduledTaskCreate, user_id: int) -> ScheduledTask:
        """Create a new scheduled task"""
        # In Pydantic V2, use .model_dump() instead of .dict()
        task = ScheduledTask(
            **task_data.model_dump(),
            user_id=user_id,
            status="pending"
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        return task
    
    def generate_optimized_schedule(self, db: Session, field_id: int, user_id: int, 
                                    operations: List[str] = None) -> List[ScheduledTask]:
        """Generate optimized schedule for field operations"""
        # Using the renamed FarmField model here
        field = db.query(FarmField).filter(FarmField.id == field_id).first()
        
        if not field:
            raise Exception(f"Field with id {field_id} not found")
        
        if not operations:
            operations = ["land_preparation", "planting", "fertilization", 
                          "irrigation", "pest_control", "harvesting"]
        
        scheduled_tasks = []
        current_date = field.planting_date if field.planting_date else datetime.now()
        
        crop_params = self.decision_tree.crop_parameters.get(
            field.crop_type, 
            self.decision_tree.crop_parameters["corn"]
        )
        
        # Get weather forecast
        weather_request = {
            "latitude": field.location_lat or 13.0,
            "longitude": field.location_lon or 123.0,
            "days": 180  # 6 months forecast
        }
        
        weather_data = self.weather_service.get_weather_forecast(weather_request)
        
        for operation in operations:
            days_to_add = crop_params["growth_stages"].get(operation, 7)
            proposed_date = current_date + timedelta(days=days_to_add)
            
            weather_suitability = self.weather_service.check_weather_suitability(
                weather_data, proposed_date, requires_dry_weather=True
            )
            
            if not weather_suitability["is_suitable"]:
                start_window = proposed_date - timedelta(days=7)
                end_window = proposed_date + timedelta(days=7)
                
                optimal_windows = self.weather_service.get_optimal_weather_window(
                    weather_data, start_window, end_window, requires_dry_weather=True
                )
                
                if optimal_windows:
                    optimal_window = next(
                        (w for w in optimal_windows if w["is_suitable"]), 
                        optimal_windows[0]
                    )
                    optimal_date = optimal_window["date"]
                else:
                    optimal_date = proposed_date
            else:
                optimal_date = proposed_date
            
            estimated_cost = self.decision_tree._estimate_operation_cost(
                operation, field.area_hectares
            )
            
            task_data = ScheduledTaskCreate(
                task_type=operation,
                task_name=f"{operation.replace('_', ' ').title()} - {field.name}",
                description=f"Automatically scheduled {operation} for {field.crop_type}",
                scheduled_date=optimal_date,
                estimated_cost=estimated_cost,
                requires_dry_weather=True,
                priority=self._calculate_priority(operation),
                field_id=field_id
            )
            
            task = self.create_scheduled_task(db, task_data, user_id)
            task.decision_tree_recommendation = True
            db.commit()
            
            scheduled_tasks.append(task)
            current_date = optimal_date
        
        return scheduled_tasks
    
    def _calculate_priority(self, operation: str) -> int:
        """Calculate priority level for operation"""
        priorities = {
            "land_preparation": 1,
            "planting": 2,
            "fertilization": 3,
            "irrigation": 4,
            "pest_control": 3,
            "harvesting": 1
        }
        return priorities.get(operation, 3)

    # ... (Rest of the methods remain the same, just ensure they use 'FarmField' or 'field')