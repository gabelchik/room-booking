import uuid
from src.db.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def ensure_default_users(self, admin_uuid: uuid.UUID, user_uuid: uuid.UUID):
        admin = await self.user_repo.get_by_id(admin_uuid)
        if not admin:
            await self.user_repo.create_user(admin_uuid, "admin")
        user = await self.user_repo.get_by_id(user_uuid)
        if not user:
            await self.user_repo.create_user(user_uuid, "user")