"""Seed Phase 9 Users (Admin and Farmers) and isolated test farms."""

import os
import sys
import uuid
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models.tenant import User, UserRole
from app.models.farm import Farm, Field
from app.models.survey import Survey


def seed_phase9():
    db = SessionLocal()
    try:
        print("--- Seeding Phase 9 Users & Farms ---")

        # 1. Update/Create Admin
        admin = db.query(User).filter(User.email == "admin@agridrone.local").first()
        admin_pass_hash = get_password_hash("Admin@AgriDrone2026!")
        if not admin:
            admin = User(
                email="admin@agridrone.local",
                password_hash=admin_pass_hash,
                full_name="Platform Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            print("Created admin@agridrone.local")
        else:
            admin.password_hash = admin_pass_hash
            admin.role = UserRole.ADMIN
            admin.is_active = True
            print("Updated admin@agridrone.local password hash")

        # 2. Update/Create Farmer 1 (Green Valley)
        farmer1 = db.query(User).filter(User.email == "farmer@greenvalley.local").first()
        farmer1_pass_hash = get_password_hash("Farmer@AgriDrone2026!")
        if not farmer1:
            farmer1 = User(
                email="farmer@greenvalley.local",
                password_hash=farmer1_pass_hash,
                full_name="John Doe (Green Valley)",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer1)
            print("Created farmer@greenvalley.local")
        else:
            farmer1.password_hash = farmer1_pass_hash
            farmer1.role = UserRole.FARMER
            farmer1.is_active = True
            print("Updated farmer@greenvalley.local password hash")

        # 3. Update/Create Farmer 2 (Sunrise Orchards)
        farmer2 = db.query(User).filter(User.email == "farmer2@sunrise.local").first()
        farmer2_pass_hash = get_password_hash("Farmer2@AgriDrone2026!")
        if not farmer2:
            farmer2 = User(
                email="farmer2@sunrise.local",
                password_hash=farmer2_pass_hash,
                full_name="Jane Smith (Sunrise Orchards)",
                role=UserRole.FARMER,
                is_active=True,
            )
            db.add(farmer2)
            print("Created farmer2@sunrise.local")
        else:
            farmer2.password_hash = farmer2_pass_hash
            farmer2.role = UserRole.FARMER
            farmer2.is_active = True
            print("Updated farmer2@sunrise.local password hash")

        db.commit()
        db.refresh(admin)
        db.refresh(farmer1)
        db.refresh(farmer2)

        # 4. Check farms and assign ownership
        all_farms = db.query(Farm).order_by(Farm.created_at.asc()).all()
        if all_farms:
            # Assign first farm to Farmer 1
            all_farms[0].owner_id = farmer1.id
            print(f"Assigned farm '{all_farms[0].name}' to Farmer 1 ({farmer1.email})")

            # If there's a second farm, assign to Farmer 2
            if len(all_farms) > 1:
                all_farms[1].owner_id = farmer2.id
                print(f"Assigned farm '{all_farms[1].name}' to Farmer 2 ({farmer2.email})")
            else:
                # Create a second farm for Farmer 2 to enable rigorous IDOR isolation tests
                farm2 = Farm(
                    name="Sunrise Organic Orchards",
                    owner_id=farmer2.id,
                    total_area_hectares=45.0,
                    contact_phone="+1-555-0199",
                )
                db.add(farm2)
                db.commit()
                db.refresh(farm2)

                field2 = Field(
                    farm_id=farm2.id,
                    field_name="East Block Apples",
                    crop_type="Apples",
                    area_hectares=18.5,
                )
                db.add(field2)
                db.commit()
                db.refresh(field2)

                survey2 = Survey(
                    field_id=field2.id,
                    survey_code="SURV-SUNRISE-001",
                    flight_date=datetime.utcnow(),
                    status="COMPLETED",
                )
                db.add(survey2)
                db.commit()
                print(f"Created isolated Farm 2 '{farm2.name}' and assigned to Farmer 2 ({farmer2.email})")
        else:
            # Create Farm 1 for Farmer 1
            farm1 = Farm(
                name="Green Valley Wheat Estate",
                owner_id=farmer1.id,
                total_area_hectares=120.0,
                contact_phone="+1-555-0100",
            )
            db.add(farm1)
            db.commit()
            db.refresh(farm1)

            field1 = Field(
                farm_id=farm1.id,
                field_name="North Pivot Corn",
                crop_type="Corn",
                area_hectares=35.0,
            )
            db.add(field1)
            db.commit()
            db.refresh(field1)

            survey1 = Survey(
                field_id=field1.id,
                survey_code="SURV-GV-001",
                flight_date=datetime.utcnow(),
                status="COMPLETED",
            )
            db.add(survey1)

            # Create Farm 2 for Farmer 2
            farm2 = Farm(
                name="Sunrise Organic Orchards",
                owner_id=farmer2.id,
                total_area_hectares=45.0,
                contact_phone="+1-555-0199",
            )
            db.add(farm2)
            db.commit()
            db.refresh(farm2)

            field2 = Field(
                farm_id=farm2.id,
                field_name="East Block Apples",
                crop_type="Apples",
                area_hectares=18.5,
            )
            db.add(field2)
            db.commit()
            db.refresh(field2)

            survey2 = Survey(
                field_id=field2.id,
                survey_code="SURV-SUNRISE-001",
                flight_date=datetime.utcnow(),
                status="COMPLETED",
            )
            db.add(survey2)
            print("Created isolated Farm 1 and Farm 2 with fields and surveys")

        db.commit()
        print("--- Phase 9 Seeding Successfully Completed ---")

    except Exception as e:
        db.rollback()
        print(f"Error seeding Phase 9 users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_phase9()
