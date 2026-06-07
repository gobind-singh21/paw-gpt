from app.config import ALGORITHM
from app.config import PRIVATE_KEY
from app.config import PUBLIC_KEY
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from passlib.context import CryptContext

import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Makes a hash for a plain password

        Args:
            password (str): Plain password string to be hashed

        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies the plain password against the hash

        Args:
            plain_password (str): Plain password to be checked
            hashed_password (str): Hashed password retrieved from database

        Returns:
            bool: Wether plain password matches the hash or not
        """
        return pwd_context.verify(plain_password, hashed_password)

security_bearer = HTTPBearer()

def create_jwt_token(data: dict, expires_delta: timedelta, token_type: str = "access") -> str:
    """Creates a JWT token for the given data and encodes it using private key

    Args:
        data (dict): Data to be encoded in the JWT
        expires_delta (timedelta): time after which the token should expire
        token_type (str, optional): Type of token. Defaults to "access".

    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

def verify_jwt_token(token: str, expected_type: str = "access") -> dict:
    """Verifies the JWT token is valid or not using the public key

    Args:
        token (str): JWT token to be verified
        expected_type (str, optional): Expected type of the token. Defaults to "access".

    Raises:
        HTTPException: HTTP 401 if token type doesn't matches with the expected token type
        HTTPException: HTTP 401 if token is expired
        HTTPException: HTTP 401 if token is invalid

    Returns:
        dict: Decoded data within the JWT token
    """
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=ALGORITHM)
        if payload.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"{expected_type.capitalize()} token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid {expected_type}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)) -> dict:
    token = credentials.credentials
    payload = verify_jwt_token(token, expected_type="access")
    return {"username": payload.get("sub")}