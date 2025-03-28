import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

JWT_SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

def create_access_token(data: dict, expires_minutes: int = 15):
    to_encode = data.copy()
    iat = datetime.now(timezone.utc)
    exp = iat + timedelta(minutes=expires_minutes)
    to_encode.update({
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp())
    })

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_days: int = 7):
    to_encode = data.copy()
    iat = datetime.now(timezone.utc)
    exp = iat + timedelta(days=expires_days)
    to_encode.update({
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp())
    })

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt
