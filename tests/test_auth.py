#!/usr/bin/env python3
"""
认证模块测试
测试用户注册、登录、会话管理等功能
"""

import sys
import os
import unittest
import tempfile
import time

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.auth import (
    AuthService, UserStore, SessionManager, PasswordHasher,
    User, Session, AuthError
)


class TestPasswordHasher(unittest.TestCase):
    """密码哈希工具测试"""
    
    def setUp(self):
        self.hasher = PasswordHasher()
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "test_password_123"
        hash1, salt1 = self.hasher.hash_password(password)
        
        # 哈希值应该包含盐值
        self.assertIn(":", hash1)
        self.assertIsNotNone(salt1)
        
        # 相同密码使用相同盐值应产生相同哈希
        hash2, _ = self.hasher.hash_password(password, salt1)
        self.assertEqual(hash1, hash2)
    
    def test_hash_different_passwords(self):
        """测试不同密码产生不同哈希"""
        hash1, _ = self.hasher.hash_password("password1")
        hash2, _ = self.hasher.hash_password("password2")
        
        self.assertNotEqual(hash1, hash2)
    
    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "correct_password"
        hash_value, _ = self.hasher.hash_password(password)
        
        self.assertTrue(self.hasher.verify_password(password, hash_value))
    
    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "correct_password"
        hash_value, _ = self.hasher.hash_password(password)
        
        self.assertFalse(self.hasher.verify_password("wrong_password", hash_value))
    
    def test_verify_invalid_hash(self):
        """测试无效哈希值"""
        self.assertFalse(self.hasher.verify_password("password", "invalid_hash"))
        self.assertFalse(self.hasher.verify_password("password", ""))


class TestUserStore(unittest.TestCase):
    """用户存储测试"""
    
    def setUp(self):
        # 使用临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.store = UserStore(self.temp_file.name)
    
    def tearDown(self):
        # 清理临时文件
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_create_user(self):
        """测试创建用户"""
        user = User(
            user_id="test_id_1",
            username="testuser",
            password_hash="hash:value",
            email="test@example.com"
        )
        
        result = self.store.create_user(user)
        self.assertTrue(result)
        
        # 验证用户已保存
        saved_user = self.store.get_user_by_id("test_id_1")
        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.username, "testuser")
    
    def test_create_duplicate_user(self):
        """测试创建重复用户"""
        user = User(
            user_id="test_id_1",
            username="testuser",
            password_hash="hash:value",
            email="test@example.com"
        )
        
        self.store.create_user(user)
        result = self.store.create_user(user)
        self.assertFalse(result)
    
    def test_get_user_by_username(self):
        """测试按用户名查找"""
        user = User(
            user_id="test_id_1",
            username="findme",
            password_hash="hash:value",
            email="test@example.com"
        )
        self.store.create_user(user)
        
        found = self.store.get_user_by_username("findme")
        self.assertIsNotNone(found)
        self.assertEqual(found.user_id, "test_id_1")
        
        not_found = self.store.get_user_by_username("notexist")
        self.assertIsNone(not_found)
    
    def test_get_user_by_email(self):
        """测试按邮箱查找"""
        user = User(
            user_id="test_id_1",
            username="testuser",
            password_hash="hash:value",
            email="unique@example.com"
        )
        self.store.create_user(user)
        
        found = self.store.get_user_by_email("unique@example.com")
        self.assertIsNotNone(found)
        
        not_found = self.store.get_user_by_email("other@example.com")
        self.assertIsNone(not_found)
    
    def test_update_user(self):
        """测试更新用户"""
        user = User(
            user_id="test_id_1",
            username="oldname",
            password_hash="hash:value",
            email="test@example.com"
        )
        self.store.create_user(user)
        
        user.username = "newname"
        result = self.store.update_user(user)
        self.assertTrue(result)
        
        updated = self.store.get_user_by_id("test_id_1")
        self.assertEqual(updated.username, "newname")
    
    def test_delete_user(self):
        """测试删除用户"""
        user = User(
            user_id="test_id_1",
            username="todelete",
            password_hash="hash:value",
            email="test@example.com"
        )
        self.store.create_user(user)
        
        result = self.store.delete_user("test_id_1")
        self.assertTrue(result)
        
        deleted = self.store.get_user_by_id("test_id_1")
        self.assertIsNone(deleted)


