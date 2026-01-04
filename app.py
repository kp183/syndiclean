"""
LoanGuard Interest Validator - Main Streamlit Application

A professional banking tool for validating syndicated loan interest calculations
by extracting data from PDF notices and comparing calculated values against 
reported amounts.
"""

import streamlit as st
import io
import traceback
from typing import Optional
import pandas as pd
from datetime import datetime
from extractor import extract_loan_data, ExtractedData
from calculator import (
    calculate_interest_with_details, 
    validate_calculation_inputs, 
    format_currency, 
    format_percentage, 
    format_days,
    CalculationResult
)
from validator import (
    validate_interest_calculation,
    format_validation_for_display,
    can_perform_validation,
    ValidationResult
)
from input_validator import (
    perform_comprehensive_validation,
    format_validation_errors_for_display
)
from logging_config import (
    setup_logging,
    get_logger,
    LoggingContext,
    log_operation,
    log_validation_result,
    log_extraction_result,
    log_calculation_result,
    log_error
)

def validate_pdf_file(uploaded_file) -> bool:
    """
    Validate that the uploaded file is a PDF.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        bool: True if file is valid PDF, False otherwise
    """
    logger = get_logger()
    
    if uploaded_file is None:
        logger.debug("File validation failed: No file provided")
        return False
    
    try:
        # Check file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            logger.warning(f"File validation failed: Invalid extension for {uploaded_file.name}")
            return False
        
        # Check MIME type
        if uploaded_file.type != 'application/pdf':
            logger.warning(f"File validation failed: Invalid MIME type {uploaded_file.type} for {uploaded_file.name}")
            return False
        
        logger.info(f"File validation passed for {uploaded_file.name}")
        return True
        
    except Exception as e:
        log_error(e, "file_validation", uploaded_file.name if uploaded_file else None)
        return False

