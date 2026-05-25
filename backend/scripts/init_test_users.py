"""
初始化测试账号脚本
在数据库中创建 E2E 测试所需的测试用户

Usage:
    python -m scripts.init_test_users
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.user import User, UserStatus
from app.models.role import Role
from app.services.auth import init_default_roles


async def create_test_users():
    """创建测试用户"""
    test_users = [
        {
            "username": "adminuser",
            "email": "admin@example.com",
            "password": "Admin123456",
            "full_name": "Admin User",
            "is_superuser": True,
            "status": UserStatus.ACTIVE,
        },
        {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123456",
            "full_name": "Test User",
            "is_superuser": False,
            "status": UserStatus.ACTIVE,
        },
        {
            "username": "viewer",
            "email": "viewer@example.com",
            "password": "Viewer123456",
            "full_name": "Viewer User",
            "is_superuser": False,
            "status": UserStatus.ACTIVE,
        },
    ]

    async with async_session_maker() as session:
        try:
            # 初始化默认角色
            await init_default_roles(session)

            created_count = 0
            for user_data in test_users:
                # 检查用户是否已存在
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.username == user_data["username"])
                )
                existing_user = result.scalar_one_or_none()

                if existing_user:
                    print(f"  ⏭️  用户 {user_data['username']} 已存在，跳过")
                    continue

                # 创建用户
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    is_superuser=user_data["is_superuser"],
                    status=user_data["status"],
                )
                session.add(user)
                created_count += 1
                print(f"  ✅ 创建用户: {user_data['username']} ({user_data['email']})")

            await session.commit()
            print(f"\n成功创建 {created_count} 个测试用户")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 错误: {e}")
            raise


def main():
    """主入口"""
    print("=" * 50)
    print("初始化测试用户")
    print("=" * 50)

    asyncio.run(create_test_users())

    print("\n" + "=" * 50)
    print("测试账号:")
    print("  adminuser / Admin123456 (超级管理员)")
    print("  testuser / Test123456 (普通用户)")
    print("  viewer / Viewer123456 (只读用户)")
    print("=" * 50)


if __name__ == "__main__":
    main()