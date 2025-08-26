"""
Enterprise Analytics and Reporting Engine

Provides advanced analytics, reporting, and business intelligence
features for MetaWalletGen CLI enterprise deployments.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import io
import base64

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsMetrics:
    """Analytics metrics container"""
    total_wallets: int
    active_wallets: int
    encrypted_wallets: int
    encryption_rate: float
    wallets_created_today: int
    wallets_created_week: int
    wallets_created_month: int
    average_wallets_per_user: float
    top_users: List[Dict[str, Any]]
    top_tags: List[Dict[str, Any]]
    wallet_growth_trend: List[Dict[str, Any]]
    security_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]

@dataclass
class ReportConfig:
    """Report configuration"""
    title: str
    description: str
    include_charts: bool = True
    include_tables: bool = True
    include_metrics: bool = True
    format: str = "html"  # html, pdf, json, csv
    date_range: Optional[tuple] = None
    filters: Dict[str, Any] = None

class AnalyticsEngine:
    """Core analytics engine for data processing and metrics calculation"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def calculate_basic_metrics(self, username: str = None) -> Dict[str, Any]:
        """Calculate basic wallet metrics"""
        if username:
            # User-specific metrics
            total_query = 'SELECT COUNT(*) as count FROM wallets WHERE created_by = ?'
            total_wallets = self.db_manager.execute_query(total_query, (username,))[0]['count']
            
            encrypted_query = 'SELECT COUNT(*) as count FROM wallets WHERE created_by = ? AND is_encrypted = 1'
            encrypted_wallets = self.db_manager.execute_query(encrypted_query, (username,))[0]['count']
            
            today_query = '''
                SELECT COUNT(*) as count FROM wallets 
                WHERE created_by = ? AND date(created_at) = date('now')
            '''
            wallets_today = self.db_manager.execute_query(today_query, (username,))[0]['count']
            
            week_query = '''
                SELECT COUNT(*) as count FROM wallets 
                WHERE created_by = ? AND created_at >= date('now', '-7 days')
            '''
            wallets_week = self.db_manager.execute_query(week_query, (username,))[0]['count']
            
            month_query = '''
                SELECT COUNT(*) as count FROM wallets 
                WHERE created_by = ? AND created_at >= date('now', '-30 days')
            '''
            wallets_month = self.db_manager.execute_query(month_query, (username,))[0]['count']
        else:
            # System-wide metrics
            total_wallets = self.db_manager.execute_query('SELECT COUNT(*) as count FROM wallets')[0]['count']
            encrypted_wallets = self.db_manager.execute_query('SELECT COUNT(*) as count FROM wallets WHERE is_encrypted = 1')[0]['count']
            
            wallets_today = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE date(created_at) = date("now")'
            )[0]['count']
            
            wallets_week = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE created_at >= date("now", "-7 days")'
            )[0]['count']
            
            wallets_month = self.db_manager.execute_query(
                'SELECT COUNT(*) as count FROM wallets WHERE created_at >= date("now", "-30 days")'
            )[0]['count']
        
        return {
            'total_wallets': total_wallets,
            'encrypted_wallets': encrypted_wallets,
            'encryption_rate': (encrypted_wallets / total_wallets * 100) if total_wallets > 0 else 0,
            'wallets_created_today': wallets_today,
            'wallets_created_week': wallets_week,
            'wallets_created_month': wallets_month
        }
    
    def calculate_user_metrics(self) -> List[Dict[str, Any]]:
        """Calculate metrics per user"""
        query = '''
            SELECT 
                created_by,
                COUNT(*) as wallet_count,
                SUM(CASE WHEN is_encrypted = 1 THEN 1 ELSE 0 END) as encrypted_count,
                AVG(CASE WHEN last_accessed IS NOT NULL THEN 
                    (julianday('now') - julianday(last_accessed)) ELSE NULL END) as avg_days_since_access
            FROM wallets 
            GROUP BY created_by 
            ORDER BY wallet_count DESC
        '''
        
        rows = self.db_manager.execute_query(query)
        return [
            {
                'username': row['created_by'],
                'wallet_count': row['wallet_count'],
                'encrypted_count': row['encrypted_count'],
                'encryption_rate': (row['encrypted_count'] / row['wallet_count'] * 100) if row['wallet_count'] > 0 else 0,
                'avg_days_since_access': row['avg_days_since_access'] or 0
            }
            for row in rows
        ]
    
    def calculate_tag_metrics(self) -> List[Dict[str, Any]]:
        """Calculate metrics per tag"""
        query = '''
            SELECT 
                wt.tag,
                COUNT(*) as wallet_count,
                AVG(CASE WHEN w.is_encrypted = 1 THEN 1.0 ELSE 0.0 END) as encryption_rate
            FROM wallet_tags wt
            JOIN wallets w ON wt.wallet_address = w.address
            GROUP BY wt.tag
            ORDER BY wallet_count DESC
        '''
        
        rows = self.db_manager.execute_query(query)
        return [
            {
                'tag': row['tag'],
                'wallet_count': row['wallet_count'],
                'encryption_rate': row['encryption_rate'] * 100
            }
            for row in rows
        ]
    
    def calculate_growth_trend(self, days: int = 30, username: str = None) -> List[Dict[str, Any]]:
        """Calculate wallet growth trend over time"""
        if username:
            base_query = '''
                SELECT 
                    date(created_at) as date,
                    COUNT(*) as count
                FROM wallets 
                WHERE created_by = ? AND created_at >= date('now', ?)
                GROUP BY date(created_at)
                ORDER BY date
            '''
            params = (username, f'-{days} days')
        else:
            base_query = '''
                SELECT 
                    date(created_at) as date,
                    COUNT(*) as count
                FROM wallets 
                WHERE created_at >= date('now', ?)
                GROUP BY date(created_at)
                ORDER BY date
            '''
            params = (f'-{days} days',)
        
        rows = self.db_manager.execute_query(base_query, params)
        
        # Fill in missing dates with zero counts
        date_counts = {row['date']: row['count'] for row in rows}
        trend_data = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            count = date_counts.get(date, 0)
            trend_data.append({
                'date': date,
                'count': count,
                'cumulative': sum(date_counts.get(d, 0) for d in date_counts if d <= date)
            })
        
        return list(reversed(trend_data))
    
    def calculate_security_metrics(self) -> Dict[str, Any]:
        """Calculate security-related metrics"""
        # Encryption statistics
        encryption_query = '''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_encrypted = 1 THEN 1 ELSE 0 END) as encrypted,
                SUM(CASE WHEN is_encrypted = 0 THEN 1 ELSE 0 END) as unencrypted
            FROM wallets
        '''
        encryption_stats = self.db_manager.execute_query(encryption_query)[0]
        
        # Access patterns
        access_query = '''
            SELECT 
                COUNT(*) as total_accesses,
                COUNT(DISTINCT wallet_address) as unique_wallets_accessed,
                COUNT(DISTINCT user_id) as unique_users
            FROM wallet_access_log
            WHERE timestamp >= datetime('now', '-30 days')
        '''
        access_stats = self.db_manager.execute_query(access_query)[0]
        
        # Failed access attempts (if we had such data)
        failed_attempts = 0  # Placeholder for future implementation
        
        return {
            'encryption': {
                'total_wallets': encryption_stats['total'],
                'encrypted_wallets': encryption_stats['encrypted'],
                'unencrypted_wallets': encryption_stats['unencrypted'],
                'encryption_rate': (encryption_stats['encrypted'] / encryption_stats['total'] * 100) if encryption_stats['total'] > 0 else 0
            },
            'access_patterns': {
                'total_accesses_30d': access_stats['total_accesses'],
                'unique_wallets_accessed': access_stats['unique_wallets_accessed'],
                'unique_users': access_stats['unique_users'],
                'avg_accesses_per_wallet': (access_stats['total_accesses'] / access_stats['unique_wallets_accessed']) if access_stats['unique_wallets_accessed'] > 0 else 0
            },
            'security_incidents': {
                'failed_attempts': failed_attempts,
                'risk_level': 'low' if failed_attempts == 0 else 'medium' if failed_attempts < 10 else 'high'
            }
        }
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance-related metrics"""
        # Database performance
        db_query = '''
            SELECT 
                COUNT(*) as total_wallets,
                COUNT(DISTINCT created_by) as unique_users,
                AVG(CAST((julianday('now') - julianday(created_at)) AS INTEGER)) as avg_wallet_age_days
            FROM wallets
        '''
        db_stats = self.db_manager.execute_query(db_query)[0]
        
        # Recent activity
        recent_query = '''
            SELECT 
                COUNT(*) as recent_wallets,
                AVG(CAST((julianday('now') - julianday(created_at)) AS INTEGER)) as avg_recent_age
            FROM wallets
            WHERE created_at >= datetime('now', '-7 days')
        '''
        recent_stats = self.db_manager.execute_query(recent_query)[0]
        
        return {
            'database': {
                'total_wallets': db_stats['total_wallets'],
                'unique_users': db_stats['unique_users'],
                'avg_wallet_age_days': db_stats['avg_wallet_age_days'] or 0
            },
            'recent_activity': {
                'wallets_last_7_days': recent_stats['recent_wallets'],
                'avg_age_recent_wallets': recent_stats['avg_recent_age'] or 0
            },
            'efficiency': {
                'wallets_per_user': (db_stats['total_wallets'] / db_stats['unique_users']) if db_stats['unique_users'] > 0 else 0,
                'activity_rate': (recent_stats['recent_wallets'] / db_stats['total_wallets'] * 100) if db_stats['total_wallets'] > 0 else 0
            }
        }
    
    def generate_comprehensive_metrics(self, username: str = None) -> AnalyticsMetrics:
        """Generate comprehensive analytics metrics"""
        basic_metrics = self.calculate_basic_metrics(username)
        user_metrics = self.calculate_user_metrics()
        tag_metrics = self.calculate_tag_metrics()
        growth_trend = self.calculate_growth_trend(username=username)
        security_metrics = self.calculate_security_metrics()
        performance_metrics = self.calculate_performance_metrics()
        
        # Calculate average wallets per user
        if username:
            avg_wallets_per_user = basic_metrics['total_wallets']
        else:
            total_users = len(user_metrics)
            avg_wallets_per_user = (basic_metrics['total_wallets'] / total_users) if total_users > 0 else 0
        
        return AnalyticsMetrics(
            total_wallets=basic_metrics['total_wallets'],
            active_wallets=basic_metrics['total_wallets'],  # Simplified for now
            encrypted_wallets=basic_metrics['encrypted_wallets'],
            encryption_rate=basic_metrics['encryption_rate'],
            wallets_created_today=basic_metrics['wallets_created_today'],
            wallets_created_week=basic_metrics['wallets_created_week'],
            wallets_created_month=basic_metrics['wallets_created_month'],
            average_wallets_per_user=avg_wallets_per_user,
            top_users=user_metrics[:10],
            top_tags=tag_metrics[:10],
            wallet_growth_trend=growth_trend,
            security_metrics=security_metrics,
            performance_metrics=performance_metrics
        )

class ReportGenerator:
    """Generate various types of reports and visualizations"""
    
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.setup_matplotlib()
    
    def setup_matplotlib(self) -> None:
        """Setup matplotlib for non-interactive backend"""
        plt.switch_backend('Agg')
        plt.style.use('default')
    
    def generate_html_report(self, config: ReportConfig, username: str = None) -> str:
        """Generate HTML report"""
        metrics = self.analytics_engine.generate_comprehensive_metrics(username)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .metric-card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #2196F3; }}
                .metric-label {{ color: #666; margin-top: 5px; }}
                .chart-container {{ margin: 20px 0; text-align: center; }}
                .table-container {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{config.title}</h1>
                <p>{config.description}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {f'<p><strong>User:</strong> {username}</p>' if username else ''}
            </div>
        """
        
        if config.include_metrics:
            html_content += self._generate_metrics_html(metrics)
        
        if config.include_charts:
            html_content += self._generate_charts_html(metrics)
        
        if config.include_tables:
            html_content += self._generate_tables_html(metrics)
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_metrics_html(self, metrics: AnalyticsMetrics) -> str:
        """Generate metrics section HTML"""
        return f"""
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{metrics.total_wallets:,}</div>
                <div class="metric-label">Total Wallets</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.encryption_rate:.1f}%</div>
                <div class="metric-label">Encryption Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.wallets_created_month:,}</div>
                <div class="metric-label">Wallets This Month</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.average_wallets_per_user:.1f}</div>
                <div class="metric-label">Avg per User</div>
            </div>
        </div>
        """
    
    def _generate_charts_html(self, metrics: AnalyticsMetrics) -> str:
        """Generate charts section HTML"""
        charts_html = "<div class='chart-container'>"
        
        # Growth trend chart
        if metrics.wallet_growth_trend:
            growth_chart = self._create_growth_chart(metrics.wallet_growth_trend)
            charts_html += f"""
            <h3>Wallet Growth Trend (Last 30 Days)</h3>
            <img src="data:image/png;base64,{growth_chart}" alt="Growth Trend Chart" style="max-width: 100%; height: auto;">
            """
        
        # User distribution chart
        if metrics.top_users:
            user_chart = self._create_user_distribution_chart(metrics.top_users)
            charts_html += f"""
            <h3>Top Users by Wallet Count</h3>
            <img src="data:image/png;base64,{user_chart}" alt="User Distribution Chart" style="max-width: 100%; height: auto;">
            """
        
        charts_html += "</div>"
        return charts_html
    
    def _generate_tables_html(self, metrics: AnalyticsMetrics) -> str:
        """Generate tables section HTML"""
        tables_html = "<div class='table-container'>"
        
        # Top users table
        if metrics.top_users:
            tables_html += """
            <h3>Top Users</h3>
            <table>
                <thead>
                    <tr><th>Username</th><th>Wallet Count</th><th>Encryption Rate</th><th>Last Access (Days)</th></tr>
                </thead>
                <tbody>
            """
            for user in metrics.top_users[:10]:
                tables_html += f"""
                <tr>
                    <td>{user['username']}</td>
                    <td>{user['wallet_count']:,}</td>
                    <td>{user['encryption_rate']:.1f}%</td>
                    <td>{user['avg_days_since_access']:.1f}</td>
                </tr>
                """
            tables_html += "</tbody></table>"
        
        # Top tags table
        if metrics.top_tags:
            tables_html += """
            <h3>Top Tags</h3>
            <table>
                <thead>
                    <tr><th>Tag</th><th>Wallet Count</th><th>Encryption Rate</th></tr>
                </thead>
                <tbody>
            """
            for tag in metrics.top_tags[:10]:
                tables_html += f"""
                <tr>
                    <td>{tag['tag']}</td>
                    <td>{tag['wallet_count']:,}</td>
                    <td>{tag['encryption_rate']:.1f}%</td>
                </tr>
                """
            tables_html += "</tbody></table>"
        
        tables_html += "</div>"
        return tables_html
    
    def _create_growth_chart(self, growth_data: List[Dict[str, Any]]) -> str:
        """Create growth trend chart and return as base64 string"""
        dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in growth_data]
        counts = [item['count'] for item in growth_data]
        cumulative = [item['cumulative'] for item in growth_data]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Daily counts
        ax1.plot(dates, counts, marker='o', linewidth=2, markersize=4)
        ax1.set_title('Daily Wallet Creation')
        ax1.set_ylabel('Wallets Created')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.grid(True, alpha=0.3)
        
        # Cumulative counts
        ax2.plot(dates, cumulative, marker='s', linewidth=2, markersize=4, color='orange')
        ax2.set_title('Cumulative Wallets')
        ax2.set_ylabel('Total Wallets')
        ax2.set_xlabel('Date')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def _create_user_distribution_chart(self, user_data: List[Dict[str, Any]]) -> str:
        """Create user distribution chart and return as base64 string"""
        usernames = [user['username'] for user in user_data]
        wallet_counts = [user['wallet_count'] for user in user_data]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(range(len(usernames)), wallet_counts, color='skyblue', alpha=0.7)
        
        ax.set_title('Top Users by Wallet Count')
        ax.set_xlabel('Users')
        ax.set_ylabel('Wallet Count')
        ax.set_xticks(range(len(usernames)))
        ax.set_xticklabels(usernames, rotation=45, ha='right')
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, count in zip(bars, wallet_counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count:,}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def generate_json_report(self, config: ReportConfig, username: str = None) -> str:
        """Generate JSON report"""
        metrics = self.analytics_engine.generate_comprehensive_metrics(username)
        return json.dumps(asdict(metrics), indent=2, default=str)
    
    def generate_csv_report(self, config: ReportConfig, username: str = None) -> str:
        """Generate CSV report"""
        metrics = self.analytics_engine.generate_comprehensive_metrics(username)
        
        # Convert to pandas DataFrame for CSV generation
        data = []
        
        # Basic metrics
        data.append(['Metric', 'Value'])
        data.append(['Total Wallets', metrics.total_wallets])
        data.append(['Encryption Rate', f"{metrics.encryption_rate:.1f}%"])
        data.append(['Wallets This Month', metrics.wallets_created_month])
        data.append(['Average per User', f"{metrics.average_wallets_per_user:.1f}"])
        
        # Top users
        data.append([])
        data.append(['Top Users'])
        data.append(['Username', 'Wallet Count', 'Encryption Rate', 'Last Access (Days)'])
        for user in metrics.top_users:
            data.append([
                user['username'],
                user['wallet_count'],
                f"{user['encryption_rate']:.1f}%",
                f"{user['avg_days_since_access']:.1f}"
            ])
        
        # Top tags
        data.append([])
        data.append(['Top Tags'])
        data.append(['Tag', 'Wallet Count', 'Encryption Rate'])
        for tag in metrics.top_tags:
            data.append([
                tag['tag'],
                tag['wallet_count'],
                f"{tag['encryption_rate']:.1f}%"
            ])
        
        # Convert to CSV string
        csv_content = ""
        for row in data:
            csv_content += ",".join(str(cell) for cell in row) + "\n"
        
        return csv_content
