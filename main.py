from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
import models
import auth
import complaints
import admin


app = FastAPI(title="City Complaint Platform")


models.Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(admin.router)


@app.get("/")
def home():
    return {
        "message": "City Complaint Platform API is running"
    }