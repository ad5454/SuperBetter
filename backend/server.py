from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

security = HTTPBearer()

# Enums
class QuestType(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly" 
    EPIC = "Epic"

class QuestStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    password_hash: str = ""
    total_xp: int = 0
    level: int = 1
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: Optional[datetime] = None
    badges: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Quest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    quest_type: QuestType
    status: QuestStatus = QuestStatus.TODO
    xp_reward: int
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class QuestCreate(BaseModel):
    title: str
    description: str
    quest_type: QuestType
    deadline: Optional[datetime] = None

class PowerUp(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    xp_reward: int = 5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PowerUpCreate(BaseModel):
    title: str
    description: str

class PowerUpLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    power_up_id: str
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BadGuy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    max_hp: int = 100
    current_hp: int = 100
    defeat_xp_reward: int = 15
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BadGuyCreate(BaseModel):
    title: str
    description: str
    max_hp: int = 100

class BadGuyDefeat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    bad_guy_id: str
    damage_dealt: int = 10
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SideQuest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    xp_reward: int = 8

class Badge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: str
    criteria_type: str  # e.g., "streak", "xp", "quests_completed"
    criteria_value: int

class DashboardStats(BaseModel):
    user: User
    quests_today: int
    quests_completed_today: int
    daily_side_quest: Optional[SideQuest]
    recent_badges: List[Badge]

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_level(total_xp: int) -> int:
    return max(1, total_xp // 100)

def get_xp_reward(quest_type: QuestType) -> int:
    rewards = {
        QuestType.DAILY: 10,
        QuestType.WEEKLY: 25,
        QuestType.EPIC: 50
    }
    return rewards.get(quest_type, 10)

async def update_user_xp(user_id: str, xp_gained: int):
    user_data = await db.users.find_one({"id": user_id})
    if user_data:
        new_total_xp = user_data["total_xp"] + xp_gained
        new_level = calculate_level(new_total_xp)
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"total_xp": new_total_xp, "level": new_level}}
        )

async def update_streak(user_id: str):
    user_data = await db.users.find_one({"id": user_id})
    if user_data:
        today = datetime.now(timezone.utc).date()
        last_activity = user_data.get("last_activity_date")
        
        if last_activity:
            last_activity_date = last_activity.date() if isinstance(last_activity, datetime) else last_activity
            
            if last_activity_date == today:
                # Already updated today
                return
            elif last_activity_date == today - timedelta(days=1):
                # Continue streak
                new_streak = user_data["current_streak"] + 1
            else:
                # Streak broken, restart
                new_streak = 1
        else:
            # First activity
            new_streak = 1
        
        longest_streak = max(user_data.get("longest_streak", 0), new_streak)
        
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "current_streak": new_streak,
                "longest_streak": longest_streak,
                "last_activity_date": datetime.now(timezone.utc)
            }}
        )

async def check_and_award_badges(user_id: str):
    user_data = await db.users.find_one({"id": user_id})
    if not user_data:
        return
    
    # Define badge criteria
    badge_criteria = [
        {"name": "First Steps", "criteria_type": "xp", "criteria_value": 10, "icon": "🌟"},
        {"name": "Rising Star", "criteria_type": "xp", "criteria_value": 100, "icon": "⭐"},
        {"name": "Experience Master", "criteria_type": "xp", "criteria_value": 1000, "icon": "🏆"},
        {"name": "Streak Starter", "criteria_type": "streak", "criteria_value": 3, "icon": "🔥"},
        {"name": "Consistency King", "criteria_type": "streak", "criteria_value": 7, "icon": "👑"},
        {"name": "Dedication Legend", "criteria_type": "streak", "criteria_value": 30, "icon": "🗿"},
    ]
    
    current_badges = set(user_data.get("badges", []))
    new_badges = []
    
    for badge in badge_criteria:
        if badge["name"] not in current_badges:
            if badge["criteria_type"] == "xp" and user_data["total_xp"] >= badge["criteria_value"]:
                new_badges.append(badge["name"])
            elif badge["criteria_type"] == "streak" and user_data.get("longest_streak", 0) >= badge["criteria_value"]:
                new_badges.append(badge["name"])
    
    if new_badges:
        await db.users.update_one(
            {"id": user_id},
            {"$push": {"badges": {"$each": new_badges}}}
        )