def setup_page_config():
    """Configure Streamlit page settings for professional banking appearance."""
    logger = get_logger()
    
    try:
        st.set_page_config(
            page_title="LoanGuard - Interest Validator",
            page_icon="🏦",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        logger.debug("Streamlit page configuration completed successfully")
        
    except Exception as e:
        log_error(e, "page_setup")
        # Continue execution even if page config fails
    
    # Add custom CSS for professional banking appearance
    st.markdown("""
    <style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Professional color scheme */
    :root {
        --primary-blue: #1f4e79;
        --secondary-blue: #2d5aa0;
        --success-green: #28a745;
        --warning-orange: #fd7e14;
        --error-red: #dc3545;
        --light-gray: #f8f9fa;
        --dark-gray: #6c757d;
    }
    
    /* Header styling */
    .banking-header {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .banking-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 300;
        letter-spacing: 1px;
    }
    
    .banking-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 300;
    }
    
    /* Section headers */
    .section-header {
        background: var(--light-gray);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-left: 4px solid var(--primary-blue);
        margin: 1.5rem 0 1rem 0;
    }
    
    .section-header h3 {
        margin: 0;
        color: var(--primary-blue);
        font-weight: 500;
    }
    
    /* Status cards */
    .status-card {
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 2px solid;
    }
    
    .status-card-pass {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-color: var(--success-green);
        color: #155724;
    }
    
    .status-card-fail {
        background: linear-gradient(135deg, #f8d7da 0%, #f1b0b7 100%);
        border-color: var(--error-red);
        color: #721c24;
    }
    
    .status-card h2 {
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }
    
    .status-card h3 {
        margin: 0.5rem 0;
        font-size: 1.3rem;
        font-weight: 400;
    }
    
    .status-card p {
        margin: 0;
        font-size: 1.1rem;
        line-height: 1.4;
    }
    
    /* Data tables */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Upload section */
    .upload-section {
        background: var(--light-gray);
        padding: 2rem;
        border-radius: 15px;
        border: 2px dashed var(--primary-blue);
        text-align: center;
        margin: 1rem 0;
    }
    
    /* Progress indicators */
    .progress-step {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .progress-step-completed {
        background: var(--success-green);
        color: white;
    }
    
    .progress-step-current {
        background: var(--secondary-blue);
        color: white;
    }
    
    .progress-step-pending {
        background: var(--light-gray);
        color: var(--dark-gray);
        border: 1px solid var(--dark-gray);
    }
    
    /* Loading indicators */
    .loading-container {
        text-align: center;
        padding: 2rem;
    }
    
    .loading-text {
        color: var(--primary-blue);
        font-size: 1.1rem;
        margin-top: 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--secondary-blue) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--light-gray);
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Footer */
    .app-footer {
        text-align: center;
        color: var(--dark-gray);
        font-size: 0.9rem;
        padding: 2rem 0;
        border-top: 1px solid #dee2e6;
        margin-top: 3rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .banking-header h1 {
            font-size: 2rem;
        }
        
        .banking-header p {
            font-size: 1rem;
        }
        
        .status-card {
            padding: 1.5rem;
        }
        
        .status-card h2 {
            font-size: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the professional banking header with progress indicator."""
    st.markdown("""
    <div class="banking-header">
        <h1>🏦 LoanGuard</h1>
        <p>Interest Payment Notice Validator</p>
        <p style="font-size: 0.9rem; margin-top: 1rem; opacity: 0.8;">
            Professional Banking Tool • Syndicated Loan Operations • Version 1.0
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_progress_indicator(current_step: str):
    """
    Render progress indicator showing current step in the validation process.
    
    Args:
        current_step: Current step in process ("upload", "extract", "calculate", "validate")
    """
    steps = {
        "upload": "📄 Upload PDF",
        "extract": "🔍 Extract Data", 
        "calculate": "🧮 Calculate Interest",
        "validate": "✅ Validate Results"
    }
    
    step_order = ["upload", "extract", "calculate", "validate"]
    current_index = step_order.index(current_step) if current_step in step_order else 0
    
    progress_html = "<div style='text-align: center; margin: 1.5rem 0;'>"
    
    for i, (step_key, step_label) in enumerate(steps.items()):
        if i < current_index:
            css_class = "progress-step-completed"
        elif i == current_index:
            css_class = "progress-step-current"
        else:
            css_class = "progress-step-pending"
        
        progress_html += f'<span class="progress-step {css_class}">{step_label}</span>'
        
        # Add arrow between steps (except after last step)
        if i < len(steps) - 1:
            progress_html += ' <span style="color: #6c757d; margin: 0 0.5rem;">→</span> '
    
    progress_html += "</div>"
    
    st.markdown(progress_html, unsafe_allow_html=True)

def create_sample_correct_pdf():
    """
    Create a sample PDF with correct interest calculation that will PASS validation.
    
    Returns:
        bytes: PDF content as bytes
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Sample data that will result in PASS
        story.append(Paragraph("INTEREST PAYMENT NOTICE", styles['Title']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Loan Information:", styles['Heading2']))
        story.append(Paragraph("Principal Amount: $1,000,000.00", styles['Normal']))
        story.append(Paragraph("Interest Rate: 5.25%", styles['Normal']))
        story.append(Paragraph("Start Date: 01/01/2024", styles['Normal']))
        story.append(Paragraph("End Date: 03/31/2024", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Calculate correct interest: $1,000,000 × 0.0525 × 90 ÷ 360 = $13,125.00
        story.append(Paragraph("Interest Calculation:", styles['Heading2']))
        story.append(Paragraph("Interest Amount: $13,125.00", styles['Normal']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("This notice contains correct interest calculation.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: create a simple text-based PDF using basic PDF structure
        return create_simple_pdf_correct()

def create_sample_incorrect_pdf():
    """
    Create a sample PDF with incorrect interest calculation that will FAIL validation.
    
    Returns:
        bytes: PDF content as bytes
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Sample data that will result in FAIL
        story.append(Paragraph("INTEREST PAYMENT NOTICE", styles['Title']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Loan Information:", styles['Heading2']))
        story.append(Paragraph("Principal Amount: $1,000,000.00", styles['Normal']))
        story.append(Paragraph("Interest Rate: 5.25%", styles['Normal']))
        story.append(Paragraph("Start Date: 01/01/2024", styles['Normal']))
        story.append(Paragraph("End Date: 03/31/2024", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Incorrect interest: should be $13,125.00 but showing $15,000.00
        story.append(Paragraph("Interest Calculation:", styles['Heading2']))
        story.append(Paragraph("Interest Amount: $15,000.00", styles['Normal']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("This notice contains incorrect interest calculation for testing.", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: create a simple text-based PDF using basic PDF structure
        return create_simple_pdf_incorrect()

def create_simple_pdf_correct():
    """
    Create a simple PDF with correct interest calculation using basic PDF structure.
    
    Returns:
        bytes: PDF content as bytes
    """
    pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 400
>>
stream
BT
/F1 16 Tf
50 750 Td
(INTEREST PAYMENT NOTICE) Tj
0 -40 Td
/F1 12 Tf
(Principal Amount: $1,000,000.00) Tj
0 -20 Td
(Interest Rate: 5.25%) Tj
0 -20 Td
(Start Date: 01/01/2024) Tj
0 -20 Td
(End Date: 03/31/2024) Tj
0 -40 Td
(Interest Amount: $13,125.00) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000724 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
801
%%EOF"""
    return pdf_content.encode('utf-8')

def create_simple_pdf_incorrect():
    """
    Create a simple PDF with incorrect interest calculation using basic PDF structure.
    
    Returns:
        bytes: PDF content as bytes
    """
    pdf_content = """%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 400
>>
stream
BT
/F1 16 Tf
50 750 Td
(INTEREST PAYMENT NOTICE) Tj
0 -40 Td
/F1 12 Tf
(Principal Amount: $1,000,000.00) Tj
0 -20 Td
(Interest Rate: 5.25%) Tj
0 -20 Td
(Start Date: 01/01/2024) Tj
0 -20 Td
(End Date: 03/31/2024) Tj
0 -40 Td
(Interest Amount: $15,000.00) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000724 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
801
%%EOF"""
    return pdf_content.encode('utf-8')

def render_upload_section():
    """Render the file upload section with enhanced styling and guidance."""
    st.markdown("""
    <div class="section-header">
        <h3>📄 Upload Interest Payment Notice</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Create three columns for better layout with sample PDFs
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <div class="upload-section">
            <h4 style="color: #1f4e79; margin-top: 0;">Select PDF Document</h4>
            <p style="color: #6c757d; margin-bottom: 1rem;">
                Upload a PDF file containing the interest payment notice to validate calculations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Select a PDF file containing the interest payment notice",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #2196f3;">
            <h5 style="color: #1565c0; margin-top: 0;">📋 Required Information</h5>
            <ul style="color: #1976d2; font-size: 0.9rem; margin-bottom: 0;">
                <li>Principal amount ($)</li>
                <li>Interest rate (%)</li>
                <li>Start & end dates</li>
                <li>Interest amount</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #28a745;">
            <h5 style="color: #155724; margin-top: 0;">📥 Sample PDFs for Testing</h5>
            <p style="color: #155724; font-size: 0.85rem; margin-bottom: 1rem;">
                Download sample files to test the validator:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample PDF download buttons
        sample_correct_pdf = create_sample_correct_pdf()
        sample_incorrect_pdf = create_sample_incorrect_pdf()
        
        st.download_button(
            label="📄 Download Sample (PASS)",
            data=sample_correct_pdf,
            file_name="sample_correct_interest_notice.pdf",
            mime="application/pdf",
            help="Download a sample PDF that will show PASS result",
            use_container_width=True
        )
        
        st.download_button(
            label="📄 Download Sample (FAIL)",
            data=sample_incorrect_pdf,
            file_name="sample_incorrect_interest_notice.pdf", 
            mime="application/pdf",
            help="Download a sample PDF that will show FAIL result",
            use_container_width=True
        )
    
    if uploaded_file is not None:
        if validate_pdf_file(uploaded_file):
            st.success(f"✅ **File uploaded successfully:** {uploaded_file.name}")
            
            # Show file details
            file_size = len(uploaded_file.getvalue()) / 1024  # KB
            st.info(f"📊 **File details:** {file_size:.1f} KB • Ready for processing")
            return uploaded_file
        else:
            st.error("❌ **Invalid file format.** Please upload a PDF file.")
            st.markdown("""
            <div style="background: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffc107; margin-top: 1rem;">
                <strong>💡 Tip:</strong> Ensure your file has a .pdf extension and is not corrupted.
            </div>
            """, unsafe_allow_html=True)
            return None
    
    return None

def render_extracted_data(extracted_data: ExtractedData):
    """
    Render extracted data in a professionally formatted table.
    
    Args:
        extracted_data: ExtractedData object containing extracted information
    """
    st.markdown("""
    <div class="section-header">
        <h3>📋 Extracted Financial Data</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if any data was extracted
    has_data = any([
        extracted_data.principal_amount is not None,
        extracted_data.interest_rate is not None,
        extracted_data.start_date is not None,
        extracted_data.end_date is not None,
        extracted_data.notice_interest_amount is not None
    ])
    
    if not has_data:
        st.markdown("""
        <div style="background: #fff3cd; padding: 2rem; border-radius: 10px; border-left: 4px solid #ffc107; text-align: center;">
            <h4 style="color: #856404; margin-top: 0;">⚠️ No Financial Data Found</h4>
            <p style="color: #856404; margin-bottom: 0;">
                No financial data could be extracted from the PDF. Please ensure the document contains clearly marked financial information.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create data for display table with enhanced formatting
    data_rows = []
    
    # Helper function to create status indicator
    def get_status_indicator(value, field_name):
        if value is not None:
            return "✅ Extracted"
        else:
            return "❌ Missing"
    
    if extracted_data.principal_amount is not None:
        data_rows.append({
            "Field": "💰 Principal Amount",
            "Value": f"${extracted_data.principal_amount:,.2f}",
            "Status": get_status_indicator(extracted_data.principal_amount, "principal")
        })
    else:
        data_rows.append({
            "Field": "💰 Principal Amount",
            "Value": "Not found",
            "Status": get_status_indicator(None, "principal")
        })
    
    if extracted_data.interest_rate is not None:
        data_rows.append({
            "Field": "📈 Interest Rate",
            "Value": f"{extracted_data.interest_rate * 100:.4f}%",
            "Status": get_status_indicator(extracted_data.interest_rate, "rate")
        })
    else:
        data_rows.append({
            "Field": "📈 Interest Rate",
            "Value": "Not found",
            "Status": get_status_indicator(None, "rate")
        })
    
    if extracted_data.start_date is not None:
        data_rows.append({
            "Field": "📅 Start Date",
            "Value": extracted_data.start_date.strftime("%m/%d/%Y"),
            "Status": get_status_indicator(extracted_data.start_date, "start_date")
        })
    else:
        data_rows.append({
            "Field": "📅 Start Date",
            "Value": "Not found",
            "Status": get_status_indicator(None, "start_date")
        })
    
    if extracted_data.end_date is not None:
        data_rows.append({
            "Field": "📅 End Date",
            "Value": extracted_data.end_date.strftime("%m/%d/%Y"),
            "Status": get_status_indicator(extracted_data.end_date, "end_date")
        })
    else:
        data_rows.append({
            "Field": "📅 End Date",
            "Value": "Not found",
            "Status": get_status_indicator(None, "end_date")
        })
    
    if extracted_data.notice_interest_amount is not None:
        data_rows.append({
            "Field": "💵 Notice Interest Amount",
            "Value": f"${extracted_data.notice_interest_amount:,.2f}",
            "Status": get_status_indicator(extracted_data.notice_interest_amount, "interest")
        })
    else:
        data_rows.append({
            "Field": "💵 Notice Interest Amount",
            "Value": "Not found",
            "Status": get_status_indicator(None, "interest")
        })
    
    # Display as a formatted table
    df = pd.DataFrame(data_rows)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Field": st.column_config.TextColumn("Field", width="medium"),
            "Value": st.column_config.TextColumn("Value", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )
    
    # Show extraction confidence if available
    if extracted_data.extraction_confidence:
        with st.expander("📊 Extraction Confidence Details", expanded=False):
            st.markdown("**Data extraction confidence levels:**")
            
            confidence_data = []
            for field, confidence in extracted_data.extraction_confidence.items():
                confidence_level = "High" if confidence >= 0.8 else "Medium" if confidence >= 0.6 else "Low"
                confidence_color = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.6 else "🔴"
                
                confidence_data.append({
                    "Field": field.replace('_', ' ').title(),
                    "Confidence": f"{confidence * 100:.0f}%",
                    "Level": f"{confidence_color} {confidence_level}"
                })
            
            if confidence_data:
                conf_df = pd.DataFrame(confidence_data)
                st.dataframe(conf_df, use_container_width=True, hide_index=True)
                
                # Show guidance for low confidence extractions
                low_confidence = [item for item in confidence_data if "Low" in item["Level"]]
                if low_confidence:
                    st.warning("⚠️ **Low confidence extractions detected.** Please review these values carefully.")
    
    # Add summary statistics
    extracted_count = sum(1 for row in data_rows if "✅" in row["Status"])
    total_fields = len(data_rows)
    
    if extracted_count == total_fields:
        st.success(f"🎉 **Complete extraction:** All {total_fields} required fields found")
    else:
        missing_count = total_fields - extracted_count
        st.warning(f"⚠️ **Partial extraction:** {extracted_count}/{total_fields} fields found ({missing_count} missing)")

@log_operation("pdf_extraction")
def process_pdf_extraction(uploaded_file):
    """
    Process PDF file and extract financial data with comprehensive validation.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        ExtractedData or None: Extracted data object or None if extraction failed
    """
    logger = get_logger()
    file_name = uploaded_file.name if uploaded_file else "unknown"
    
    try:
        with LoggingContext(logger, loan_file_name=file_name):
            with st.spinner("🔍 Extracting financial data from PDF..."):
                logger.info(f"Starting PDF extraction for {file_name}")
                
                # Extract data from PDF
                extracted_data = extract_loan_data(uploaded_file)
                
                # Log extraction results
                log_extraction_result(extracted_data, file_name)
                
                # Perform comprehensive validation
                logger.info("Performing comprehensive data validation")
                validation_result = perform_comprehensive_validation(extracted_data)
                
                # Display validation results
                display_validation_results(validation_result)
                
                # Return data even if there are warnings (but not if there are errors)
                if validation_result.is_valid:
                    logger.info(f"PDF extraction completed successfully for {file_name}")
                    return extracted_data
                else:
                    logger.warning(f"PDF extraction failed validation for {file_name}")
                    return None
                    
    except Exception as e:
        log_error(e, "pdf_extraction", file_name)
        
        st.error(f"❌ **Extraction Error**")
        st.error(f"Failed to extract data from PDF: {str(e)}")
        
        # Provide helpful guidance
        st.markdown("""
        **Possible solutions:**
        - Ensure the PDF contains clearly marked financial information
        - Check that amounts are formatted with dollar signs (e.g., $1,234,567.89)
        - Verify that interest rates include percentage symbols (e.g., 5.25%)
        - Confirm that dates are in standard formats (e.g., 12/31/2023)
        """)
        
        # Log detailed error information for debugging
        logger.error(f"Detailed error trace for {file_name}: {traceback.format_exc()}")
        
        return None


def display_validation_results(validation_result):
    """
    Display comprehensive validation results in the UI.
    
    Args:
        validation_result: ValidationResult object containing validation details
    """
    display_info = format_validation_errors_for_display(validation_result)
    
    # Show validation summary
    if display_info['has_errors']:
        st.error(f"❌ **Data Validation Failed** - {display_info['summary']}")
        
        # Display errors
        st.markdown("**❌ Errors that must be fixed:**")
        for error in display_info['errors']:
            st.error(f"• **{error['field'].replace('_', ' ').title()}**: {error['message']}")
            if error['suggestion']:
                st.info(f"  💡 {error['suggestion']}")
        
        # Show guidance
        st.markdown("""
        **Next steps:**
        - Review the PDF to ensure all required information is present and clearly marked
        - Check that dates are in MM/DD/YYYY format
        - Verify that amounts include dollar signs and percentages include % symbols
        - Ensure the document is not corrupted or password-protected
        """)
        
    elif display_info['has_warnings']:
        st.warning(f"⚠️ **Data Validation Warnings** - {display_info['summary']}")
        
        # Display warnings in an expander
        with st.expander("⚠️ View Validation Warnings"):
            st.markdown("**⚠️ Warnings (validation can continue):**")
            for warning in display_info['warnings']:
                st.warning(f"• **{warning['field'].replace('_', ' ').title()}**: {warning['message']}")
                if warning['suggestion']:
                    st.info(f"  💡 {warning['suggestion']}")
        
        st.success("✅ **Validation passed** - Proceeding with warnings noted above")
        
    else:
        st.success(f"✅ **Data Validation Passed** - {display_info['summary']}")

@log_operation("interest_calculation")
def render_calculation_results(extracted_data: ExtractedData):
    """
    Render interest calculation results with enhanced styling and progress indicators.
    
    Args:
        extracted_data: ExtractedData object containing extracted information
    """
    logger = get_logger()
    
    st.markdown("""
    <div class="section-header">
        <h3>🧮 Interest Calculation</h3>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Validate that we have all required data for calculation
        validation_errors = validate_calculation_inputs(
            extracted_data.principal_amount,
            extracted_data.interest_rate,
            extracted_data.start_date,
            extracted_data.end_date
        )
        
        if validation_errors:
            logger.warning(f"Calculation validation failed: {validation_errors}")
            
            st.markdown("""
            <div style="background: #f8d7da; padding: 2rem; border-radius: 10px; border-left: 4px solid #dc3545;">
                <h4 style="color: #721c24; margin-top: 0;">❌ Cannot Perform Calculation</h4>
                <p style="color: #721c24; margin-bottom: 1rem;">Missing or invalid data prevents interest calculation:</p>
            </div>
            """, unsafe_allow_html=True)
            
            for field, error in validation_errors.items():
                st.error(f"• **{field.replace('_', ' ').title()}**: {error}")
            
            st.markdown("""
            <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; margin-top: 1rem;">
                <strong>💡 Next Steps:</strong>
                <ul style="margin-bottom: 0;">
                    <li>Ensure all required fields are extracted from the PDF</li>
                    <li>Verify that dates are in the correct format</li>
                    <li>Check that amounts and rates are reasonable values</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            return None
        
        # Show calculation progress
        with st.spinner("🔢 Calculating expected interest using banking formula..."):
            logger.info("Starting interest calculation")
            
            calculation_result = calculate_interest_with_details(
                extracted_data.principal_amount,
                extracted_data.interest_rate,
                extracted_data.start_date,
                extracted_data.end_date
            )
            
            # Log calculation results
            log_calculation_result(calculation_result)
        
        # Display calculation success
        st.success("✅ **Interest calculation completed successfully**")
        logger.info(f"Interest calculation successful: ${calculation_result.expected_interest:.2f}")
        
        # Create enhanced calculation summary
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Main calculation table
            calc_data = [
                {
                    "Component": "💰 Principal Amount",
                    "Value": format_currency(calculation_result.calculation_details['principal'])
                },
                {
                    "Component": "📈 Annual Interest Rate",
                    "Value": format_percentage(calculation_result.calculation_details['annual_rate'])
                },
                {
                    "Component": "📅 Start Date",
                    "Value": calculation_result.calculation_details['start_date']
                },
                {
                    "Component": "📅 End Date",
                    "Value": calculation_result.calculation_details['end_date']
                },
                {
                    "Component": "⏱️ Days in Period",
                    "Value": format_days(calculation_result.days_calculated)
                },
                {
                    "Component": "🏦 Day Count Convention",
                    "Value": calculation_result.calculation_details['day_count_convention']
                }
            ]
            
            calc_df = pd.DataFrame(calc_data)
            st.dataframe(
                calc_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Component": st.column_config.TextColumn("Component", width="medium"),
                    "Value": st.column_config.TextColumn("Value", width="medium")
                }
            )
        
        with col2:
            # Expected interest result card
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%); 
                        padding: 2rem; border-radius: 15px; text-align: center; 
                        border: 2px solid #28a745; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h4 style="color: #155724; margin-top: 0;">💵 Expected Interest</h4>
                <h2 style="color: #155724; margin: 0.5rem 0; font-size: 2rem; font-weight: 600;">
                    {format_currency(calculation_result.expected_interest)}
                </h2>
                <p style="color: #155724; margin-bottom: 0; font-size: 0.9rem;">
                    Based on banking formula
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show detailed calculation steps in an enhanced expander
        with st.expander("📊 Detailed Calculation Steps", expanded=False):
            st.markdown(f"**🔢 Formula Used:** `{calculation_result.formula_used}`")
            
            st.markdown("**📋 Step-by-step calculation:**")
            steps = calculation_result.calculation_details['calculation_steps']
            
            for i, (step_key, step_value) in enumerate(steps.items(), 1):
                st.markdown(f"**Step {i}:** {step_value}")
            
            # Add visual formula breakdown
            st.markdown("---")
            st.markdown("**🎯 Formula Breakdown:**")
            
            principal = calculation_result.calculation_details['principal']
            rate = calculation_result.calculation_details['annual_rate']
            days = calculation_result.days_calculated
            
            st.markdown(f"""
            ```
            Interest = Principal × Rate × Days ÷ 360
            Interest = ${principal:,.2f} × {rate:.6f} × {days} ÷ 360
            Interest = ${calculation_result.expected_interest:,.2f}
            ```
            """)
        
        return calculation_result
        
    except Exception as e:
        log_error(e, "interest_calculation")
        
        st.markdown("""
        <div style="background: #f8d7da; padding: 2rem; border-radius: 10px; border-left: 4px solid #dc3545;">
            <h4 style="color: #721c24; margin-top: 0;">❌ Calculation Error</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.error(f"Failed to calculate interest: {str(e)}")
        
        # Provide helpful guidance
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; margin-top: 1rem;">
            <strong>💡 Possible Solutions:</strong>
            <ul style="margin-bottom: 0;">
                <li>Verify that all extracted data is valid</li>
                <li>Check that dates are in the correct format</li>
                <li>Ensure principal amount and interest rate are reasonable values</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Log detailed error for debugging
        logger.error(f"Detailed calculation error: {traceback.format_exc()}")
        
        return None


@log_operation("validation")
def render_validation_results(extracted_data: ExtractedData, calculation_result: CalculationResult):
    """
    Render validation results with enhanced professional styling.
    
    Args:
        extracted_data: ExtractedData object containing notice interest amount
        calculation_result: CalculationResult object containing calculated interest
    """
    logger = get_logger()
    
    st.markdown("""
    <div class="section-header">
        <h3>🔍 Validation Results</h3>
        <p style="color: #6c757d; margin-top: 0.5rem; font-style: italic;">Final pre-send validation before lender notification</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Check if validation can be performed
        can_validate, issues = can_perform_validation(extracted_data, calculation_result)
        
        if not can_validate:
            logger.warning(f"Validation cannot be performed: {issues}")
            
            st.markdown("""
            <div style="background: #fff3cd; padding: 2rem; border-radius: 10px; border-left: 4px solid #ffc107;">
                <h4 style="color: #856404; margin-top: 0;">⚠️ Cannot Perform Validation</h4>
                <p style="color: #856404; margin-bottom: 1rem;">The following issues prevent validation:</p>
            </div>
            """, unsafe_allow_html=True)
            
            for issue in issues:
                st.warning(f"• {issue}")
            
            # Show expected interest if available
            if calculation_result and calculation_result.expected_interest is not None:
                st.info(f"**Expected Interest:** {format_currency(calculation_result.expected_interest)}")
            return
        
        # Perform validation with progress indicator
        with st.spinner("🔍 Validating interest calculation against notice amount..."):
            logger.info("Starting validation process")
            
            validation_result = validate_interest_calculation(extracted_data, calculation_result)
            
            # Log validation results
            log_validation_result(validation_result)
        
        # Get display formatting
        display_info = format_validation_for_display(validation_result)
        
        # Create enhanced comparison table
        st.markdown("**📊 Calculation Comparison:**")
        
        comparison_data = [
            {
                "Source": "🧮 **Expected (Calculated)**",
                "Amount": f"**{format_currency(validation_result.expected_amount)}**",
                "Details": "Based on extracted data and banking formula"
            },
            {
                "Source": "📄 **Notice (PDF)**",
                "Amount": f"**{format_currency(validation_result.notice_amount)}**",
                "Details": "Amount shown in the interest payment notice"
            },
            {
                "Source": "📏 **Difference**",
                "Amount": f"**{format_currency(validation_result.difference_amount)}**",
                "Details": f"Percentage difference: {validation_result.percentage_difference:.2f}%"
            },
            {
                "Source": "⚖️ **Tolerance**",
                "Amount": f"**{format_currency(validation_result.tolerance_used)}**",
                "Details": "Acceptable variance ($1 or 0.01%, whichever is larger)"
            }
        ]
        
        comp_df = pd.DataFrame(comparison_data)
        st.dataframe(
            comp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Source": st.column_config.TextColumn("Source", width="medium"),
                "Amount": st.column_config.TextColumn("Amount", width="small"),
                "Details": st.column_config.TextColumn("Details", width="large")
            }
        )
        
        # Display enhanced status card based on validation result
        if validation_result.status == "PASS":
            logger.info(f"Validation PASSED - difference: ${validation_result.difference_amount:.2f}")
            
            st.markdown(f"""
            <div class="status-card status-card-pass">
                <h2>{display_info['status_icon']} {display_info['status_text']}</h2>
                <h3>{display_info['status_message']}</h3>
                <p>{display_info['explanation']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.success(f"✅ **Validation successful** - Difference of {format_currency(validation_result.difference_amount)} is  within  acceptable  tolerance of {format_currency(validation_result.tolerance_used)}")
            
            # Show additional success details
            st.markdown("""
            <div style="background: #d1ecf1; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #17a2b8; margin-top: 1rem;">
                <strong>🎉 Ready to Proceed:</strong>
                <ul style="margin-bottom: 0;">
                    <li>The notice is ready to be sent to lenders</li>
                    <li>Interest calculation is accurate within banking standards</li>
                    <li>No further action required</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            logger.warning(f"Validation FAILED - difference: ${validation_result.difference_amount:.2f}")
            
            st.markdown(f"""
            <div class="status-card status-card-fail">
                <h2>🔴 Validation Failed – Interest Mismatch Detected</h2>
                <h3>{display_info['status_message']}</h3>
                <p>The notice shows ${validation_result.difference_amount:,.2f} more than expected. This difference exceeds the acceptable tolerance of ${validation_result.tolerance_used:,.2f}. Please review the interest calculation in the notice.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show direction of difference with enhanced styling
            if validation_result.notice_amount > validation_result.expected_amount:
                st.markdown(f"""
                <div style="background: #f8d7da; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #dc3545; margin-top: 1rem;">
                    <strong>📈 Notice Amount is Higher:</strong> The notice shows <strong>${validation_result.difference_amount:,.2f} more</strong> than expected
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f8d7da; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #dc3545; margin-top: 1rem;">
                    <strong>📉 Notice Amount is Lower:</strong> The notice shows <strong>${validation_result.difference_amount:,.2f} less</strong> than expected
                </div>
                """, unsafe_allow_html=True)
        
        # Show recommendations in an enhanced format
        if display_info['recommendations']:
            with st.expander("💡 Recommendations & Next Steps", expanded=validation_result.status == "FAIL"):
                st.markdown("**Recommended actions:**")
                for i, recommendation in enumerate(display_info['recommendations'], 1):
                    st.markdown(f"{i}. {recommendation}")
                
                if validation_result.status == "FAIL":
                    st.markdown("---")
                    st.markdown("**🔧 Troubleshooting Steps:**")
                    st.markdown("""
                    - Double-check all extracted values for accuracy
                    - Verify the PDF contains the correct interest calculation
                    - Consider if there are special terms or adjustments not captured
                    - Review the calculation methodology with the loan documentation
                    """)
        
    except Exception as e:
        log_error(e, "validation")
        
        st.markdown("""
        <div style="background: #f8d7da; padding: 2rem; border-radius: 10px; border-left: 4px solid #dc3545;">
            <h4 style="color: #721c24; margin-top: 0;">❌ Validation Error</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.error(f"Failed to perform validation: {str(e)}")
        
        # Provide helpful guidance
        st.markdown("""
        <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; margin-top: 1rem;">
            <strong>💡 Possible Solutions:</strong>
            <ul style="margin-bottom: 0;">
                <li>Ensure all required data was extracted successfully</li>
                <li>Verify that the interest calculation completed without errors</li>
                <li>Check that the PDF contains a valid interest amount for comparison</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Log detailed error for debugging
        logger.error(f"Detailed validation error: {traceback.format_exc()}")


def main():
    """Main application entry point with enhanced user experience and comprehensive logging."""
    # Initialize logging
    logger = setup_logging(
        log_level="INFO",
        log_file="logs/loanguard.log"
    )
    
    logger.info("LoanGuard application starting")
    
    try:
        setup_page_config()
        render_header()
        
        # Initialize session state for progress tracking
        if 'current_step' not in st.session_state:
            st.session_state.current_step = 'upload'
            logger.debug("Initialized session state")
        
        # Generate unique session ID for logging context
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"New session started: {st.session_state.session_id}")
        
        # Create main container for better layout
        with st.container():
            with LoggingContext(logger, user_session=st.session_state.session_id):
                # Show progress indicator
                render_progress_indicator(st.session_state.current_step)
                
                # File upload section
                uploaded_file = render_upload_section()
                
                if uploaded_file is not None:
                    logger.info(f"File uploaded: {uploaded_file.name}")
                    st.session_state.current_step = 'extract'
                    render_progress_indicator(st.session_state.current_step)
                    
                    # Add spacing
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Process PDF extraction
                    extracted_data = process_pdf_extraction(uploaded_file)
                    
                    if extracted_data is not None:
                        # Display extracted data
                        render_extracted_data(extracted_data)
                        
                        st.session_state.current_step = 'calculate'
                        render_progress_indicator(st.session_state.current_step)
                        
                        # Add spacing
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Perform interest calculation
                        calculation_result = render_calculation_results(extracted_data)
                        
                        if calculation_result is not None:
                            st.session_state.current_step = 'validate'
                            render_progress_indicator(st.session_state.current_step)
                            
                            # Add spacing
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Display validation results
                            render_validation_results(extracted_data, calculation_result)
                            
                            logger.info(f"Complete workflow finished for {uploaded_file.name}")
                        else:
                            # Reset progress if calculation failed
                            st.session_state.current_step = 'extract'
                            logger.warning("Calculation failed, resetting to extract step")
                    else:
                        # Reset progress if extraction failed
                        st.session_state.current_step = 'upload'
                        logger.warning("Extraction failed, resetting to upload step")
                else:
                    # Reset progress when no file
                    st.session_state.current_step = 'upload'
                    
                    # Show placeholders when no file is uploaded
                    st.markdown("""
                    <div class="section-header">
                        <h3>📋 Extracted Financial Data</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; text-align: center; border: 2px dashed #dee2e6;">
                        <h4 style="color: #6c757d; margin-top: 0;">📄 Upload Required</h4>
                        <p style="color: #6c757d; margin-bottom: 0;">
                            Upload a PDF file to see extracted financial data here.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class="section-header">
                        <h3>🧮 Interest Calculation</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; text-align: center; border: 2px dashed #dee2e6;">
                        <h4 style="color: #6c757d; margin-top: 0;">🔢 Calculation Pending</h4>
                        <p style="color: #6c757d; margin-bottom: 0;">
                            Interest calculation details will appear here after data extraction.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class="section-header">
                        <h3>🔍 Validation Results</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; text-align: center; border: 2px dashed #dee2e6;">
                        <h4 style="color: #6c757d; margin-top: 0;">⏳ Validation Awaiting</h4>
                        <p style="color: #6c757d; margin-bottom: 0;">
                            Validation results will appear here after processing.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Enhanced footer
                st.markdown("---")
                st.markdown("""
                <div class="app-footer">
                    <strong>🏦 LoanGuard v1.0</strong> • Internal Banking Tool for Interest Validation<br>
                    <small>Syndicated Loan Operations • Professional Grade Validation • Secure Processing</small>
                </div>
                """, unsafe_allow_html=True)
    
    except Exception as e:
        log_error(e, "main_application")
        
        st.error("❌ **Application Error**")
        st.error("An unexpected error occurred. Please refresh the page and try again.")
        
        # Show error details in expander for debugging
        with st.expander("🔧 Technical Details", expanded=False):
            st.code(str(e))
            st.markdown("**Error Type:** " + type(e).__name__)
        
        logger.critical(f"Critical application error: {traceback.format_exc()}")
    
    finally:
        logger.info("LoanGuard application session ended")

if __name__ == "__main__":
    main()