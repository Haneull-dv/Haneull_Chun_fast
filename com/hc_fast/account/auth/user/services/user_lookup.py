import hashlib
from com.hc_fast.utils.creational.builder.redis_builder import redis_client
from com.hc_fast.account.auth.user.repository.find_user import get_check_user_id_stmt, get_login_stmt
from com.hc_fast.utils.creational.abstract.abstract_service import AbstractService
from sqlalchemy.exc import OperationalError
from com.hc_fast.utils.config.security.jwt_config import create_access_token, create_refresh_token
import time
import logging
import traceback

logger = logging.getLogger(__name__)

class Login(AbstractService):
    async def handle(self, **kwargs):
        try:
            user_schema = kwargs.get("user_schema")
            db = kwargs.get("db")
            response = kwargs.get("response")

            user_dict = user_schema if isinstance(user_schema, dict) else user_schema.dict()
            user_id = user_dict.get("user_id")
            password = user_dict.get("password")

            max_attempts = 3

            # 1단계: 사용자 ID 존재 여부 확인
            for attempt in range(max_attempts):
                try:
                    stmt, params = get_check_user_id_stmt(user_id)
                    rows = await db.fetch(stmt, *params)
                    user_exists = rows[0] if rows else None
                    break
                except OperationalError as e:
                    if "Name or service not known" in str(e) or "could not translate host name" in str(e):
                        if attempt < max_attempts - 1:
                            time.sleep(2 ** attempt)
                        else:
                            return {"status": "error", "message": f"DB 연결 오류: {str(e)}", "user": None}
                    else:
                        raise
                except Exception as e:
                    raise

            if user_exists is None:
                return {"status": "error", "message": "등록된 ID가 없습니다", "user": None}

            # 2단계: 로그인 검증
            for attempt in range(max_attempts):
                try:
                    stmt, params = get_login_stmt(user_id, password)
                    rows = await db.fetch(stmt, *params)
                    logged_in_user = rows[0] if rows else None
                    break
                except OperationalError as e:
                    if "Name or service not known" in str(e) or "could not translate host name" in str(e):
                        if attempt < max_attempts - 1:
                            time.sleep(2 ** attempt)
                        else:
                            return {"status": "error", "message": f"로그인 중 DB 연결 오류: {str(e)}", "user": None}
                    else:
                        raise
                except Exception as e:
                    raise

            if logged_in_user is None:
                return {"status": "error", "message": "비밀번호가 일치하지 않습니다", "user": None}

            # 3단계: 토큰 발급
            access_token = create_access_token(data={"sub": logged_in_user["user_id"]})
            refresh_token = create_refresh_token(data={"sub": logged_in_user["user_id"]})
            print("🗝️🗝️🗝️access_token : ", access_token)
            print("🗝️🗝️🗝️refresh_token : ", refresh_token)
            # ✅ redis에 refresh토큰 저장, 토큰 만료 시간은 예: 7일 (초 단위)
            refresh_token_key = f"refresh_token:{logged_in_user['user_id']}"
            refresh_token_ttl = 60 * 60 * 24 * 7  # 7일
            hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
            redis_client.setex(refresh_token_key, refresh_token_ttl, hashed_token)

            return {
                "status": "success",
                "message": "로그인 성공입니다",
                "access_token": access_token,
                "user": {"user_id": logged_in_user["user_id"]}
            }

        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": f"예외 발생: {str(e)}", "user": None}
