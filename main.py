import streamlit as st
import sqlite3
from datetime import date
from mailmerge import MailMerge
import os
import pandas as pd
from PIL import Image
from docx2pdf import convert
from time import sleep
import subprocess
# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (name TEXT, father_name TEXT, cnic TEXT, roll_no TEXT, registration_date DATE)''')
    conn.commit()
    conn.close()

# Initialize admin credentials
ADMIN_USERNAME = "2409"
ADMIN_PASSWORD = "2105264@tT"

def convert_to_pdf(docx_path):
    output_dir = os.path.dirname(docx_path)
    pdf_path = docx_path.replace('.docx', '.pdf')
    
    try:
        subprocess.call(['soffice',
                     '--headless',
                     '--convert-to',
                     'pdf',
                     '--outdir',
                     output_dir,
                     docx_path])
        return pdf_path
    except Exception as e:
        st.error(f"Error converting to PDF: {str(e)}")
        return docx_path  # Fallback to docx if conversion fails

# Check if CNIC exists
def check_cnic_exists(cnic):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE cnic=?", (cnic,))
    result = c.fetchone()
    conn.close()
    return result

# Get roll number slip for existing CNIC
def get_existing_slip(cnic):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT roll_no FROM students WHERE cnic=?", (cnic,))
    roll_no = c.fetchone()[0]
    conn.close()
    return f"slips/{roll_no}.docx"

def generate_roll_no(name):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students")
    count = c.fetchone()[0]
    conn.close()
    return f"STD-{count + 1:03d}"

def generate_slip(name, father_name, cnic, roll_no):
    template = "slip.docx"
    document = MailMerge(template)
    
    document.merge(
        name=name,
        fathername=father_name,
        date='{:%d-%b-%Y}'.format(date.today()),
        rollno=roll_no,
        cnic=cnic
    )
    
    output_file = f"slips/{roll_no}.docx"
    document.write(output_file)
    return output_file

def authenticate(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def main():
    st.set_page_config(page_title="School Registration System", layout="wide")
    
    # Custom CSS for layout
    st.markdown("""
        <style>
        .container {
            display: flex;
            align-items: center;
            padding: 10px;
        }
        .logo-img {
            float: left;
            width: 150px;
        }
        .school-info {
            margin-left: 20px;
            padding: 10px;
        }
        .school-name {
            font-size: 32px;
            font-weight: bold;
            color: #1f4d7a;
        }
        .school-address {
            font-size: 18px;
            color: #666;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create slips directory if it doesn't exist
    if not os.path.exists("slips"):
        os.makedirs("slips")
    
    # Initialize database
    init_db()
    
    # Header with logo and school info
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        try:
            logo = Image.open("logo.png")
            st.image(logo, width=150)
        except:
            st.warning("Place 'school_logo.png' in the same directory")
    
    with col2:
        st.markdown("""
            <div class="school-info">
                <div class="school-name">Suffah Islamic School System</div>
                <div class="school-address">New City Phase 2 - Campus-1</div>
                <div class="school-address">Wah Cantt - 47040</div>
                <div class="school-address">Phone: 0514905828</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("👤 Admin"):
            st.session_state.page = 'admin_login'
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'registration'
    
    if st.session_state.page == 'registration':
        show_registration_page()
    elif st.session_state.page == 'admin_login':
        show_admin_login()
    elif st.session_state.page == 'admin_dashboard':
        show_admin_dashboard()

def show_registration_page():
    st.markdown("### Student Registration")
    
    with st.form("registration_form"):
        name = st.text_input("Full Name")
        father_name = st.text_input("Father's Name")
        cnic = st.text_input("CNIC/B-Form Number")
        submitted = st.form_submit_button("Submit")
    
    if submitted:
        if not all([name, father_name, cnic]):
            st.error("Please fill all the fields")
            return
        
        # Show processing message with spinner
        with st.spinner('Processing your registration...'):
            # Check if CNIC already exists
            existing_record = check_cnic_exists(cnic)
            
            if existing_record:
                sleep(1)  # Add small delay for better UX
                st.warning("You are already registered!")
                st.write(f"Name: {existing_record[0]}")
                st.write(f"Roll Number: {existing_record[3]}")
                
                # Show PDF generation message
                with st.spinner('Generating your PDF slip...'):
                    existing_slip = get_existing_slip(cnic)
                    pdf_slip = convert_to_pdf(existing_slip)
                    sleep(1)  # Add small delay for better UX
                    
                with open(pdf_slip, "rb") as file:
                    st.success('Your slip is ready!')
                    st.download_button(
                        label="Download Your Roll Number Slip",
                        data=file,
                        file_name=f"{existing_record[3]}_slip.pdf",
                        mime="application/pdf"
                    )
            else:
                roll_no = generate_roll_no(name)
                
                # Save to database
                conn = sqlite3.connect('students.db')
                c = conn.cursor()
                c.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)",
                         (name, father_name, cnic, roll_no, date.today()))
                conn.commit()
                conn.close()
                
                # Show document generation message
                with st.spinner('Generating your registration slip...'):
                    slip_file = generate_slip(name, father_name, cnic, roll_no)
                    pdf_slip = convert_to_pdf(slip_file)
                    sleep(1)  # Add small delay for better UX
                
                st.success("Registration Successful!")
                st.write(f"Your Roll Number is: {roll_no}")
                
                with open(pdf_slip, "rb") as file:
                    st.download_button(
                        label="Download Roll Number Slip",
                        data=file,
                        file_name=f"{roll_no}_slip.pdf",
                        mime="application/pdf"
                    )
                st.balloons()

def show_admin_login():
    st.title("Admin Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.page = 'admin_dashboard'
        else:
            st.error("Invalid credentials")

def show_admin_dashboard():
    st.title("Admin Dashboard")
    
    # Logout button
    if st.button("Logout"):
        st.session_state.page = 'registration'
        st.rerun()
    
    # Display student records
    conn = sqlite3.connect('students.db')
    df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    
    st.write("### Student Records")
    st.dataframe(df)
    
    # Export to CSV option
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Export to CSV",
            data=csv,
            file_name="student_records.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