# Initialize default side quests
async def initialize_side_quests():
    existing = await db.side_quests.count_documents({})
    if existing == 0:
        default_side_quests = [
            {"title": "Take 10 Deep Breaths", "description": "Practice mindful breathing for stress relief", "xp_reward": 8},
            {"title": "Write 3 Things You're Grateful For", "description": "Practice gratitude to boost positivity", "xp_reward": 8},
            {"title": "Do 20 Push-ups", "description": "Get your blood pumping with quick exercise", "xp_reward": 8},
            {"title": "Drink a Full Glass of Water", "description": "Stay hydrated for better health", "xp_reward": 5},
            {"title": "Tidy Your Workspace", "description": "Create a cleaner environment for productivity", "xp_reward": 8},
            {"title": "Text Someone You Care About", "description": "Strengthen your social connections", "xp_reward": 8},
            {"title": "Take a 5-Minute Walk", "description": "Get moving and clear your head", "xp_reward": 8},
            {"title": "Listen to Your Favorite Song", "description": "Boost your mood with music", "xp_reward": 5},
        ]
        
        for sq in default_side_quests:
            side_quest = SideQuest(
                title=sq["title"],
                description=sq["description"], 
                xp_reward=sq["xp_reward"]
            )
            await db.side_quests.insert_one(side_quest.dict())

# Auth endpoints
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password)
    )
    
    await db.users.insert_one(user.dict())
    
    # Create JWT token
    token = create_jwt_token(user.id)
    
    return {"token": token, "user": {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "total_xp": user.total_xp,
        "level": user.level,
        "current_streak": user.current_streak
    }}

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user_data = await db.users.find_one({"email": login_data.email})
    if not user_data or not verify_password(login_data.password, user_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user_data["id"])
    
    return {"token": token, "user": {
        "id": user_data["id"],
        "email": user_data["email"],
        "username": user_data["username"],
        "total_xp": user_data["total_xp"],
        "level": user_data["level"],
        "current_streak": user_data["current_streak"]
    }}

# Dashboard endpoint
@api_router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date()
    
    # Count today's quests
    quests_today = await db.quests.count_documents({
        "user_id": current_user.id,
        "created_at": {"$gte": datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)}
    })
    
    quests_completed_today = await db.quests.count_documents({
        "user_id": current_user.id,
        "status": QuestStatus.DONE,
        "completed_at": {"$gte": datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)}
    })
    
    # Get random side quest
    side_quests = await db.side_quests.find().to_list(None)
    daily_side_quest = None
    if side_quests:
        import random
        daily_side_quest = SideQuest(**random.choice(side_quests))
    
    return DashboardStats(
        user=current_user,
        quests_today=quests_today,
        quests_completed_today=quests_completed_today,
        daily_side_quest=daily_side_quest,
        recent_badges=[]
    )

# Quest endpoints
@api_router.get("/quests", response_model=List[Quest])
async def get_quests(current_user: User = Depends(get_current_user)):
    quests = await db.quests.find({"user_id": current_user.id}).to_list(None)
    return [Quest(**quest) for quest in quests]

@api_router.post("/quests", response_model=Quest)
async def create_quest(quest_data: QuestCreate, current_user: User = Depends(get_current_user)):
    xp_reward = get_xp_reward(quest_data.quest_type)
    
    quest = Quest(
        user_id=current_user.id,
        title=quest_data.title,
        description=quest_data.description,
        quest_type=quest_data.quest_type,
        xp_reward=xp_reward,
        deadline=quest_data.deadline
    )
    
    await db.quests.insert_one(quest.dict())
    return quest

@api_router.put("/quests/{quest_id}/complete")
async def complete_quest(quest_id: str, current_user: User = Depends(get_current_user)):
    quest_data = await db.quests.find_one({"id": quest_id, "user_id": current_user.id})
    if not quest_data:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    if quest_data["status"] == QuestStatus.DONE:
        raise HTTPException(status_code=400, detail="Quest already completed")
    
    # Update quest
    await db.quests.update_one(
        {"id": quest_id},
        {"$set": {"status": QuestStatus.DONE, "completed_at": datetime.now(timezone.utc)}}
    )
    
    # Award XP and update streak
    await update_user_xp(current_user.id, quest_data["xp_reward"])
    await update_streak(current_user.id)
    await check_and_award_badges(current_user.id)
    
    return {"message": "Quest completed!", "xp_gained": quest_data["xp_reward"]}

