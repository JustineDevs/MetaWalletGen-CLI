#!/usr/bin/env python3
"""
MetaWalletGen CLI - Complete System Test Suite

This module provides comprehensive testing of the entire system,
including integration tests, performance tests, and security tests.
"""

import unittest
import tempfile
import shutil
import os
import sys
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from metagen.core.wallet_generator import WalletGenerator
from metagen.core.encryption import EncryptionManager
from metagen.core.storage_manager import StorageManager
from metagen.enterprise.auth import AuthManager, User, Role, Permission
from metagen.enterprise.database import DatabaseManager, WalletRepository
from metagen.enterprise.analytics import AnalyticsEngine, ReportGenerator
from metagen.enterprise.audit import AuditLogger, AuditLevel
from metagen.performance.monitor import PerformanceMonitor
from metagen.performance.cache import CacheManager
from metagen.performance.load_balancer import LoadBalancer
from metagen.api.rest_api import MetaWalletGenAPI
from metagen.api.web_dashboard import WebDashboard

class TestCompleteSystem(unittest.TestCase):
    """Test the complete MetaWalletGen CLI system"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        
        # Initialize components
        self.db_manager = DatabaseManager(db_path=self.db_path)
        self.auth_manager = AuthManager(db_path=self.db_path)
        self.wallet_repo = WalletRepository(self.db_manager)
        self.analytics_engine = AnalyticsEngine()
        self.audit_logger = AuditLogger(db_path=self.db_path)
        self.wallet_generator = WalletGenerator()
        self.encryption_manager = EncryptionManager()
        self.storage_manager = StorageManager()
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager()
        self.load_balancer = LoadBalancer()
        
        # Create test user
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            role=Role.USER
        )
        self.auth_manager.create_user(self.test_user, "testpass123")
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_01_wallet_generation_workflow(self):
        """Test complete wallet generation workflow"""
        print("\n🧪 Testing Wallet Generation Workflow...")
        
        # Generate wallets
        wallets = self.wallet_generator.generate_wallets(3)
        self.assertEqual(len(wallets), 3)
        
        # Validate wallet data
        for wallet in wallets:
            self.assertTrue(wallet.address.startswith('0x'))
            self.assertEqual(len(wallet.private_key), 66)  # 0x + 64 hex chars
            self.assertTrue(len(wallet.mnemonic.split()) >= 12)
        
        # Store in database
        for wallet in wallets:
            record = self.wallet_repo.create_wallet_record(
                address=wallet.address,
                private_key=wallet.private_key,
                mnemonic=wallet.mnemonic,
                network='mainnet',
                user_id=self.test_user.username
            )
            self.assertIsNotNone(record.id)
        
        # Retrieve from database
        stored_wallets = self.wallet_repo.get_wallets_by_user(self.test_user.username)
        self.assertEqual(len(stored_wallets), 3)
        
        print("✅ Wallet generation workflow completed successfully")
    
    def test_02_encryption_and_storage(self):
        """Test encryption and storage functionality"""
        print("\n🔒 Testing Encryption and Storage...")
        
        # Create test data
        test_data = {
            'wallets': [
                {'address': '0x123...', 'private_key': '0xabc...'},
                {'address': '0x456...', 'private_key': '0xdef...'}
            ]
        }
        
        # Encrypt data
        password = "secure_password_123"
        encrypted_data = self.encryption_manager.encrypt_data(
            json.dumps(test_data), password
        )
        self.assertIsNotNone(encrypted_data)
        
        # Decrypt data
        decrypted_data = self.encryption_manager.decrypt_data(
            encrypted_data, password
        )
        self.assertEqual(json.loads(decrypted_data), test_data)
        
        # Test storage
        storage_path = os.path.join(self.test_dir, 'wallets.json')
        self.storage_manager.save_wallets(
            test_data['wallets'], storage_path, format='json'
        )
        
        # Verify file exists
        self.assertTrue(os.path.exists(storage_path))
        
        # Load and verify data
        loaded_data = self.storage_manager.load_wallets(storage_path, format='json')
        self.assertEqual(loaded_data, test_data['wallets'])
        
        print("✅ Encryption and storage functionality completed successfully")
    
    def test_03_authentication_and_authorization(self):
        """Test authentication and authorization system"""
        print("\n🔐 Testing Authentication and Authorization...")
        
        # Test user authentication
        auth_result = self.auth_manager.authenticate_user("testuser", "testpass123")
        self.assertTrue(auth_result)
        
        # Test invalid password
        auth_result = self.auth_manager.authenticate_user("testuser", "wrongpass")
        self.assertFalse(auth_result)
        
        # Test user permissions
        user = self.auth_manager.get_user("testuser")
        self.assertIsNotNone(user)
        
        # Test role-based permissions
        self.assertTrue(self.auth_manager.user_has_permission(user, Permission.READ))
        self.assertFalse(self.auth_manager.user_has_permission(user, Permission.ADMIN))
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            role=Role.ADMIN
        )
        self.auth_manager.create_user(admin_user, "adminpass123")
        
        # Test admin permissions
        admin = self.auth_manager.get_user("admin")
        self.assertTrue(self.auth_manager.user_has_permission(admin, Permission.ADMIN))
        
        print("✅ Authentication and authorization completed successfully")
    
    def test_04_database_operations(self):
        """Test database operations and integrity"""
        print("\n🗄️ Testing Database Operations...")
        
        # Test wallet creation
        wallet_record = self.wallet_repo.create_wallet_record(
            address="0x1234567890abcdef",
            private_key="0xabcdef1234567890",
            mnemonic="test mnemonic phrase here",
            network="mainnet",
            user_id=self.test_user.username
        )
        self.assertIsNotNone(wallet_record.id)
        
        # Test wallet retrieval
        retrieved_wallet = self.wallet_repo.get_wallet_by_id(wallet_record.id)
        self.assertEqual(retrieved_wallet.address, "0x1234567890abcdef")
        
        # Test wallet update
        self.wallet_repo.update_wallet_record(
            wallet_record.id, tags=["test", "mainnet"]
        )
        updated_wallet = self.wallet_repo.get_wallet_by_id(wallet_record.id)
        self.assertIn("test", updated_wallet.tags)
        
        # Test wallet deletion
        self.wallet_repo.delete_wallet_record(wallet_record.id)
        deleted_wallet = self.wallet_repo.get_wallet_by_id(wallet_record.id)
        self.assertIsNone(deleted_wallet)
        
        print("✅ Database operations completed successfully")
    
    def test_05_analytics_and_reporting(self):
        """Test analytics and reporting functionality"""
        print("\n📊 Testing Analytics and Reporting...")
        
        # Generate sample data
        for i in range(5):
            wallet_record = self.wallet_repo.create_wallet_record(
                address=f"0x{i:040x}",
                private_key=f"0x{i:064x}",
                mnemonic=f"test mnemonic {i}",
                network="mainnet",
                user_id=self.test_user.username
            )
        
        # Test analytics
        wallet_stats = self.analytics_engine.get_wallet_statistics()
        self.assertIsNotNone(wallet_stats)
        
        # Test report generation
        report_config = {
            'format': 'html',
            'include_charts': True,
            'title': 'Test Report'
        }
        
        report = self.analytics_engine.generate_report(
            report_type='wallet_summary',
            config=report_config
        )
        self.assertIsNotNone(report)
        
        print("✅ Analytics and reporting completed successfully")
    
    def test_06_audit_and_compliance(self):
        """Test audit logging and compliance"""
        print("\n📝 Testing Audit and Compliance...")
        
        # Test audit logging
        audit_event = self.audit_logger.log_event(
            level=AuditLevel.INFO,
            user_id=self.test_user.username,
            action="wallet_generated",
            details="Test wallet generation",
            ip_address="127.0.0.1"
        )
        self.assertIsNotNone(audit_event.id)
        
        # Test audit retrieval
        events = self.audit_logger.get_recent_events(limit=10)
        self.assertGreater(len(events), 0)
        
        # Test compliance rules
        compliance_result = self.audit_logger.check_compliance(
            user_id=self.test_user.username,
            action="wallet_generated"
        )
        self.assertIsNotNone(compliance_result)
        
        print("✅ Audit and compliance completed successfully")
    
    def test_07_performance_monitoring(self):
        """Test performance monitoring system"""
        print("\n⚡ Testing Performance Monitoring...")
        
        # Test system metrics
        cpu_usage = self.performance_monitor.get_cpu_usage()
        memory_usage = self.performance_monitor.get_memory_usage()
        disk_usage = self.performance_monitor.get_disk_usage()
        
        self.assertIsInstance(cpu_usage, (int, float))
        self.assertIsInstance(memory_usage, (int, float))
        self.assertIsInstance(disk_usage, (int, float))
        
        # Test performance recording
        self.performance_monitor.record_operation(
            operation="wallet_generation",
            duration=0.5,
            success=True
        )
        
        # Test metrics retrieval
        metrics = self.performance_monitor.get_current_metrics()
        self.assertIsNotNone(metrics)
        
        print("✅ Performance monitoring completed successfully")
    
    def test_08_caching_system(self):
        """Test caching system functionality"""
        print("\n💾 Testing Caching System...")
        
        # Test cache operations
        self.cache_manager.set("test_key", "test_value", ttl=60)
        
        # Test cache retrieval
        value = self.cache_manager.get("test_key")
        self.assertEqual(value, "test_value")
        
        # Test cache expiration
        self.cache_manager.set("expire_key", "expire_value", ttl=1)
        time.sleep(1.1)
        expired_value = self.cache_manager.get("expire_key")
        self.assertIsNone(expired_value)
        
        # Test cache statistics
        stats = self.cache_manager.get_stats()
        self.assertIsNotNone(stats)
        
        print("✅ Caching system completed successfully")
    
    def test_09_load_balancing(self):
        """Test load balancing functionality"""
        print("\n⚖️ Testing Load Balancing...")
        
        # Add workers
        self.load_balancer.add_worker("worker1", capacity=100)
        self.load_balancer.add_worker("worker2", capacity=150)
        self.load_balancer.add_worker("worker3", capacity=200)
        
        # Test round-robin strategy
        worker1 = self.load_balancer.get_next_worker("round_robin")
        worker2 = self.load_balancer.get_next_worker("round_robin")
        worker3 = self.load_balancer.get_next_worker("round_robin")
        
        self.assertIsNotNone(worker1)
        self.assertIsNotNone(worker2)
        self.assertIsNotNone(worker3)
        
        # Test least-connections strategy
        worker = self.load_balancer.get_next_worker("least_connections")
        self.assertIsNotNone(worker)
        
        print("✅ Load balancing completed successfully")
    
    def test_10_api_integration(self):
        """Test API integration and endpoints"""
        print("\n🌐 Testing API Integration...")
        
        # Mock Flask app for testing
        with patch('metagen.api.rest_api.Flask') as mock_flask:
            mock_app = MagicMock()
            mock_flask.return_value = mock_app
            
            # Create API instance
            api = MetaWalletGenAPI(
                host='127.0.0.1',
                port=5000,
                debug=False
            )
            
            # Test API initialization
            self.assertIsNotNone(api)
            
            # Test health endpoint
            with api.app.test_client() as client:
                response = client.get('/api/health')
                self.assertEqual(response.status_code, 200)
        
        print("✅ API integration completed successfully")
    
    def test_11_web_dashboard(self):
        """Test web dashboard functionality"""
        print("\n🖥️ Testing Web Dashboard...")
        
        # Mock Flask dependencies
        with patch('metagen.api.web_dashboard.FLASK_AVAILABLE', True):
            with patch('metagen.api.web_dashboard.Flask') as mock_flask:
                mock_app = MagicMock()
                mock_flask.return_value = mock_app
                
                # Create dashboard instance
                dashboard = WebDashboard(
                    host='127.0.0.1',
                    port=5001,
                    debug=False
                )
                
                # Test dashboard initialization
                self.assertIsNotNone(dashboard)
                self.assertEqual(dashboard.host, '127.0.0.1')
                self.assertEqual(dashboard.port, 5001)
                
                # Test status method
                status = dashboard.get_status()
                self.assertIsInstance(status, dict)
                self.assertIn('host', status)
                self.assertIn('port', status)
        
        print("✅ Web dashboard completed successfully")
    
    def test_12_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔄 Testing End-to-End Workflow...")
        
        # 1. User authentication
        auth_result = self.auth_manager.authenticate_user("testuser", "testpass123")
        self.assertTrue(auth_result)
        
        # 2. Generate wallets
        wallets = self.wallet_generator.generate_wallets(2)
        self.assertEqual(len(wallets), 2)
        
        # 3. Store in database
        for wallet in wallets:
            record = self.wallet_repo.create_wallet_record(
                address=wallet.address,
                private_key=wallet.private_key,
                mnemonic=wallet.mnemonic,
                network='mainnet',
                user_id=self.test_user.username
            )
            self.assertIsNotNone(record.id)
        
        # 4. Encrypt and store to file
        wallet_data = [w.to_dict() for w in wallets]
        storage_path = os.path.join(self.test_dir, 'encrypted_wallets.vault')
        
        password = "secure_storage_password"
        encrypted_data = self.encryption_manager.encrypt_data(
            json.dumps(wallet_data), password
        )
        
        with open(storage_path, 'wb') as f:
            f.write(encrypted_data)
        
        # 5. Verify storage
        self.assertTrue(os.path.exists(storage_path))
        
        # 6. Load and decrypt
        with open(storage_path, 'rb') as f:
            loaded_encrypted = f.read()
        
        decrypted_data = self.encryption_manager.decrypt_data(
            loaded_encrypted, password
        )
        loaded_wallets = json.loads(decrypted_data)
        
        # 7. Verify data integrity
        self.assertEqual(len(loaded_wallets), 2)
        self.assertEqual(loaded_wallets[0]['address'], wallets[0].address)
        
        # 8. Generate analytics
        wallet_stats = self.analytics_engine.get_wallet_statistics()
        self.assertIsNotNone(wallet_stats)
        
        # 9. Audit logging
        audit_event = self.audit_logger.log_event(
            level=AuditLevel.INFO,
            user_id=self.test_user.username,
            action="end_to_end_test",
            details="Complete workflow test",
            ip_address="127.0.0.1"
        )
        self.assertIsNotNone(audit_event.id)
        
        print("✅ End-to-end workflow completed successfully")
    
    def test_13_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n🏃 Testing Performance Benchmarks...")
        
        # Test wallet generation performance
        start_time = time.time()
        wallets = self.wallet_generator.generate_wallets(100)
        generation_time = time.time() - start_time
        
        self.assertEqual(len(wallets), 100)
        self.assertLess(generation_time, 10.0)  # Should complete within 10 seconds
        
        # Test encryption performance
        test_data = json.dumps([w.to_dict() for w in wallets])
        password = "benchmark_password"
        
        start_time = time.time()
        encrypted_data = self.encryption_manager.encrypt_data(test_data, password)
        encryption_time = time.time() - start_time
        
        self.assertLess(encryption_time, 5.0)  # Should complete within 5 seconds
        
        # Test decryption performance
        start_time = time.time()
        decrypted_data = self.encryption_manager.decrypt_data(encrypted_data, password)
        decryption_time = time.time() - start_time
        
        self.assertLess(decryption_time, 5.0)  # Should complete within 5 seconds
        self.assertEqual(decrypted_data, test_data)
        
        print(f"✅ Performance benchmarks completed:")
        print(f"   - Wallet generation: {generation_time:.3f}s for 100 wallets")
        print(f"   - Encryption: {encryption_time:.3f}s")
        print(f"   - Decryption: {decryption_time:.3f}s")
    
    def test_14_security_features(self):
        """Test security features"""
        print("\n🛡️ Testing Security Features...")
        
        # Test password strength validation
        weak_password = "123"
        strong_password = "SecurePass123!@#"
        
        # Test encryption strength
        test_data = "sensitive_wallet_data"
        password = strong_password
        
        encrypted_data = self.encryption_manager.encrypt_data(test_data, password)
        
        # Verify data is actually encrypted
        self.assertNotIn(test_data, str(encrypted_data))
        
        # Test decryption with wrong password
        wrong_password = "WrongPassword123!@#"
        
        with self.assertRaises(Exception):
            self.encryption_manager.decrypt_data(encrypted_data, wrong_password)
        
        # Test correct decryption
        decrypted_data = self.encryption_manager.decrypt_data(encrypted_data, password)
        self.assertEqual(decrypted_data, test_data)
        
        print("✅ Security features completed successfully")
    
    def test_15_error_handling(self):
        """Test error handling and edge cases"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test invalid wallet generation count
        with self.assertRaises(ValueError):
            self.wallet_generator.generate_wallets(-1)
        
        # Test invalid network
        with self.assertRaises(ValueError):
            self.wallet_generator.generate_wallets(1, network="invalid_network")
        
        # Test database connection errors
        invalid_db_path = "/invalid/path/database.db"
        with self.assertRaises(Exception):
            DatabaseManager(db_path=invalid_db_path)
        
        # Test cache with invalid TTL
        with self.assertRaises(ValueError):
            self.cache_manager.set("key", "value", ttl=-1)
        
        print("✅ Error handling completed successfully")

def run_complete_test_suite():
    """Run the complete test suite"""
    print("🚀 Starting MetaWalletGen CLI Complete System Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCompleteSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   - Tests Run: {result.testsRun}")
    print(f"   - Failures: {len(result.failures)}")
    print(f"   - Errors: {len(result.errors)}")
    print(f"   - Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed! MetaWalletGen CLI is ready for production.")
    else:
        print("\n⚠️ Some tests failed. Please review and fix the issues.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_complete_test_suite()
    sys.exit(0 if success else 1)
