# ============================================================
# DATABASE - PostgreSQL setup and models
# ============================================================

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- DATABASE CONNECTION ---
DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/options_pricer"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- USERS TABLE ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.now)

# --- API KEYS TABLE ---
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    calls_remaining = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.now)

# --- API USAGE TABLE ---
class APIUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True)
    api_key = Column(String, nullable=False)
    index = Column(String, nullable=False)
    strike = Column(Float, nullable=False)
    expiry_type = Column(String, nullable=False)
    call_price = Column(Float, nullable=False)
    put_price = Column(Float, nullable=False)
    called_at = Column(DateTime, default=datetime.now)

# --- CREATE ALL TABLES ---
def create_tables():
    Base.metadata.create_all(engine)
    print("Tables created successfully!")

# --- ADD DEFAULT USERS AND KEYS ---
def seed_data():
    db = SessionLocal()

    # Check if data already exists
    existing = db.query(User).first()
    if existing:
        print("Data already exists - skipping seed")
        db.close()
        return

    # Create demo user
    demo_user = User(name="Demo User", email="demo@optionspricer.com", plan="free")
    pro_user = User(name="Pro User", email="pro@optionspricer.com", plan="pro")

    db.add(demo_user)
    db.add(pro_user)
    db.commit()
    db.refresh(demo_user)
    db.refresh(pro_user)

    # Create API keys
    demo_key = APIKey(user_id=demo_user.id, api_key="demo-key-123", calls_remaining=10)
    pro_key = APIKey(user_id=pro_user.id, api_key="pro-key-456", calls_remaining=999999)

    db.add(demo_key)
    db.add(pro_key)
    db.commit()

    print("Seed data added successfully!")
    db.close()

if __name__ == "__main__":
    create_tables()
    seed_data()