@api_router.delete("/quests/{quest_id}")
async def delete_quest(quest_id: str, current_user: User = Depends(get_current_user)):
    result = await db.quests.delete_one({"id": quest_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quest not found")
    return {"message": "Quest deleted"}

# Power-up endpoints
@api_router.get("/power-ups", response_model=List[PowerUp])
async def get_power_ups(current_user: User = Depends(get_current_user)):
    power_ups = await db.power_ups.find({"user_id": current_user.id}).to_list(None)
    return [PowerUp(**power_up) for power_up in power_ups]

@api_router.post("/power-ups", response_model=PowerUp)
async def create_power_up(power_up_data: PowerUpCreate, current_user: User = Depends(get_current_user)):
    power_up = PowerUp(
        user_id=current_user.id,
        title=power_up_data.title,
        description=power_up_data.description
    )
    
    await db.power_ups.insert_one(power_up.dict())
    return power_up

@api_router.post("/power-ups/{power_up_id}/log")
async def log_power_up(power_up_id: str, current_user: User = Depends(get_current_user)):
    power_up_data = await db.power_ups.find_one({"id": power_up_id, "user_id": current_user.id})
    if not power_up_data:
        raise HTTPException(status_code=404, detail="Power-up not found")
    
    # Log the power-up usage
    power_up_log = PowerUpLog(
        user_id=current_user.id,
        power_up_id=power_up_id
    )
    await db.power_up_logs.insert_one(power_up_log.dict())
    
    # Award XP
    await update_user_xp(current_user.id, power_up_data["xp_reward"])
    await check_and_award_badges(current_user.id)
    
    return {"message": "Power-up logged!", "xp_gained": power_up_data["xp_reward"]}

# Bad guy endpoints
@api_router.get("/bad-guys", response_model=List[BadGuy])
async def get_bad_guys(current_user: User = Depends(get_current_user)):
    bad_guys = await db.bad_guys.find({"user_id": current_user.id}).to_list(None)
    return [BadGuy(**bad_guy) for bad_guy in bad_guys]

@api_router.post("/bad-guys", response_model=BadGuy)
async def create_bad_guy(bad_guy_data: BadGuyCreate, current_user: User = Depends(get_current_user)):
    bad_guy = BadGuy(
        user_id=current_user.id,
        title=bad_guy_data.title,
        description=bad_guy_data.description,
        max_hp=bad_guy_data.max_hp,
        current_hp=bad_guy_data.max_hp
    )
    
    await db.bad_guys.insert_one(bad_guy.dict())
    return bad_guy

@api_router.post("/bad-guys/{bad_guy_id}/defeat")
async def defeat_bad_guy(bad_guy_id: str, damage: int = 10, current_user: User = Depends(get_current_user)):
    bad_guy_data = await db.bad_guys.find_one({"id": bad_guy_id, "user_id": current_user.id})
    if not bad_guy_data:
        raise HTTPException(status_code=404, detail="Bad guy not found")
    
    # Deal damage
    new_hp = max(0, bad_guy_data["current_hp"] - damage)
    
    # Log the defeat attempt
    defeat_log = BadGuyDefeat(
        user_id=current_user.id,
        bad_guy_id=bad_guy_id,
        damage_dealt=damage
    )
    await db.bad_guy_defeats.insert_one(defeat_log.dict())
    
    # Update bad guy HP
    await db.bad_guys.update_one(
        {"id": bad_guy_id},
        {"$set": {"current_hp": new_hp}}
    )
    
    # Award XP
    await update_user_xp(current_user.id, bad_guy_data["defeat_xp_reward"])
    await check_and_award_badges(current_user.id)
    
    # If defeated, reset HP
    if new_hp == 0:
        await db.bad_guys.update_one(
            {"id": bad_guy_id},
            {"$set": {"current_hp": bad_guy_data["max_hp"]}}
        )
        return {"message": "Bad guy defeated! It has respawned.", "xp_gained": bad_guy_data["defeat_xp_reward"]}
    
    return {"message": f"Dealt {damage} damage!", "xp_gained": bad_guy_data["defeat_xp_reward"], "remaining_hp": new_hp}

# Side quest endpoints
@api_router.get("/side-quests/daily")
async def get_daily_side_quest():
    side_quests = await db.side_quests.find().to_list(None)
    if not side_quests:
        return None
    
    import random
    return SideQuest(**random.choice(side_quests))

@api_router.post("/side-quests/complete")
async def complete_side_quest(current_user: User = Depends(get_current_user)):
    # Get today's side quest
    side_quest = await get_daily_side_quest()
    if not side_quest:
        raise HTTPException(status_code=404, detail="No side quest available")
    
    # Award XP
    await update_user_xp(current_user.id, side_quest.xp_reward)
    await check_and_award_badges(current_user.id)
    
    return {"message": "Side quest completed!", "xp_gained": side_quest.xp_reward}

# Initialize data on startup
@app.on_event("startup")
async def startup_event():
    await initialize_side_quests()

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()