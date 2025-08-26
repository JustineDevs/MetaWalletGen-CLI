"""
Web Dashboard for MetaWalletGen CLI.

This module provides a modern web interface for wallet management,
analytics, and system administration.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import plotly.graph_objs as go
import plotly.utils
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..enterprise.auth import AuthManager, User
from ..enterprise.database import DatabaseManager, WalletRepository
from ..enterprise.analytics import AnalyticsEngine, ReportGenerator
from ..enterprise.audit import AuditLogger, ComplianceChecker


class WebDashboard:
    """Web dashboard interface for MetaWalletGen CLI."""
    
    def __init__(self, auth_manager: AuthManager, database_manager: DatabaseManager,
                 analytics_engine: AnalyticsEngine, audit_logger: AuditLogger):
        """Initialize web dashboard."""
        self.auth_manager = auth_manager
        self.database_manager = database_manager
        self.analytics_engine = analytics_engine
        self.audit_logger = audit_logger
        self.compliance_checker = ComplianceChecker(audit_logger)
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.secret_key = self.auth_manager._secret_key
        CORS(self.app)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            if not session.get('user_id'):
                return redirect(url_for('login'))
            
            user = self.auth_manager.get_user(session['user_id'])
            if not user:
                return redirect(url_for('login'))
            
            # Get dashboard data
            dashboard_data = self._get_dashboard_data(user)
            return self._render_dashboard(dashboard_data, user)
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """User login."""
            if request.method == 'POST':
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                
                if self.auth_manager.authenticate_user(username, password):
                    user = self.auth_manager.get_user_by_username(username)
                    session['user_id'] = user.user_id
                    session['username'] = user.username
                    session['role'] = user.role.name
                    
                    # Log login event
                    self.audit_logger.log_security_event(
                        user_id=user.user_id,
                        action="login",
                        resource="web_dashboard",
                        details={"ip_address": request.remote_addr},
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                    
                    return jsonify({"success": True, "redirect": "/"})
                else:
                    return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
            return self._render_login()
        
        @self.app.route('/logout')
        def logout():
            """User logout."""
            if session.get('user_id'):
                # Log logout event
                self.audit_logger.log_security_event(
                    user_id=session['user_id'],
                    action="logout",
                    resource="web_dashboard",
                    details={"ip_address": request.remote_addr},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                session.clear()
            
            return redirect(url_for('login'))
        
        @self.app.route('/wallets')
        def wallets():
            """Wallet management page."""
            if not session.get('user_id'):
                return redirect(url_for('login'))
            
            user = self.auth_manager.get_user(session['user_id'])
            if not user:
                return redirect(url_for('login'))
            
            # Get user's wallets
            wallet_repo = WalletRepository(self.database_manager)
            user_wallets = wallet_repo.get_wallets_by_user(user.user_id)
            
            return self._render_wallets(user_wallets, user)
        
        @self.app.route('/analytics')
        def analytics():
            """Analytics and reporting page."""
            if not session.get('user_id'):
                return redirect(url_for('login'))
            
            user = self.auth_manager.get_user(session['user_id'])
            if not user:
                return redirect(url_for('login'))
            
            # Check if user has analytics access
            if not user.role.has_permission('view_analytics'):
                return jsonify({"error": "Access denied"}), 403
            
            analytics_data = self._get_analytics_data()
            return self._render_analytics(analytics_data, user)
        
        @self.app.route('/admin')
        def admin():
            """Admin panel."""
            if not session.get('user_id'):
                return redirect(url_for('login'))
            
            user = self.auth_manager.get_user(session['user_id'])
            if not user:
                return redirect(url_for('login'))
            
            # Check if user is admin
            if user.role.name != 'admin':
                return jsonify({"error": "Access denied"}), 403
            
            admin_data = self._get_admin_data()
            return self._render_admin(admin_data, user)
        
        @self.app.route('/api/wallets', methods=['GET', 'POST'])
        def api_wallets():
            """API endpoint for wallet operations."""
            if not session.get('user_id'):
                return jsonify({"error": "Unauthorized"}), 401
            
            user = self.auth_manager.get_user(session['user_id'])
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            
            if request.method == 'GET':
                # List wallets
                wallet_repo = WalletRepository(self.database_manager)
                wallets = wallet_repo.get_wallets_by_user(user.user_id)
                return jsonify([self._wallet_to_dict(w) for w in wallets])
            
            elif request.method == 'POST':
                # Create wallet (placeholder - would integrate with WalletGenerator)
                data = request.get_json()
                # TODO: Implement wallet creation
                return jsonify({"message": "Wallet creation not yet implemented"})
        
        @self.app.route('/api/compliance/check', methods=['POST'])
        def api_compliance_check():
            """Run compliance check."""
            if not session.get('user_id'):
                return jsonify({"error": "Unauthorized"}), 401
            
            user = self.auth_manager.get_user(session['user_id'])
            if not user:
                return jsonify({"error": "Unauthorized"}), 401
            
            # Check if user has compliance access
            if not user.role.has_permission('run_compliance'):
                return jsonify({"error": "Access denied"}), 403
            
            data = request.get_json()
            rule_id = data.get('rule_id')
            
            if rule_id:
                result = self.compliance_checker.check_compliance(rule_id, data.get('context'))
                return jsonify(asdict(result))
            else:
                results = self.compliance_checker.run_compliance_audit()
                return jsonify([asdict(r) for r in results])
    
    def _get_dashboard_data(self, user: User) -> Dict[str, Any]:
        """Get dashboard data for user."""
        try:
            wallet_repo = WalletRepository(self.database_manager)
            user_wallets = wallet_repo.get_wallets_by_user(user.user_id)
            
            # Get recent activity
            recent_events = self.audit_logger.get_audit_trail(
                user_id=user.user_id, limit=10
            )
            
            # Get basic metrics
            metrics = self.analytics_engine.get_user_metrics(user.user_id)
            
            return {
                "wallet_count": len(user_wallets),
                "recent_events": [self._event_to_dict(e) for e in recent_events],
                "metrics": metrics,
                "compliance_status": self._get_compliance_summary()
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}
    
    def _get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics data."""
        try:
            # Get system-wide metrics
            system_metrics = self.analytics_engine.get_system_metrics()
            
            # Get performance metrics
            performance_metrics = self.analytics_engine.get_performance_metrics()
            
            # Get security metrics
            security_metrics = self.analytics_engine.get_security_metrics()
            
            return {
                "system": system_metrics,
                "performance": performance_metrics,
                "security": security_metrics
            }
        except Exception as e:
            self.logger.error(f"Failed to get analytics data: {e}")
            return {"error": str(e)}
    
    def _get_admin_data(self) -> Dict[str, Any]:
        """Get admin panel data."""
        try:
            # Get all users
            users = self.auth_manager.get_all_users()
            
            # Get system health
            system_health = self._check_system_health()
            
            # Get compliance summary
            compliance_summary = self._get_compliance_summary()
            
            return {
                "users": [self._user_to_dict(u) for u in users],
                "system_health": system_health,
                "compliance": compliance_summary
            }
        except Exception as e:
            self.logger.error(f"Failed to get admin data: {e}")
            return {"error": str(e)}
    
    def _get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary."""
        try:
            results = self.compliance_checker.run_compliance_audit()
            
            summary = {
                "total_rules": len(results),
                "passed": len([r for r in results if r.status.value == "PASS"]),
                "failed": len([r for r in results if r.status.value == "FAIL"]),
                "warnings": len([r for r in results if r.status.value == "WARNING"]),
                "not_applicable": len([r for r in results if r.status.value == "NOT_APPLICABLE"])
            }
            
            return summary
        except Exception as e:
            self.logger.error(f"Failed to get compliance summary: {e}")
            return {"error": str(e)}
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health."""
        try:
            # Check database connectivity
            db_healthy = self.database_manager.test_connection()
            
            # Check file system access
            fs_healthy = self._check_file_system()
            
            # Check core functionality
            core_healthy = self._check_core_functionality()
            
            return {
                "database": db_healthy,
                "file_system": fs_healthy,
                "core_functionality": core_healthy,
                "overall": all([db_healthy, fs_healthy, core_healthy])
            }
        except Exception as e:
            self.logger.error(f"Failed to check system health: {e}")
            return {"error": str(e)}
    
    def _check_file_system(self) -> bool:
        """Check file system access."""
        try:
            # Test write access to temp directory
            test_file = Path("temp_test.txt")
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False
    
    def _check_core_functionality(self) -> bool:
        """Check core functionality."""
        try:
            # Basic checks - could be expanded
            return True
        except Exception:
            return False
    
    def _render_dashboard(self, data: Dict[str, Any], user: User) -> str:
        """Render dashboard HTML."""
        return self._get_dashboard_template().format(
            username=user.username,
            role=user.role.name,
            wallet_count=data.get('wallet_count', 0),
            recent_events=json.dumps(data.get('recent_events', [])),
            metrics=json.dumps(data.get('metrics', {})),
            compliance=json.dumps(data.get('compliance_status', {}))
        )
    
    def _render_login(self) -> str:
        """Render login HTML."""
        return self._get_login_template()
    
    def _render_wallets(self, wallets: List, user: User) -> str:
        """Render wallets page HTML."""
        return self._get_wallets_template().format(
            username=user.username,
            wallets=json.dumps([self._wallet_to_dict(w) for w in wallets])
        )
    
    def _render_analytics(self, data: Dict[str, Any], user: User) -> str:
        """Render analytics page HTML."""
        return self._get_analytics_template().format(
            username=user.username,
            analytics_data=json.dumps(data)
        )
    
    def _render_admin(self, data: Dict[str, Any], user: User) -> str:
        """Render admin panel HTML."""
        return self._get_admin_template().format(
            username=user.username,
            admin_data=json.dumps(data)
        )
    
    def _wallet_to_dict(self, wallet) -> Dict[str, Any]:
        """Convert wallet object to dictionary."""
        try:
            return {
                "id": wallet.id,
                "user_id": wallet.user_id,
                "address": wallet.address,
                "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
                "tags": wallet.tags or [],
                "encrypted": wallet.encrypted
            }
        except Exception:
            return {"error": "Failed to serialize wallet"}
    
    def _event_to_dict(self, event) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        try:
            return {
                "timestamp": event.timestamp.isoformat(),
                "action": event.action,
                "resource": event.resource,
                "level": event.level.value,
                "details": event.details
            }
        except Exception:
            return {"error": "Failed to serialize event"}
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert user object to dictionary."""
        try:
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        except Exception:
            return {"error": "Failed to serialize user"}
    
    def _get_dashboard_template(self) -> str:
        """Get dashboard HTML template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MetaWalletGen Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-wallet"></i> MetaWalletGen
                    </a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">
                            Welcome, {username} ({role})
                        </span>
                        <a class="nav-link" href="/wallets">Wallets</a>
                        <a class="nav-link" href="/analytics">Analytics</a>
                        <a class="nav-link" href="/admin">Admin</a>
                        <a class="nav-link" href="/logout">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid mt-4">
                <div class="row">
                    <div class="col-md-3">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Total Wallets</h5>
                                <h2 class="text-primary">{wallet_count}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-9">
                        <div class="card">
                            <div class="card-header">
                                <h5>Recent Activity</h5>
                            </div>
                            <div class="card-body">
                                <div id="activity-chart"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>System Metrics</h5>
                            </div>
                            <div class="card-body">
                                <div id="metrics-chart"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Compliance Status</h5>
                            </div>
                            <div class="card-body">
                                <div id="compliance-chart"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Initialize charts with data
                const data = {{
                    recent_events: {recent_events},
                    metrics: {metrics},
                    compliance: {compliance}
                }};
                
                // Activity chart
                const activityCtx = document.getElementById('activity-chart').getContext('2d');
                new Chart(activityCtx, {{
                    type: 'line',
                    data: {{
                        labels: data.recent_events.map(e => new Date(e.timestamp).toLocaleString()),
                        datasets: [{{
                            label: 'Activity Level',
                            data: data.recent_events.map((e, i) => i + 1),
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
                
                // Metrics chart
                const metricsCtx = document.getElementById('metrics-chart').getContext('2d');
                new Chart(metricsCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: Object.keys(data.metrics),
                        datasets: [{{
                            data: Object.values(data.metrics),
                            backgroundColor: [
                                '#FF6384',
                                '#36A2EB',
                                '#FFCE56',
                                '#4BC0C0'
                            ]
                        }}]
                    }}
                }});
                
                // Compliance chart
                const complianceCtx = document.getElementById('compliance-chart').getContext('2d');
                new Chart(complianceCtx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Passed', 'Failed', 'Warnings', 'N/A'],
                        datasets: [{{
                            label: 'Compliance Rules',
                            data: [
                                data.compliance.passed || 0,
                                data.compliance.failed || 0,
                                data.compliance.warnings || 0,
                                data.compliance.not_applicable || 0
                            ],
                            backgroundColor: [
                                '#28a745',
                                '#dc3545',
                                '#ffc107',
                                '#6c757d'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
    
    def _get_login_template(self) -> str:
        """Get login HTML template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MetaWalletGen Login</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                }}
                .login-card {{
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="row justify-content-center">
                    <div class="col-md-6 col-lg-4">
                        <div class="login-card p-5">
                            <div class="text-center mb-4">
                                <h2><i class="fas fa-wallet"></i> MetaWalletGen</h2>
                                <p class="text-muted">Enterprise Wallet Management</p>
                            </div>
                            
                            <form id="login-form">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" required>
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Login</button>
                            </form>
                            
                            <div id="error-message" class="alert alert-danger mt-3" style="display: none;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                document.getElementById('login-form').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    
                    try {{
                        const response = await fetch('/login', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{ username, password }})
                        }});
                        
                        const data = await response.json();
                        
                        if (data.success) {{
                            window.location.href = data.redirect;
                        }} else {{
                            const errorDiv = document.getElementById('error-message');
                            errorDiv.textContent = data.error;
                            errorDiv.style.display = 'block';
                        }}
                    }} catch (error) {{
                        console.error('Login error:', error);
                    }}
                }});
            </script>
        </body>
        </html>
        """
    
    def _get_wallets_template(self) -> str:
        """Get wallets page HTML template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wallets - MetaWalletGen</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-wallet"></i> MetaWalletGen
                    </a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">Welcome, {username}</span>
                        <a class="nav-link active" href="/wallets">Wallets</a>
                        <a class="nav-link" href="/analytics">Analytics</a>
                        <a class="nav-link" href="/admin">Admin</a>
                        <a class="nav-link" href="/logout">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid mt-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h2>My Wallets</h2>
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#create-wallet-modal">
                        <i class="fas fa-plus"></i> Create Wallet
                    </button>
                </div>
                
                <div class="row" id="wallets-container">
                    <!-- Wallets will be loaded here -->
                </div>
            </div>
            
            <!-- Create Wallet Modal -->
            <div class="modal fade" id="create-wallet-modal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Create New Wallet</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="create-wallet-form">
                                <div class="mb-3">
                                    <label for="wallet-tags" class="form-label">Tags (optional)</label>
                                    <input type="text" class="form-control" id="wallet-tags" placeholder="personal, savings, trading">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" form="create-wallet-form" class="btn btn-primary">Create Wallet</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                const wallets = {wallets};
                
                function renderWallets() {{
                    const container = document.getElementById('wallets-container');
                    container.innerHTML = '';
                    
                    wallets.forEach(wallet => {{
                        const walletCard = document.createElement('div');
                        walletCard.className = 'col-md-4 mb-3';
                        walletCard.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">Wallet Address</h6>
                                    <p class="card-text text-muted font-monospace small">{wallet.address}</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <small class="text-muted">Created: ${{new Date(wallet.created_at).toLocaleDateString()}}</small>
                                        <span class="badge bg-${{wallet.encrypted ? 'success' : 'warning'}}">
                                            ${{wallet.encrypted ? 'Encrypted' : 'Plain'}}
                                        </span>
                                    </div>
                                    ${{wallet.tags.length > 0 ? `<div class="mt-2">${{wallet.tags.map(tag => `<span class="badge bg-secondary me-1">${{tag}}</span>`).join('')}}</div>` : ''}}
                                </div>
                            </div>
                        `;
                        container.appendChild(walletCard);
                    }});
                }}
                
                // Load wallets on page load
                renderWallets();
                
                // Handle wallet creation
                document.getElementById('create-wallet-form').addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    // TODO: Implement wallet creation
                    alert('Wallet creation not yet implemented');
                }});
            </script>
        </body>
        </html>
        """
    
    def _get_analytics_template(self) -> str:
        """Get analytics page HTML template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analytics - MetaWalletGen</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-wallet"></i> MetaWalletGen
                    </a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">Welcome, {username}</span>
                        <a class="nav-link" href="/wallets">Wallets</a>
                        <a class="nav-link active" href="/analytics">Analytics</a>
                        <a class="nav-link" href="/admin">Admin</a>
                        <a class="nav-link" href="/logout">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid mt-4">
                <h2>System Analytics</h2>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>System Performance</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="performance-chart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Security Metrics</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="security-chart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>System Overview</h5>
                            </div>
                            <div class="card-body">
                                <div id="system-overview"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                const analyticsData = {analytics_data};
                
                // Performance chart
                const perfCtx = document.getElementById('performance-chart').getContext('2d');
                new Chart(perfCtx, {{
                    type: 'line',
                    data: {{
                        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                        datasets: [{{
                            label: 'Response Time (ms)',
                            data: [12, 19, 3, 5, 2, 3],
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});
                
                // Security chart
                const secCtx = document.getElementById('security-chart').getContext('2d');
                new Chart(secCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['Secure', 'Warnings', 'Issues'],
                        datasets: [{{
                            data: [80, 15, 5],
                            backgroundColor: [
                                '#28a745',
                                '#ffc107',
                                '#dc3545'
                            ]
                        }}]
                    }}
                }});
                
                // System overview
                document.getElementById('system-overview').innerHTML = `
                    <div class="row">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-primary">${{analyticsData.system?.total_wallets || 0}}</h4>
                                <p>Total Wallets</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-success">${{analyticsData.system?.active_users || 0}}</h4>
                                <p>Active Users</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-info">${{analyticsData.system?.encryption_rate || 0}}%</h4>
                                <p>Encryption Rate</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-warning">${{analyticsData.performance?.avg_response_time || 0}}ms</h4>
                                <p>Avg Response Time</p>
                            </div>
                        </div>
                    </div>
                `;
            </script>
        </body>
        </html>
        """
    
    def _get_admin_template(self) -> str:
        """Get admin panel HTML template."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel - MetaWalletGen</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">
                        <i class="fas fa-wallet"></i> MetaWalletGen
                    </a>
                    <div class="navbar-nav ms-auto">
                        <span class="navbar-text me-3">Welcome, {username} (Admin)</span>
                        <a class="nav-link" href="/wallets">Wallets</a>
                        <a class="nav-link" href="/analytics">Analytics</a>
                        <a class="nav-link active" href="/admin">Admin</a>
                        <a class="nav-link" href="/logout">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid mt-4">
                <h2>Admin Panel</h2>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>System Health</h5>
                            </div>
                            <div class="card-body">
                                <div id="system-health"></div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Compliance Status</h5>
                            </div>
                            <div class="card-body">
                                <div id="compliance-status"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5>User Management</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped">
                                        <thead>
                                            <tr>
                                                <th>Username</th>
                                                <th>Email</th>
                                                <th>Role</th>
                                                <th>Created</th>
                                                <th>Last Login</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="users-table">
                                            <!-- Users will be loaded here -->
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                const adminData = {admin_data};
                
                // Render system health
                const health = adminData.system_health || {{}};
                document.getElementById('system-health').innerHTML = `
                    <div class="row">
                        <div class="col-6">
                            <div class="text-center">
                                <h4 class="text-${{health.database ? 'success' : 'danger'}}">
                                    <i class="fas fa-${{health.database ? 'check' : 'times'}}"></i>
                                </h4>
                                <p>Database</p>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="text-center">
                                <h4 class="text-${{health.file_system ? 'success' : 'danger'}}">
                                    <i class="fas fa-${{health.file_system ? 'check' : 'times'}}"></i>
                                </h4>
                                <p>File System</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // Render compliance status
                const compliance = adminData.compliance || {{}};
                document.getElementById('compliance-status').innerHTML = `
                    <div class="row">
                        <div class="col-6">
                            <div class="text-center">
                                <h4 class="text-success">${{compliance.passed || 0}}</h4>
                                <p>Passed</p>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="text-center">
                                <h4 class="text-danger">${{compliance.failed || 0}}</h4>
                                <p>Failed</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // Render users table
                const users = adminData.users || [];
                const usersTable = document.getElementById('users-table');
                usersTable.innerHTML = users.map(user => `
                    <tr>
                        <td>${{user.username}}</td>
                        <td>${{user.email || 'N/A'}}</td>
                        <td><span class="badge bg-${{user.role === 'admin' ? 'danger' : 'primary'}}">${{user.role}}</span></td>
                        <td>${{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}}</td>
                        <td>${{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'N/A'}}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary">Edit</button>
                            <button class="btn btn-sm btn-outline-danger">Delete</button>
                        </td>
                    </tr>
                `).join('');
            </script>
        </body>
        </html>
        """
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the web dashboard."""
        try:
            self.logger.info(f"Starting web dashboard on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
        except Exception as e:
            self.logger.error(f"Failed to start web dashboard: {e}")
            raise
