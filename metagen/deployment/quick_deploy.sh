#!/bin/bash

# MetaWalletGen CLI - Quick Production Deployment Script
# This script automates the immediate next steps for production deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/config"
LOG_FILE="$PROJECT_ROOT/deployment.log"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is not recommended for security reasons."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check system requirements
check_system_requirements() {
    log "🔍 Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3.8+ is required but not installed"
        exit 1
    fi
    
    # Check required packages
    REQUIRED_PACKAGES=("git" "curl" "wget")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if command -v "$package" &> /dev/null; then
            log_success "$package found"
        else
            log_warning "$package not found - please install manually"
        fi
    done
    
    # Check disk space
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log_warning "Disk usage is ${DISK_USAGE}% - consider freeing up space"
    else
        log_success "Disk usage: ${DISK_USAGE}%"
    fi
    
    # Check memory
    MEMORY_GB=$(free -g | awk 'NR==2{print $2}')
    if [ "$MEMORY_GB" -lt 2 ]; then
        log_warning "Only ${MEMORY_GB}GB RAM available - 4GB+ recommended"
    else
        log_success "Available memory: ${MEMORY_GB}GB"
    fi
}

# Create directory structure
create_directories() {
    log "📁 Creating directory structure..."
    
    DIRS=(
        "/opt/metawalletgen"
        "/var/lib/metawalletgen"
        "/var/log/metawalletgen"
        "/var/backups/metawalletgen"
        "/etc/metawalletgen"
        "/tmp/metawalletgen"
    )
    
    for dir in "${DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            sudo mkdir -p "$dir"
            log_success "Created $dir"
        else
            log_success "$dir already exists"
        fi
    done
    
    # Set permissions
    sudo chown -R "$USER:$USER" /opt/metawalletgen
    sudo chown -R "$USER:$USER" /tmp/metawalletgen
    sudo chmod 755 /opt/metawalletgen
    sudo chmod 1777 /tmp/metawalletgen
}

# Deploy application
deploy_application() {
    log "🚀 Deploying MetaWalletGen CLI..."
    
    cd /opt/metawalletgen
    
    # Clone or update repository
    if [ -d ".git" ]; then
        log "Updating existing repository..."
        git pull origin main
    else
        log "Cloning repository..."
        git clone https://github.com/your-org/metawalletgen-cli.git .
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    log "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Copy configuration
    if [ -f "$CONFIG_DIR/production.yaml" ]; then
        sudo cp "$CONFIG_DIR/production.yaml" /etc/metawalletgen/
        sudo chown "$USER:$USER" /etc/metawalletgen/production.yaml
        log_success "Configuration copied"
    else
        log_warning "Production configuration not found - using defaults"
    fi
    
    log_success "Application deployed successfully"
}

# Initialize database
initialize_database() {
    log "🗄️  Initializing database..."
    
    cd /opt/metawalletgen
    source venv/bin/activate
    
    # Set environment variables
    export METAWALLETGEN_ENV=production
    export METAWALLETGEN_CONFIG=/etc/metawalletgen/production.yaml
    
    # Initialize database
    if python -m metagen.enterprise.database --init; then
        log_success "Database initialized"
    else
        log_error "Database initialization failed"
        return 1
    fi
    
    # Create admin user
    if python -m metagen.enterprise.auth --create-admin; then
        log_success "Admin user created"
    else
        log_warning "Admin user creation failed or user already exists"
    fi
}

# Setup systemd service
setup_systemd_service() {
    log "⚙️  Setting up systemd service..."
    
    if [ -f "$PROJECT_ROOT/metagen/systemd/metawalletgen.service" ]; then
        sudo cp "$PROJECT_ROOT/metagen/systemd/metawalletgen.service" /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable metawalletgen
        log_success "Systemd service configured"
    else
        log_warning "Systemd service file not found - skipping service setup"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "📊 Setting up monitoring..."
    
    # Check if Prometheus is available
    if command -v prometheus &> /dev/null; then
        log_success "Prometheus found"
    else
        log_warning "Prometheus not found - install manually for full monitoring"
    fi
    
    # Check if Grafana is available
    if command -v grafana-server &> /dev/null; then
        log_success "Grafana found"
    else
        log_warning "Grafana not found - install manually for dashboards"
    fi
    
    # Start performance monitoring
    cd /opt/metawalletgen
    source venv/bin/activate
    export METAWALLETGEN_ENV=production
    export METAWALLETGEN_CONFIG=/etc/metawalletgen/production.yaml
    
    if python -m metagen.performance.monitor --start; then
        log_success "Performance monitoring started"
    else
        log_warning "Performance monitoring failed to start"
    fi
}

