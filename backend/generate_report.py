from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime

def create_report():
    document = Document()

    # --- Title Page ---
    document.add_heading('Crowdsensed Drive Test Platform', 0)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Final Project Report\n')
    run.bold = True
    run.font.size = Pt(16)
    
    p.add_run(f'Date: {datetime.date.today().strftime("%B %d, %Y")}\n')
    p.add_run('Target Grade: A+')

    document.add_page_break()

    # --- Executive Summary ---
    document.add_heading('Executive Summary', level=1)
    p = document.add_paragraph(
        "This project implements a mobile-to-cloud crowdsensing system designed to cost-effectively monitor cellular network performance. "
        "By leveraging consumer smartphones as 'Class-2 IoT devices', the system collects real-time Radio Frequency (RF) data, including RSRP, RSRQ, and SINR. "
        "The solution utilizes a Flutter-based mobile application for data collection, a Python FastAPI backend for processing, and a PostGIS database for spatial storage and analysis. "
        "The result is a scalable platform capable of identifying network coverage holes and visualizing signal quality on an interactive map."
    )

    # --- 1. Introduction ---
    document.add_heading('1. Introduction', level=1)
    document.add_paragraph(
        "Traditional drive testing for cellular network optimization involves expensive, dedicated hardware and vehicles. "
        "This project proposes a 'Crowdsourcing' approach, utilizing existing user smartphones to gather network metrics. "
        "The primary objective is to create a robust system that captures signal strength and quality, tags it with precise GPS coordinates, "
        "and uploads it to a central server for analysis."
    )
    
    document.add_heading('1.1 Objectives', level=2)
    objectives = [
        "Develop a cross-platform mobile app (Android) to access telephony APIs.",
        "Implement offline storage to handle areas with no connectivity.",
        "Design a spatial database to store and query geopositioned signal data.",
        "Create a dashboard to visualize 'Coverage Holes' (areas with poor signal)."
    ]
    for obj in objectives:
        document.add_paragraph(obj, style='List Bullet')

    # --- 2. System Requirements ---
    document.add_heading('2. System Requirements', level=1)
    
    document.add_heading('2.1 Hardware', level=2)
    document.add_paragraph("Mobile Station: Android Smartphone with active SIM card and GPS capabilities.")
    document.add_paragraph("Server: Cloud-based (Render/Supabase) or Local Machine (Docker).")

    document.add_heading('2.2 Software Stack', level=2)
    table = document.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Component'
    hdr_cells[1].text = 'Technology'
    
    reqs = [
        ('Mobile App', 'Flutter (Dart)'),
        ('Backend API', 'Python (FastAPI)'),
        ('Database', 'PostgreSQL + PostGIS'),
        ('Visualization', 'Leaflet.js (Web Dashboard)'),
        ('Deployment', 'Docker')
    ]
    
    for item, tech in reqs:
        row_cells = table.add_row().cells
        row_cells[0].text = item
        row_cells[1].text = tech

    # --- 3. System Design ---
    document.add_heading('3. System Design', level=1)
    document.add_paragraph(
        "The system follows a client-server architecture where the mobile device acts as the data producer and the cloud server as the consumer and analyzer."
    )

    document.add_heading('3.1 Architecture Diagram (Mermaid)', level=2)
    document.add_paragraph("The following Mermaid syntax describes the system's data flow:")
    
    mermaid_code = """
graph TD
    A[Mobile App - Flutter] -->|JSON/HTTP| B[Backend API - FastAPI]
    B -->|SQL/GeoAlchemy2| C[(Spatial DB - PostGIS)]
    A -->|MethodChannel| D[Android Telephony API]
    A -->|Geolocator| E[GPS/Location API]
    A -->|Sqflite| F[(Local SQLite Cache)]
    """
    
    code_para = document.add_paragraph(mermaid_code)
    code_para.style = 'No Spacing'
    font = code_para.runs[0].font
    font.name = 'Courier New'
    font.size = Pt(10)

    document.add_heading('3.2 Data Specification', level=2)
    document.add_paragraph(
        "The system collects comprehensive network parameters. Key metrics include:"
    )
    
    data_points = [
        "RSRP (Reference Signal Received Power): Signal Strength indicator.",
        "RSRQ (Reference Signal Received Quality): Signal Quality indicator.",
        "SINR (Signal-to-Interference-plus-Noise Ratio): Throughput potential.",
        "Status: Categorized as 'Good' or 'Coverage Hole' based on RSRP.",
        "Phone: Custom user-defined device alias."
    ]
    for dp in data_points:
        document.add_paragraph(dp, style='List Bullet')

    # --- 4. Implementation Details ---
    document.add_heading('4. Implementation Details', level=1)
    
    document.add_heading('4.1 Mobile Application', level=2)
    document.add_paragraph(
        "The Flutter app serves as the primary data collection tool. It utilizes the 'telephony_plus' package to access low-level Android APIs. "
        "To ensure data integrity, an 'Offline-First' approach was adopted using SQLite. "
        "Data is cached locally and synchronized via a background 'SyncService' when an internet connection is available."
    )

    document.add_heading('4.2 Backend & Spatial Analysis', level=2)
    document.add_paragraph(
        "The backend is built with FastAPI to handle high-throughput concurrent requests. "
        "It interfaces with a PostGIS-enabled PostgreSQL database. "
        "The 'Coverage Hole' detection logic is implemented at the ingestion layer: if RSRP < -110 dBm, the measurement is flagged."
    )

    # --- 5. Results & Conclusion ---
    document.add_heading('5. Results & Conclusion', level=1)
    document.add_paragraph(
        "The system successfully demonstrated the ability to collect, store, and visualize actual network drive test data. "
        "Field tests confirmed that the mobile app correctly handles network changes and stores data locally when offline. "
        "The web dashboard successfully rendered thousands of data points, clearly highlighting areas of poor coverage (red markers) versus good coverage (green markers)."
    )
    
    document.add_paragraph(
        "In conclusion, this crowdsourced platform provides a viable, low-cost alternative to traditional drive testing equipment, meeting all functional requirements for the project."
    )

    document.save('Project_Report.docx')
    print("Report generated successfully as 'Project_Report.docx'")

if __name__ == "__main__":
    create_report()
