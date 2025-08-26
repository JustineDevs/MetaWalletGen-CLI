"""
Enterprise Audit Logging and Compliance System

Provides comprehensive audit logging, compliance checking,
and regulatory reporting for enterprise deployments.
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import threading
from enum import Enum
import csv
import xml.etree.ElementTree as ET
import io

logger = logging.getLogger(__name__)

class AuditLevel(Enum):
    """Audit log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"

class ComplianceStandard(Enum):
    """Compliance standards"""
    SOX = "SOX"  # Sarbanes-Oxley
    PCI_DSS = "PCI_DSS"  # Payment Card Industry Data Security Standard
    HIPAA = "HIPAA"  # Health Insurance Portability and Accountability Act
    GDPR = "GDPR"  # General Data Protection Regulation
    SOC2 = "SOC2"  # Service Organization Control 2
    ISO27001 = "ISO27001"  # Information Security Management

@dataclass
class AuditEvent:
    """Audit event record"""
    id: Optional[int]
    timestamp: datetime
    level: AuditLevel
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    session_id: Optional[str]
    compliance_tags: List[str]
    risk_score: float
    hash: str

@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    id: Optional[int]
    name: str
    description: str
    standard: ComplianceStandard
    category: str
    severity: str  # low, medium, high, critical
    enabled: bool
    rule_definition: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self, db_path: str = "audit.db", log_file: str = "audit.log"):
        self.db_path = db_path
        self.log_file = log_file
        self.lock = threading.Lock()
        self.secret_key = self._load_or_generate_secret()
        
        self._init_database()
        self._setup_file_logging()
    
    def _load_or_generate_secret(self) -> str:
        """Load existing secret key or generate new one"""
        secret_file = Path("audit_secret.key")
        if secret_file.exists():
            return secret_file.read_text().strip()
        else:
            import secrets
            secret = secrets.token_urlsafe(32)
            secret_file.write_text(secret)
            return secret
    
    def _init_database(self) -> None:
        """Initialize audit database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audit_events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT NOT NULL,
                session_id TEXT,
                compliance_tags TEXT NOT NULL,
                risk_score REAL NOT NULL,
                hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Create compliance_rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                standard TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                rule_definition TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create compliance_violations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                violation_details TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                resolution_notes TEXT,
                resolved_at TEXT,
                resolved_by TEXT,
                FOREIGN KEY (rule_id) REFERENCES compliance_rules (id),
                FOREIGN KEY (event_id) REFERENCES audit_events (id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_type, resource_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_level ON audit_events(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_rule_standard ON compliance_rules(standard)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON compliance_violations(timestamp)')
        
        conn.commit()
        conn.close()
        
        # Create default compliance rules
        self._create_default_compliance_rules()
    
    def _setup_file_logging(self) -> None:
        """Setup file-based logging for audit events"""
        audit_handler = logging.FileHandler(self.log_file)
        audit_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(formatter)
        
        logger.addHandler(audit_handler)
        logger.setLevel(logging.INFO)
    
    def _create_default_compliance_rules(self) -> None:
        """Create default compliance rules"""
        default_rules = [
            {
                'name': 'SOX_Financial_Data_Access',
                'description': 'Monitor access to financial data and wallet information',
                'standard': ComplianceStandard.SOX,
                'category': 'Data Access',
                'severity': 'high',
                'rule_definition': {
                    'action_patterns': ['wallet:read', 'wallet:write', 'wallet:export'],
                    'resource_types': ['wallet', 'financial_data'],
                    'time_restrictions': {'business_hours_only': True},
                    'approval_required': True
                }
            },
            {
                'name': 'PCI_DSS_Encryption_Requirement',
                'description': 'Ensure all wallet data is encrypted',
                'standard': ComplianceStandard.PCI_DSS,
                'category': 'Data Protection',
                'severity': 'critical',
                'rule_definition': {
                    'encryption_required': True,
                    'encryption_algorithm': 'AES-256',
                    'key_rotation': True
                }
            },
            {
                'name': 'GDPR_Data_Retention',
                'description': 'Enforce data retention policies',
                'standard': ComplianceStandard.GDPR,
                'category': 'Data Retention',
                'severity': 'medium',
                'rule_definition': {
                    'retention_period_days': 2555,  # 7 years
                    'auto_deletion': True,
                    'consent_required': True
                }
            },
            {
                'name': 'SOC2_Access_Control',
                'description': 'Monitor and control user access to sensitive data',
                'standard': ComplianceStandard.SOC2,
                'category': 'Access Control',
                'severity': 'high',
                'rule_definition': {
                    'multi_factor_auth': True,
                    'session_timeout': 28800,  # 8 hours
                    'failed_attempts_limit': 5,
                    'lockout_duration': 1800  # 30 minutes
                }
            }
        ]
        
        for rule_data in default_rules:
            self.create_compliance_rule(
                name=rule_data['name'],
                description=rule_data['description'],
                standard=rule_data['standard'],
                category=rule_data['category'],
                severity=rule_data['severity'],
                rule_definition=rule_data['rule_definition']
            )
    
    def log_event(self, level: AuditLevel, user_id: str, action: str, 
                  resource_type: str, resource_id: str, details: Dict[str, Any],
                  ip_address: str = None, user_agent: str = None,
                  session_id: str = None, compliance_tags: List[str] = None) -> str:
        """Log an audit event"""
        with self.lock:
            timestamp = datetime.utcnow()
            compliance_tags = compliance_tags or []
            
            # Calculate risk score based on action and context
            risk_score = self._calculate_risk_score(level, action, resource_type, details)
            
            # Generate event hash for integrity
            event_hash = self._generate_event_hash(
                timestamp, user_id, action, resource_type, resource_id, details
            )
            
            # Create audit event
            event = AuditEvent(
                id=None,
                timestamp=timestamp,
                level=level,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
                session_id=session_id,
                compliance_tags=compliance_tags,
                risk_score=risk_score,
                hash=event_hash
            )
            
            # Save to database
            event_id = self._save_audit_event(event)
            
            # Log to file
            self._log_to_file(event)
            
            # Check compliance rules
            self._check_compliance_rules(event)
            
            logger.info(f"Audit event logged: {action} by {user_id} on {resource_type}:{resource_id}")
            
            return event_id
    
    def _calculate_risk_score(self, level: AuditLevel, action: str, 
                            resource_type: str, details: Dict[str, Any]) -> float:
        """Calculate risk score for audit event"""
        base_score = 0.0
        
        # Level-based scoring
        level_scores = {
            AuditLevel.DEBUG: 0.1,
            AuditLevel.INFO: 0.3,
            AuditLevel.WARNING: 0.6,
            AuditLevel.ERROR: 0.8,
            AuditLevel.CRITICAL: 1.0,
            AuditLevel.SECURITY: 0.9
        }
        base_score += level_scores.get(level, 0.5)
        
        # Action-based scoring
        high_risk_actions = ['wallet:delete', 'user:delete', 'role:delete', 'system:config']
        medium_risk_actions = ['wallet:write', 'wallet:export', 'user:write', 'role:write']
        
        if action in high_risk_actions:
            base_score += 0.4
        elif action in medium_risk_actions:
            base_score += 0.2
        
        # Resource-based scoring
        high_risk_resources = ['wallet', 'user', 'role', 'system']
        if resource_type in high_risk_resources:
            base_score += 0.2
        
        # Context-based scoring
        if details.get('sensitive_data', False):
            base_score += 0.3
        if details.get('bulk_operation', False):
            base_score += 0.2
        if details.get('after_hours', False):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _generate_event_hash(self, timestamp: datetime, user_id: str, action: str,
                           resource_type: str, resource_id: str, details: Dict[str, Any]) -> str:
        """Generate cryptographic hash for event integrity"""
        event_string = f"{timestamp.isoformat()}:{user_id}:{action}:{resource_type}:{resource_id}:{json.dumps(details, sort_keys=True)}"
        return hmac.new(
            self.secret_key.encode('utf-8'),
            event_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _save_audit_event(self, event: AuditEvent) -> str:
        """Save audit event to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_events (
                timestamp, level, user_id, action, resource_type, resource_id,
                ip_address, user_agent, details, session_id, compliance_tags,
                risk_score, hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.timestamp.isoformat(),
            event.level.value,
            event.user_id,
            event.action,
            event.resource_type,
            event.resource_id,
            event.ip_address,
            event.user_agent,
            json.dumps(event.details),
            event.session_id,
            json.dumps(event.compliance_tags),
            event.risk_score,
            event.hash,
            datetime.utcnow().isoformat()
        ))
        
        event_id = str(cursor.lastrowid)
        conn.commit()
        conn.close()
        
        return event_id
    
    def _log_to_file(self, event: AuditEvent) -> None:
        """Log audit event to file"""
        log_entry = {
            'timestamp': event.timestamp.isoformat(),
            'level': event.level.value,
            'user_id': event.user_id,
            'action': event.action,
            'resource_type': event.resource_type,
            'resource_id': event.resource_id,
            'ip_address': event.ip_address,
            'risk_score': event.risk_score,
            'compliance_tags': event.compliance_tags,
            'details': event.details
        }
        
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
    
    def _check_compliance_rules(self, event: AuditEvent) -> None:
        """Check event against compliance rules"""
        rules = self.get_compliance_rules(enabled_only=True)
        
        for rule in rules:
            if self._evaluate_compliance_rule(rule, event):
                self._record_compliance_violation(rule, event)
    
    def _evaluate_compliance_rule(self, rule: ComplianceRule, event: AuditEvent) -> bool:
        """Evaluate if event violates compliance rule"""
        rule_def = rule.rule_definition
        
        # Check action patterns
        if 'action_patterns' in rule_def:
            if not any(pattern in event.action for pattern in rule_def['action_patterns']):
                return False
        
        # Check resource types
        if 'resource_types' in rule_def:
            if event.resource_type not in rule_def['resource_types']:
                return False
        
        # Check time restrictions
        if 'business_hours_only' in rule_def and rule_def['business_hours_only']:
            hour = event.timestamp.hour
            if hour < 9 or hour > 17:  # 9 AM to 5 PM
                event.details['after_hours'] = True
                return True
        
        # Check encryption requirements
        if 'encryption_required' in rule_def and rule_def['encryption_required']:
            if not event.details.get('encrypted', False):
                return True
        
        # Check approval requirements
        if 'approval_required' in rule_def and rule_def['approval_required']:
            if not event.details.get('approved', False):
                return True
        
        return False
    
    def _record_compliance_violation(self, rule: ComplianceRule, event: AuditEvent) -> None:
        """Record compliance rule violation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO compliance_violations (
                rule_id, event_id, violation_details, severity, timestamp
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            rule.id,
            event.id,
            json.dumps({
                'rule_name': rule.name,
                'event_details': event.details,
                'violation_type': 'compliance_rule_violation'
            }),
            rule.severity,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.warning(f"Compliance violation detected: {rule.name} by {event.user_id}")
    
    def create_compliance_rule(self, name: str, description: str, standard: ComplianceStandard,
                              category: str, severity: str, rule_definition: Dict[str, Any]) -> str:
        """Create new compliance rule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO compliance_rules (
                name, description, standard, category, severity, enabled,
                rule_definition, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, description, standard.value, category, severity, True,
            json.dumps(rule_definition),
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        rule_id = str(cursor.lastrowid)
        conn.commit()
        conn.close()
        
        return rule_id
    
    def get_compliance_rules(self, enabled_only: bool = False) -> List[ComplianceRule]:
        """Get compliance rules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if enabled_only:
            cursor.execute('SELECT * FROM compliance_rules WHERE enabled = 1')
        else:
            cursor.execute('SELECT * FROM compliance_rules')
        
        rows = cursor.fetchall()
        conn.close()
        
        rules = []
        for row in rows:
            rule = ComplianceRule(
                id=row[0],
                name=row[1],
                description=row[2],
                standard=ComplianceStandard(row[3]),
                category=row[4],
                severity=row[5],
                enabled=bool(row[6]),
                rule_definition=json.loads(row[7]),
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9])
            )
            rules.append(rule)
        
        return rules
    
    def get_audit_events(self, user_id: str = None, action: str = None,
                         resource_type: str = None, start_date: datetime = None,
                         end_date: datetime = None, limit: int = 1000) -> List[AuditEvent]:
        """Get audit events with filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM audit_events WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if action:
            query += ' AND action = ?'
            params.append(action)
        
        if resource_type:
            query += ' AND resource_type = ?'
            params.append(resource_type)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            event = AuditEvent(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                level=AuditLevel(row[2]),
                user_id=row[3],
                action=row[4],
                resource_type=row[5],
                resource_id=row[6],
                ip_address=row[7],
                user_agent=row[8],
                details=json.loads(row[9]),
                session_id=row[10],
                compliance_tags=json.loads(row[11]),
                risk_score=row[12],
                hash=row[13]
            )
            events.append(event)
        
        return events
    
    def export_audit_report(self, format: str = "csv", start_date: datetime = None,
                           end_date: datetime = None) -> str:
        """Export audit report in specified format"""
        events = self.get_audit_events(start_date=start_date, end_date=end_date)
        
        if format.lower() == "csv":
            return self._export_csv(events)
        elif format.lower() == "json":
            return self._export_json(events)
        elif format.lower() == "xml":
            return self._export_xml(events)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self, events: List[AuditEvent]) -> str:
        """Export events to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp', 'Level', 'User ID', 'Action', 'Resource Type', 'Resource ID',
            'IP Address', 'Risk Score', 'Compliance Tags', 'Details'
        ])
        
        # Write data
        for event in events:
            writer.writerow([
                event.timestamp.isoformat(),
                event.level.value,
                event.user_id,
                event.action,
                event.resource_type,
                event.resource_id,
                event.ip_address or '',
                f"{event.risk_score:.3f}",
                ';'.join(event.compliance_tags),
                json.dumps(event.details)
            ])
        
        return output.getvalue()
    
    def _export_json(self, events: List[AuditEvent]) -> str:
        """Export events to JSON format"""
        return json.dumps([asdict(event) for event in events], indent=2, default=str)
    
    def _export_xml(self, events: List[AuditEvent]) -> str:
        """Export events to XML format"""
        root = ET.Element("audit_report")
        root.set("generated", datetime.utcnow().isoformat())
        root.set("total_events", str(len(events)))
        
        for event in events:
            event_elem = ET.SubElement(root, "event")
            event_elem.set("timestamp", event.timestamp.isoformat())
            event_elem.set("level", event.level.value)
            event_elem.set("user_id", event.user_id)
            event_elem.set("action", event.action)
            event_elem.set("resource_type", event.resource_type)
            event_elem.set("resource_id", event.resource_id)
            event_elem.set("risk_score", str(event.risk_score))
            
            if event.ip_address:
                event_elem.set("ip_address", event.ip_address)
            
            details_elem = ET.SubElement(event_elem, "details")
            for key, value in event.details.items():
                detail_elem = ET.SubElement(details_elem, key)
                detail_elem.text = str(value)
        
        return ET.tostring(root, encoding='unicode')

class ComplianceChecker:
    """Compliance checking and reporting system"""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    def run_compliance_check(self, standard: ComplianceStandard = None) -> Dict[str, Any]:
        """Run comprehensive compliance check"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'standard': standard.value if standard else 'all',
            'overall_status': 'compliant',
            'violations': [],
            'recommendations': [],
            'summary': {}
        }
        
        # Get compliance rules
        if standard:
            rules = [r for r in self.audit_logger.get_compliance_rules() if r.standard == standard]
        else:
            rules = self.audit_logger.get_compliance_rules()
        
        # Check each rule
        for rule in rules:
            rule_status = self._check_rule_compliance(rule)
            if rule_status['status'] == 'violated':
                results['overall_status'] = 'non_compliant'
                results['violations'].append(rule_status)
            
            if rule_status['recommendations']:
                results['recommendations'].extend(rule_status['recommendations'])
        
        # Generate summary
        results['summary'] = {
            'total_rules': len(rules),
            'compliant_rules': len([r for r in rules if r.enabled]),
            'violations_count': len(results['violations']),
            'risk_level': self._calculate_overall_risk_level(results['violations'])
        }
        
        return results
    
    def _check_rule_compliance(self, rule: ComplianceRule) -> Dict[str, Any]:
        """Check compliance for specific rule"""
        # This is a simplified check - in a real implementation,
        # you would analyze audit logs against the rule definition
        
        rule_status = {
            'rule_name': rule.name,
            'rule_description': rule.description,
            'standard': rule.standard.value,
            'category': rule.category,
            'severity': rule.severity,
            'status': 'compliant',  # Default assumption
            'violations': [],
            'recommendations': []
        }
        
        # Add rule-specific recommendations
        if rule.standard == ComplianceStandard.SOX:
            rule_status['recommendations'].append(
                "Ensure all financial data access is logged and reviewed regularly"
            )
        elif rule.standard == ComplianceStandard.PCI_DSS:
            rule_status['recommendations'].append(
                "Implement encryption for all wallet data at rest and in transit"
            )
        elif rule.standard == ComplianceStandard.GDPR:
            rule_status['recommendations'].append(
                "Implement data retention policies and user consent management"
            )
        
        return rule_status
    
    def _calculate_overall_risk_level(self, violations: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on violations"""
        if not violations:
            return 'low'
        
        severity_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        total_score = sum(severity_scores.get(v.get('severity', 'low'), 1) for v in violations)
        
        if total_score >= 8:
            return 'critical'
        elif total_score >= 5:
            return 'high'
        elif total_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def generate_compliance_report(self, standard: ComplianceStandard = None,
                                 format: str = "html") -> str:
        """Generate compliance report"""
        compliance_data = self.run_compliance_check(standard)
        
        if format.lower() == "html":
            return self._generate_html_report(compliance_data)
        elif format.lower() == "json":
            return json.dumps(compliance_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_report(self, compliance_data: Dict[str, Any]) -> str:
        """Generate HTML compliance report"""
        status_color = 'green' if compliance_data['overall_status'] == 'compliant' else 'red'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compliance Report - {compliance_data['standard']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .status {{ color: {status_color}; font-weight: bold; font-size: 1.2em; }}
                .violations {{ margin: 20px 0; }}
                .violation {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .recommendations {{ margin: 20px 0; }}
                .recommendation {{ background: #d1ecf1; padding: 10px; margin: 5px 0; border-radius: 5px; }}
                .summary {{ background: #e2e3e5; padding: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Compliance Report</h1>
                <p><strong>Standard:</strong> {compliance_data['standard']}</p>
                <p><strong>Generated:</strong> {compliance_data['timestamp']}</p>
                <p class="status">Status: {compliance_data['overall_status'].upper()}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Rules: {compliance_data['summary']['total_rules']}</p>
                <p>Compliant Rules: {compliance_data['summary']['compliant_rules']}</p>
                <p>Violations: {compliance_data['summary']['violations_count']}</p>
                <p>Risk Level: {compliance_data['summary']['risk_level'].upper()}</p>
            </div>
        """
        
        if compliance_data['violations']:
            html_content += """
            <div class="violations">
                <h2>Compliance Violations</h2>
            """
            for violation in compliance_data['violations']:
                html_content += f"""
                <div class="violation">
                    <h3>{violation['rule_name']}</h3>
                    <p><strong>Category:</strong> {violation['category']}</p>
                    <p><strong>Severity:</strong> {violation['severity']}</p>
                    <p><strong>Description:</strong> {violation['rule_description']}</p>
                </div>
                """
            html_content += "</div>"
        
        if compliance_data['recommendations']:
            html_content += """
            <div class="recommendations">
                <h2>Recommendations</h2>
            """
            for recommendation in compliance_data['recommendations']:
                html_content += f"""
                <div class="recommendation">
                    <p>{recommendation}</p>
                </div>
                """
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