class TestSessionManager(unittest.TestCase):
    """会话管理器测试"""
    
    def setUp(self):
        self.manager = SessionManager(session_timeout=2)  # 2秒超时用于测试
    
    def test_create_session(self):
        """测试创建会话"""
        session_id = self.manager.create_session("user_1", "127.0.0.1", "TestAgent")
        
        self.assertIsNotNone(session_id)
        self.assertTrue(len(session_id) > 20)
    
    def test_get_session(self):
        """测试获取会话"""
        session_id = self.manager.create_session("user_1")
        
        session = self.manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session.user_id, "user_1")
    
    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        session = self.manager.get_session("nonexistent_session_id")
        self.assertIsNone(session)
    
    def test_session_expiry(self):
        """测试会话过期"""
        session_id = self.manager.create_session("user_1")
        
        # 等待会话过期
        time.sleep(2.5)
        
        session = self.manager.get_session(session_id)
        self.assertIsNone(session)
    
    def test_refresh_session(self):
        """测试刷新会话"""
        session_id = self.manager.create_session("user_1")
        
        time.sleep(1)
        
        # 刷新会话
        result = self.manager.refresh_session(session_id)
        self.assertTrue(result)
        
        time.sleep(1.5)
        
        # 会话应该仍然有效
        session = self.manager.get_session(session_id)
        self.assertIsNotNone(session)
    
    def test_destroy_session(self):
        """测试销毁会话"""
        session_id = self.manager.create_session("user_1")
        
        result = self.manager.destroy_session(session_id)
        self.assertTrue(result)
        
        session = self.manager.get_session(session_id)
        self.assertIsNone(session)
    
    def test_get_user_sessions(self):
        """测试获取用户所有会话"""
        self.manager.create_session("user_1")
        self.manager.create_session("user_1")
        self.manager.create_session("user_2")
        
        user1_sessions = self.manager.get_user_sessions("user_1")
        self.assertEqual(len(user1_sessions), 2)
        
        user2_sessions = self.manager.get_user_sessions("user_2")
        self.assertEqual(len(user2_sessions), 1)
    
    def test_destroy_user_sessions(self):
        """测试销毁用户所有会话"""
        self.manager.create_session("user_1")
        self.manager.create_session("user_1")
        self.manager.create_session("user_2")
        
        self.manager.destroy_user_sessions("user_1")
        
        user1_sessions = self.manager.get_user_sessions("user_1")
        self.assertEqual(len(user1_sessions), 0)
        
        user2_sessions = self.manager.get_user_sessions("user_2")
        self.assertEqual(len(user2_sessions), 1)