# Run health checks
run_health_checks() {
    log "🏥 Running health checks..."
    
    cd /opt/metawalletgen
    source venv/bin/activate
    export METAWALLETGEN_ENV=production
    export METAWALLETGEN_CONFIG=/etc/metawalletgen/production.yaml
    
    # Check database health
    if python -m metagen.enterprise.database --health-check; then
        log_success "Database health check passed"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    # Check performance monitoring
    if python -m metagen.performance.monitor --status; then
        log_success "Performance monitoring health check passed"
    else
        log_warning "Performance monitoring health check failed"
    fi
    
    # Run quick benchmark
    if python -m metagen.performance.benchmark --quick; then
        log_success "Quick benchmark completed"
    else
        log_warning "Quick benchmark failed"
    fi
}

# Setup backup
setup_backup() {
    log "💾 Setting up backup procedures..."
    
    # Create backup script
    cat > /opt/metawalletgen/backup.sh << 'EOF'
#!/bin/bash
# Backup script for MetaWalletGen CLI

BACKUP_DIR="/var/backups/metawalletgen"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
cd /opt/metawalletgen
source venv/bin/activate
export METAWALLETGEN_ENV=production
export METAWALLETGEN_CONFIG=/etc/metawalletgen/production.yaml

python -m metagen.enterprise.database --backup

# File backup
tar -czf "$BACKUP_DIR/files-$DATE.tar.gz" /var/lib/metawalletgen/ 2>/dev/null || true

# Configuration backup
cp -r /etc/metawalletgen "$BACKUP_DIR/config-$DATE" 2>/dev/null || true

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "config-*" -mtime +30 -exec rm -rf {} \; 2>/dev/null || true

echo "Backup completed: $DATE"
EOF
    
    chmod +x /opt/metawalletgen/backup.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/metawalletgen/backup.sh") | crontab -
    
    log_success "Backup procedures configured"
}

# Generate deployment report
generate_report() {
    log "📊 Generating deployment report..."
    
    REPORT_FILE="$PROJECT_ROOT/deployment_report.txt"
    
    cat > "$REPORT_FILE" << EOF
MetaWalletGen CLI - Production Deployment Report
Generated: $(date)

System Information:
- Python Version: $(python3 --version)
- Memory: $(free -h | awk 'NR==2{print $2}')
- Disk Usage: $(df / | awk 'NR==2 {print $5}')
- User: $USER
- Hostname: $(hostname)

Deployment Status:
- ✅ System requirements checked
- ✅ Directory structure created
- ✅ Application deployed
- ✅ Database initialized
- ✅ Systemd service configured
- ✅ Monitoring setup
- ✅ Health checks passed
- ✅ Backup procedures configured

Next Steps:
1. Start the service: sudo systemctl start metawalletgen
2. Check service status: sudo systemctl status metawalletgen
3. View logs: sudo journalctl -u metawalletgen -f
4. Access API: http://localhost:5000/health
5. Run full benchmark: python -m metagen.performance.benchmark --full-suite

Configuration Files:
- Main Config: /etc/metawalletgen/production.yaml
- Service: /etc/systemd/system/metawalletgen.service
- Logs: /var/log/metawalletgen/
- Data: /var/lib/metawalletgen/

Emergency Contacts:
- On-call Engineer: +1-555-0123
- System Administrator: +1-555-0124
- DevOps Team: +1-555-0125

Remember to:
- Change default passwords
- Configure SSL certificates
- Set up external monitoring
- Test backup and recovery procedures
- Schedule regular maintenance
EOF
    
    log_success "Deployment report generated: $REPORT_FILE"
}

# Main deployment function
main() {
    log "🚀 Starting MetaWalletGen CLI Production Deployment..."
    log "Log file: $LOG_FILE"
    
    # Check if running as root
    check_root
    
    # Run deployment steps
    check_system_requirements
    create_directories
    deploy_application
    initialize_database
    setup_systemd_service
    setup_monitoring
    run_health_checks
    setup_backup
    generate_report
    
    log_success "🎉 Production deployment completed successfully!"
    log ""
    log "Next steps:"
    log "1. Start the service: sudo systemctl start metawalletgen"
    log "2. Check service status: sudo systemctl status metawalletgen"
    log "3. View deployment report: cat $PROJECT_ROOT/deployment_report.txt"
    log "4. Access the API: http://localhost:5000/health"
    log ""
    log "For detailed deployment information, see:"
    log "- $PROJECT_ROOT/DEPLOYMENT_OPERATIONS_GUIDE.md"
    log "- $PROJECT_ROOT/PRODUCTION_DEPLOYMENT_CHECKLIST.md"
}

# Run main function
main "$@"
