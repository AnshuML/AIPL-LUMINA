"""
Cloud Sample Data for AIPL Chatbot
This provides sample data for cloud deployment when no documents are available
"""

import os
from datetime import datetime
from models import get_db, Document, DocumentChunk, init_database

def create_cloud_sample_data():
    """Create sample data for cloud deployment."""
    try:
        db = next(get_db())
        
        # Check if we already have documents
        existing_docs = db.query(Document).count()
        if existing_docs > 0:
            print(f"✅ Found {existing_docs} existing documents, skipping sample data creation")
            return True
        
        print("🌐 Creating sample data for cloud deployment...")
        
        # Sample documents data
        sample_documents = [
            {
                "filename": "hr_policies.pdf",
                "original_filename": "hr_policies.pdf",
                "department": "HR",
                "content": """
                HR POLICIES AND PROCEDURES
                
                ATTENDANCE POLICY:
                - Working hours: 9:00 AM to 6:00 PM (Monday to Friday)
                - Late arrival grace period: 15 minutes
                - Late arrivals beyond grace period require prior approval
                - Attendance is tracked through biometric system
                
                LEAVE POLICY:
                - Casual Leave: 12 days per year
                - Sick Leave: 6 days per year
                - Earned Leave: 21 days per year
                - Leave applications must be submitted 24 hours in advance
                - Emergency leave can be applied for same day
                
                HOLIDAY POLICY:
                - Sundays are weekly off
                - National holidays as declared by government
                - Compensatory leave for working on holidays
                
                OUTDOOR DUTY:
                - OD requests must be approved by immediate supervisor
                - Travel allowance as per company policy
                - Daily reports required for extended OD
                
                WORK FROM HOME:
                - WFH available for approved roles
                - Minimum 2 days notice required
                - Performance metrics apply to WFH employees
                """,
                "language": "en"
            },
            {
                "filename": "it_policies.pdf",
                "original_filename": "it_policies.pdf",
                "department": "IT",
                "content": """
                IT POLICIES AND PROCEDURES
                
                SYSTEM ACCESS:
                - Unique login credentials for each employee
                - Password must be changed every 90 days
                - Two-factor authentication for sensitive systems
                - No sharing of login credentials
                
                SOFTWARE USAGE:
                - Only approved software can be installed
                - License compliance is mandatory
                - Regular software updates required
                - No pirated software allowed
                
                DATA SECURITY:
                - Regular data backups
                - Encryption for sensitive data
                - Access logs maintained
                - Incident reporting within 2 hours
                
                NETWORK POLICIES:
                - No personal devices on company network
                - VPN required for remote access
                - Firewall rules strictly enforced
                - Regular security audits
                
                SUPPORT PROCEDURES:
                - IT helpdesk available 24/7
                - Priority based on severity
                - Response time: Critical (1 hour), High (4 hours), Medium (24 hours)
                """,
                "language": "en"
            },
            {
                "filename": "accounts_policies.pdf",
                "original_filename": "accounts_policies.pdf",
                "department": "ACCOUNTS",
                "content": """
                ACCOUNTS POLICIES AND PROCEDURES
                
                EXPENSE REIMBURSEMENT:
                - Original receipts required for all expenses
                - Expense reports due by 5th of each month
                - Approval required from department head
                - Reimbursement processed within 7 working days
                
                BUDGET MANAGEMENT:
                - Monthly budget reviews
                - Variance analysis required
                - Approval for budget overruns
                - Quarterly budget forecasts
                
                PAYROLL PROCESSING:
                - Salary processed on last working day
                - Overtime calculations as per policy
                - Deductions as per government norms
                - Payslips available on employee portal
                
                VENDOR PAYMENTS:
                - Three-way matching required
                - Payment terms: 30 days
                - Vendor registration mandatory
                - Regular vendor performance reviews
                
                FINANCIAL REPORTING:
                - Monthly financial statements
                - Quarterly management reports
                - Annual audit compliance
                - Regulatory filing deadlines
                
                LOAN POLICIES:
                - Personal loans available up to 3 months salary
                - Interest rate: 12% per annum
                - Repayment period: 12-36 months
                - Application through HR department
                """,
                "language": "en"
            },
            {
                "filename": "sales_policies.pdf",
                "original_filename": "sales_policies.pdf",
                "department": "SALES",
                "content": """
                SALES POLICIES AND PROCEDURES
                
                TARGET SETTING:
                - Monthly targets assigned to each salesperson
                - Quarterly reviews and adjustments
                - Performance linked to incentives
                - Territory management system
                
                CUSTOMER RELATIONSHIP:
                - CRM system mandatory for all interactions
                - Customer data confidentiality
                - Regular follow-up schedules
                - Complaint resolution within 48 hours
                
                PRICING POLICIES:
                - Standard pricing for regular products
                - Discount approval required for bulk orders
                - Competitive pricing analysis
                - Price revision quarterly
                
                ORDER PROCESSING:
                - Order confirmation within 24 hours
                - Credit check for new customers
                - Delivery timeline commitments
                - Order tracking system
                
                COMMISSION STRUCTURE:
                - Base commission: 2% of sales value
                - Performance bonus: 1% for exceeding targets
                - Quarterly commission payouts
                - Annual performance reviews
                """,
                "language": "en"
            }
        ]
        
        # Create documents and chunks
        for doc_data in sample_documents:
            # Create document record
            document = Document(
                filename=doc_data["filename"],
                original_filename=doc_data["original_filename"],
                department=doc_data["department"],
                file_path=f"sample/{doc_data['filename']}",
                file_size=len(doc_data["content"]),
                upload_user="system@aiplabro.com",
                upload_date=datetime.utcnow(),
                language=doc_data["language"],
                is_processed=True,
                chunk_count=1,
                last_indexed=datetime.utcnow()
            )
            db.add(document)
            db.flush()  # Get the document ID
            
            # Create document chunk
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=0,
                content=doc_data["content"],
                chunk_metadata={
                    "filename": doc_data["filename"],
                    "department": doc_data["department"],
                    "language": doc_data["language"],
                    "policy_type": "general"
                }
            )
            db.add(chunk)
        
        # Commit all changes
        db.commit()
        
        print(f"✅ Created {len(sample_documents)} sample documents for cloud deployment")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def get_sample_data_status():
    """Check if sample data exists."""
    try:
        db = next(get_db())
        doc_count = db.query(Document).count()
        chunk_count = db.query(DocumentChunk).count()
        return {
            "documents": doc_count,
            "chunks": chunk_count,
            "has_data": doc_count > 0 and chunk_count > 0
        }
    except Exception as e:
        print(f"Error checking sample data status: {e}")
        return {"documents": 0, "chunks": 0, "has_data": False}