class TestAuthService(unittest.TestCase):
    """认证服务测试"""
    
    def setUp(self):
        # 使用临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        user_store = UserStore(self.temp_file.name)
        session_manager = SessionManager(session_timeout=60)
        self.auth = AuthService(user_store, session_manager)
    
    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_register_success(self):
        """测试注册成功"""
        success, message, user = self.auth.register(
            "newuser", "password123", "new@example.com"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "注册成功")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "newuser")
    
    def test_register_short_username(self):
        """测试用户名太短"""
        success, message, user = self.auth.register(
            "ab", "password123", "test@example.com"
        )
        
        self.assertFalse(success)
        self.assertIn("3", message)  # 至少3个字符
        self.assertIsNone(user)
    
    def test_register_short_password(self):
        """测试密码太短"""
        success, message, user = self.auth.register(
            "username", "12345", "test@example.com"
        )
        
        self.assertFalse(success)
        self.assertIn("6", message)  # 至少6个字符
        self.assertIsNone(user)
    
    def test_register_invalid_email(self):
        """测试无效邮箱"""
        success, message, user = self.auth.register(
            "username", "password123", "invalid_email"
        )
        
        self.assertFalse(success)
        self.assertIn("邮箱", message)
        self.assertIsNone(user)
    
    def test_register_duplicate_username(self):
        """测试重复用户名"""
        self.auth.register("existuser", "password123", "first@example.com")
        
        success, message, user = self.auth.register(
            "existuser", "password456", "second@example.com"
        )
        
        self.assertFalse(success)
        self.assertIn("已被注册", message)
    
    def test_register_duplicate_email(self):
        """测试重复邮箱"""
        self.auth.register("user1", "password123", "same@example.com")
        
        success, message, user = self.auth.register(
            "user2", "password456", "same@example.com"
        )
        
        self.assertFalse(success)
        self.assertIn("已被注册", message)
    
    def test_login_success(self):
        """测试登录成功"""
        self.auth.register("loginuser", "password123", "login@example.com")
        
        success, message, session_id, user = self.auth.login("loginuser", "password123")
        
        self.assertTrue(success)
        self.assertEqual(message, "登录成功")
        self.assertIsNotNone(session_id)
        self.assertIsNotNone(user)
    
    def test_login_wrong_password(self):
        """测试密码错误"""
        self.auth.register("loginuser", "password123", "login@example.com")
        
        success, message, session_id, user = self.auth.login("loginuser", "wrongpassword")
        
        self.assertFalse(success)
        self.assertIn("错误", message)
        self.assertIsNone(session_id)
    
    def test_login_nonexistent_user(self):
        """测试用户不存在"""
        success, message, session_id, user = self.auth.login("nouser", "password123")
        
        self.assertFalse(success)
        self.assertIn("错误", message)
        self.assertIsNone(session_id)
    
    def test_logout(self):
        """测试登出"""
        self.auth.register("logoutuser", "password123", "logout@example.com")
        _, _, session_id, _ = self.auth.login("logoutuser", "password123")
        
        success, message = self.auth.logout(session_id)
        
        self.assertTrue(success)
        
        # 验证会话已销毁
        is_valid, user = self.auth.validate_session(session_id)
        self.assertFalse(is_valid)
    
    def test_validate_session(self):
        """测试会话验证"""
        self.auth.register("validateuser", "password123", "validate@example.com")
        _, _, session_id, _ = self.auth.login("validateuser", "password123")
        
        is_valid, user = self.auth.validate_session(session_id)
        
        self.assertTrue(is_valid)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "validateuser")
    
    def test_validate_invalid_session(self):
        """测试无效会话验证"""
        is_valid, user = self.auth.validate_session("invalid_session_id")
        
        self.assertFalse(is_valid)
        self.assertIsNone(user)
    
    def test_change_password(self):
        """测试修改密码"""
        self.auth.register("pwduser", "oldpassword", "pwd@example.com")
        _, _, session_id, user = self.auth.login("pwduser", "oldpassword")
        
        success, message = self.auth.change_password(
            user.user_id, "oldpassword", "newpassword"
        )
        
        self.assertTrue(success)
        
        # 验证旧密码无法登录
        success2, _, _, _ = self.auth.login("pwduser", "oldpassword")
        self.assertFalse(success2)
        
        # 验证新密码可以登录
        success3, _, _, _ = self.auth.login("pwduser", "newpassword")
        self.assertTrue(success3)
    
    def test_change_password_wrong_old(self):
        """测试修改密码时旧密码错误"""
        self.auth.register("pwduser", "correctpassword", "pwd@example.com")
        _, _, _, user = self.auth.login("pwduser", "correctpassword")
        
        success, message = self.auth.change_password(
            user.user_id, "wrongoldpassword", "newpassword"
        )
        
        self.assertFalse(success)
        self.assertIn("原密码", message)


class TestUserModel(unittest.TestCase):
    """用户模型测试"""
    
    def test_user_to_dict(self):
        """测试用户转字典（不包含密码）"""
        user = User(
            user_id="test_id",
            username="testuser",
            password_hash="secret_hash",
            email="test@example.com",
            role="user",
            created_at="2024-01-01T00:00:00",
            last_login="2024-01-02T00:00:00",
            is_active=True
        )
        
        user_dict = user.to_dict()
        
        self.assertEqual(user_dict["username"], "testuser")
        self.assertEqual(user_dict["email"], "test@example.com")
        self.assertNotIn("password_hash", user_dict)


def main():
    """运行测试"""
    print("\n" + "=" * 60)
    print("           认证模块测试 (Auth Module Tests)")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestPasswordHasher))
    suite.addTests(loader.loadTestsFromTestCase(TestUserStore))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthService))
    suite.addTests(loader.loadTestsFromTestCase(TestUserModel))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出汇总
    print("\n" + "=" * 60)
    print(f"测试完成: {result.testsRun} 个测试")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
