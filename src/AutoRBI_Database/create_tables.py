from AutoRBI_Database.base import Base
from AutoRBI_Database.session import engine

# Import ALL models so SQLAlchemy knows them
from AutoRBI_Database.models import (
    User,
    Work,
    TypeMaterial,
    Equipment,
    Component,
    AssignWork,
    CorrectionLog,
    WorkHistory
)

print("Creating tables...")

Base.metadata.create_all(bind=engine)

print("All tables created successfully!")
