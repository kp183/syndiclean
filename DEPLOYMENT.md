# LoanGuard Interest Validator - Deployment Guide

## Overview

LoanGuard is a Streamlit-based web application for validating syndicated loan interest calculations. This guide provides comprehensive instructions for deploying the application in various environments.

## System Requirements

### Minimum Requirements
- Python 3.8 or higher
- 2GB RAM
- 1GB available disk space
- Internet connection for initial setup

### Recommended Requirements
- Python 3.9 or higher
- 4GB RAM
- 2GB available disk space
- Stable internet connection

## Pre-Deployment Checklist

### 1. Environment Verification
```bash
# Check Python version
python --version

# Verify pip is available
pip --version

# Check available disk space
df -h  # Linux/Mac
dir   # Windows
```

### 2. Dependencies Installation
```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list | grep streamlit
pip list | grep pdfplumber
```

### 3. Application Structure Verification
Ensure the following files are present:
```
loanguard/
├── app.py                          # Main application
├── extractor.py                    # PDF data extraction
├── calculator.py                   # Interest calculations
├── validator.py                    # Validation logic
├── input_validator.py              # Input validation
├── logging_config.py               # Logging configuration
├── requirements.txt                # Dependencies
├── DEPLOYMENT.md                   # This file
├── README.md                       # Application documentation
├── logs/                           # Log directory
├── sample_*.pdf                    # Sample PDF files
└── test_*.py                       # Test files
```

## Deployment Options

### Option 1: Local Development Deployment

#### Quick Start
```bash
# Clone or download the application
cd loanguard

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

#### Configuration
- Default port: 8501
- Access URL: http://localhost:8501
- Logs location: ./logs/loanguard.log

### Option 2: Streamlit Cloud Deployment

#### Prerequisites
- GitHub repository with the application code
- Streamlit Cloud account (https://streamlit.io/cloud)

#### Steps
1. **Prepare Repository**
   ```bash
   # Ensure all files are committed
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Visit https://streamlit.io/cloud
   - Connect your GitHub account
   - Select the repository
   - Set main file: `app.py`
   - Deploy

3. **Configuration**
   - Python version: 3.9
   - Requirements file: requirements.txt
   - Main file path: app.py

### Option 3: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Docker Commands
```bash
# Build the image
docker build -t loanguard:latest .

# Run the container
docker run -p 8501:8501 -v $(pwd)/logs:/app/logs loanguard:latest

# Run with environment variables
docker run -p 8501:8501 \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  loanguard:latest
```

### Option 4: Production Server Deployment

#### Using Gunicorn (Not recommended for Streamlit)
Streamlit applications should use the built-in server or be deployed on platforms designed for Streamlit apps.

#### Recommended Production Setup
```bash
# Install additional production dependencies
pip install streamlit[production]

# Run with production settings
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=true
```

## Configuration Options

### Environment Variables
```bash
# Logging configuration
export LOG_LEVEL=INFO
export LOG_FILE=logs/loanguard.log

# Application settings
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
```

### Streamlit Configuration File (.streamlit/config.toml)
```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f4e79"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## Security Considerations

### 1. File Upload Security
- PDF files are processed in memory
- No permanent file storage on server
- File type validation enforced
- File size limits recommended (add to Streamlit config)

### 2. Data Privacy
- No sensitive data is permanently stored
- Logs contain only operational information
- Session data is temporary and cleared on refresh

### 3. Network Security
- Use HTTPS in production
- Configure appropriate firewall rules
- Consider VPN access for internal banking tools

### 4. Access Control
- Implement authentication if required
- Consider IP whitelisting for internal tools
- Monitor access logs

## Monitoring and Maintenance

### 1. Log Monitoring
```bash
# View real-time logs
tail -f logs/loanguard.log

# Search for errors
grep "ERROR" logs/loanguard.log

# Monitor application health
curl http://localhost:8501/_stcore/health
```

### 2. Performance Monitoring
- Monitor memory usage during PDF processing
- Track response times for large files
- Monitor disk space for log files

### 3. Regular Maintenance
- Update dependencies monthly
- Review and rotate log files
- Test with new PDF formats
- Backup configuration files

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check Python version
python --version

# Verify dependencies
pip check

# Check port availability
netstat -an | grep 8501  # Linux/Mac
netstat -an | findstr 8501  # Windows
```

#### 2. PDF Processing Errors
- Verify pdfplumber installation
- Check PDF file integrity
- Review extraction logs
- Test with sample PDFs

#### 3. Memory Issues
- Monitor memory usage during large file processing
- Consider increasing container memory limits
- Implement file size restrictions

#### 4. Permission Errors
```bash
# Fix log directory permissions
chmod 755 logs/
chmod 644 logs/loanguard.log

# Fix application file permissions
chmod 644 *.py
chmod 755 app.py
```

### Error Codes and Solutions

| Error Code | Description | Solution |
|------------|-------------|----------|
| ModuleNotFoundError | Missing dependency | Run `pip install -r requirements.txt` |
| PermissionError | File access denied | Check file/directory permissions |
| AddressAlreadyInUse | Port 8501 in use | Use different port or stop conflicting service |
| PDFSyntaxError | Corrupted PDF | Verify PDF file integrity |

## Testing Deployment

### 1. Functional Testing
```bash
# Run unit tests
python -m pytest test_*.py

# Run integration tests
python test_integration.py

# Run complete workflow test
python test_complete_workflow.py
```

### 2. Load Testing
- Test with multiple concurrent users
- Process various PDF file sizes
- Monitor resource usage

### 3. Sample Data Testing
```bash
# Test with provided sample PDFs
streamlit run app.py
# Upload each sample_*.pdf file and verify results
```

## Backup and Recovery

### 1. Configuration Backup
```bash
# Backup configuration files
tar -czf loanguard-config-$(date +%Y%m%d).tar.gz \
  requirements.txt \
  .streamlit/ \
  DEPLOYMENT.md \
  README.md
```

### 2. Log Backup
```bash
# Rotate and backup logs
cp logs/loanguard.log logs/loanguard-$(date +%Y%m%d).log
> logs/loanguard.log
```

### 3. Recovery Procedures
1. Restore configuration files
2. Reinstall dependencies
3. Verify application startup
4. Test core functionality

## Support and Maintenance

### Contact Information
- **Technical Support**: [Your IT Department]
- **Application Owner**: [Loan Operations Team]
- **Emergency Contact**: [24/7 Support Line]

### Documentation Updates
- Review deployment guide quarterly
- Update after major application changes
- Maintain version history

### Version Management
- Tag releases in version control
- Maintain changelog
- Document breaking changes

## Appendix

### A. Sample Streamlit Commands
```bash
# Basic run
streamlit run app.py

# Custom port
streamlit run app.py --server.port 8502

# Headless mode
streamlit run app.py --server.headless true

# Debug mode
streamlit run app.py --logger.level debug
```

### B. Health Check Endpoints
- Application health: `http://localhost:8501/_stcore/health`
- Metrics: `http://localhost:8501/_stcore/metrics`

### C. Log File Locations
- Application logs: `./logs/loanguard.log`
- Streamlit logs: `~/.streamlit/logs/`
- System logs: `/var/log/` (Linux) or Event Viewer (Windows)

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Next Review**: April 2026