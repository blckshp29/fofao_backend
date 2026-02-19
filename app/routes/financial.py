from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from .. import models, schemas
from ..database import get_db
from ..models import FinancialRecord, User, Field as FieldModel
from ..schemas import FinancialRecordCreate, FinancialRecord as FinancialRecordSchema
from ..financial.partial_budgeting import PartialBudgeting
from ..schemas import PartialBudgetingInput, PartialBudgetingResponse
from .auth import get_current_user

router = APIRouter()
partial_budgeting = PartialBudgeting()

@router.post("/financial/records", response_model=FinancialRecordSchema)
def create_financial_record(
    record: FinancialRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_record = FinancialRecord(**record.dict(), owner_id=current_user.id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/financial/records", response_model=List[FinancialRecordSchema])
def get_financial_records(
    start_date: datetime = None,
    end_date: datetime = None,
    category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(FinancialRecord).filter(FinancialRecord.owner_id == current_user.id)
    
    if start_date:
        query = query.filter(FinancialRecord.date >= start_date)
    if end_date:
        query = query.filter(FinancialRecord.date <= end_date)
    if category:
        query = query.filter(FinancialRecord.category == category)
    
    records = query.order_by(FinancialRecord.date.desc()).all()
    return records

@router.get("/financial/summary")
def get_financial_summary(
    start_date: datetime = None,
    end_date: datetime = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    records = db.query(FinancialRecord).filter(
        FinancialRecord.owner_id == current_user.id,
        FinancialRecord.date >= start_date,
        FinancialRecord.date <= end_date
    ).all()

    # DEBUG PRINT: Check your terminal! 
    # This will tell us if the query found anything at all.
    print(f"DEBUG: Found {len(records)} records for user {current_user.id} in this date range.")

    total_income = 0
    total_expenses = 0
    categories = {}

    for r in records:
        # Normalize to UPPERCASE to avoid "income" vs "INCOME" errors
        t_type = r.transaction_type.upper() if r.transaction_type else ""
        
        if t_type == "INCOME":
            total_income += r.amount
        elif t_type == "EXPENSE":
            total_expenses += r.amount

        # Category logic
        if r.category not in categories:
            categories[r.category] = {"INCOME": 0, "EXPENSE": 0}
        categories[r.category][t_type if t_type in ["INCOME", "EXPENSE"] else "EXPENSE"] += r.amount
    
    net_profit = total_income - total_expenses
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": (net_profit / total_income * 100) if total_income > 0 else 0,
        "category_breakdown": categories
    }

@router.post("/financial/partial-budgeting", response_model=PartialBudgetingResponse)
def calculate_partial_budgeting(
    input_data: PartialBudgetingInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return partial_budgeting.calculate_net_benefit(input_data)

@router.get("/financial/net-financial-return/{field_id}")
def calculate_net_financial_return(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from ..decision_tree.engine import DecisionTreeEngine
    
    decision_tree = DecisionTreeEngine()
    
    # Get field
    field = db.query(FieldModel).filter(
        FieldModel.id == field_id,
        FieldModel.owner_id == current_user.id
    ).first()
    
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    
    # Get financial records for this field
    financial_records = db.query(FinancialRecord).filter(
        FinancialRecord.field_id == field_id
    ).all()
    
    total_costs = sum(r.amount for r in financial_records if r.transaction_type == "expense")
    
    # Estimate yield value (simplified)
    base_yields = {
        "coconut": 50000,
        "corn": 30000,
        "rice": 40000  
    }
    
    base_yield = base_yields.get(field.crop_type.value, 20000)
    predicted_yield_value = base_yield * field.area_hectares
    
    net_financial_return = decision_tree.calculate_net_financial_return(
        predicted_yield_value, total_costs
    )
    
    return {
        "field_id": field_id,
        "crop_type": field.crop_type.value,
        "area_hectares": field.area_hectares,
        "predicted_yield_value": predicted_yield_value,
        "total_costs": total_costs,
        "net_financial_return": net_financial_return,
        "roi": (net_financial_return / total_costs * 100) if total_costs > 0 else 0
    }

# Use .put for full updates or .patch for partial updates
@router.put("/financial/records/{record_id}", response_model=schemas.FinancialRecord)
def update_record(
    record_id: int, 
    updated_data: schemas.FinancialRecordCreate, # The new data from Postman
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Find the record
    query = db.query(models.FinancialRecord).filter(models.FinancialRecord.id == record_id)
    db_record = query.first()

    # 2. Check if it exists
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 3. Security Check: Does this record belong to the logged-in user?
    if db_record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this record")

    # 4. Update the fields
    query.update(updated_data.model_dump(), synchronize_session=False)
    db.commit()
    
    return query.first()

@router.delete("/financial/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.FinancialRecord).filter(models.FinancialRecord.id == record_id)
    db_record = query.first()

    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if db_record.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    query.delete(synchronize_session=False)
    db.commit()
    return None # 204 No Content doesn't return a body