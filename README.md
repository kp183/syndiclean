# 🏦 LoanGuard Interest Validator

**Professional Banking Tool for Syndicated Loan Operations**

LoanGuard is a Streamlit-based web application that validates syndicated loan interest calculations by extracting data from PDF notices and comparing calculated values against reported amounts. Built for loan agents to prevent calculation errors before notices are sent to lenders.

## 🎯 Key Features

- **📄 PDF Data Extraction**: Automatically extracts financial data from Interest Payment Notice PDFs
- **🧮 Banking-Grade Calculations**: Uses standard 360-day banking convention for interest calculations
- **✅ Smart Validation**: Compares calculated vs. notice amounts with appropriate tolerance
- **🎨 Professional UI**: Clean, banker-style interface with clear pass/fail indicators
- **🔒 Error Handling**: Comprehensive validation and user-friendly error messages
- **📊 Detailed Reports**: Professional comparison tables and calculation breakdowns

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kp183/syndiclean.git
   cd syndiclean
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - Navigate to `http://localhost:8501`
   - Upload a PDF interest payment notice
   - Watch LoanGuard validate the calculations!

## 📋 How It Works

### 1. Upload PDF Document
- Drag and drop or select PDF files up to 50MB
- Supports standard Interest Payment Notice formats

### 2. Automatic Data Extraction
- **Principal Amount**: Loan amount in dollars
- **Interest Rate**: Annual percentage rate
- **Date Range**: Interest calculation period
- **Notice Amount**: Interest amount from the PDF

### 3. Banking Formula Calculation
```
Interest = Principal × Rate × Days / 360
```
Uses standard banking day-count convention

### 4. Validation Results
- **✅ PASS**: Green card when amounts match within tolerance
- **❌ FAIL**: Red card when difference exceeds acceptable limits
- **📊 Detailed Analysis**: Shows exact differences and recommendations

## 🏗️ Project Structure

```
syndiclean/
├── 📄 app.py                    # Main Streamlit application
├── 📄 extractor.py              # PDF data extraction engine
├── 📄 calculator.py             # Interest calculation formulas
├── 📄 validator.py              # Validation logic and comparison
├── 📄 input_validator.py        # Input validation and error handling
├── 📄 logging_config.py         # Structured logging configuration
├── 📄 requirements.txt          # Python dependencies
├── 📁 .streamlit/              # Streamlit configuration
├── 📄 sample_correct_interest_notice.pdf    # Demo file (PASS)
├── 📄 sample_incorrect_interest_notice.pdf  # Demo file (FAIL)
└── 📁 tests/                   # Test files
```

## 🧪 Testing

Run the included tests to verify functionality:

```bash
# Run all tests
python -m pytest

# Run specific tests
python -m pytest test_app.py
python -m pytest test_calculator.py
python -m pytest test_extractor.py
python -m pytest test_validator.py
```

## 📊 Demo Data

Try the included sample PDFs:
- `sample_correct_interest_notice.pdf` - Shows ✅ PASS validation
- `sample_incorrect_interest_notice.pdf` - Shows ❌ FAIL validation

## 🔧 Configuration

### Streamlit Configuration
Located in `.streamlit/config.toml`:
- Professional banking theme
- Security settings
- Upload limits and server configuration

## 🏦 Banking Features

### Professional Grade Validation
- **Tolerance Calculation**: $1 or 0.01% (whichever is larger)
- **360-Day Convention**: Standard banking day count
- **Currency Formatting**: Professional financial display
- **Error Recovery**: Graceful handling of malformed PDFs

### Executive Interface
- Clean, professional design suitable for banking executives
- Large visual indicators for quick decision making
- Banking-appropriate language and recommendations
- "Final pre-send validation before lender notification"

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Production Deployment
See `DEPLOYMENT.md` for comprehensive deployment instructions including:
- Docker deployment
- Streamlit Cloud deployment
- Production server setup
- Security considerations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Built With

- **[Streamlit](https://streamlit.io/)** - Web application framework
- **[pdfplumber](https://github.com/jsvine/pdfplumber)** - PDF text extraction
- **[pandas](https://pandas.pydata.org/)** - Data manipulation
- **[pytest](https://pytest.org/)** - Testing framework

---

**LoanGuard v1.0** - Professional Banking Tool for Interest Validation  
*Syndicated Loan Operations • Production-Ready • Secure Processing*