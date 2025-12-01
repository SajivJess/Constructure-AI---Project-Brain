"""
Generate a sample construction specification PDF for testing
Run this if you don't have real construction documents
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import os

def create_sample_construction_pdf():
    """Create a sample construction specification PDF"""
    
    output_dir = "../sample_docs"
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "sample_construction_specs.pdf")
    
    doc = SimpleDocTemplate(filename, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Title Page
    elements.append(Paragraph("CONSTRUCTION PROJECT SPECIFICATIONS", title_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Sample Office Building Renovation", styles['Heading3']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(f"Document Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Project No: 2024-001", normal_style))
    elements.append(PageBreak())
    
    # Section 1: Door Schedule
    elements.append(Paragraph("SECTION 1: DOOR SCHEDULE", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    door_data = [
        ['Mark', 'Location', 'Width (mm)', 'Height (mm)', 'Fire Rating', 'Material'],
        ['D-101', 'Main Entrance', '1200', '2400', '90 MIN', 'Aluminum/Glass'],
        ['D-102', 'Level 1 Corridor', '900', '2100', '1 HR', 'Hollow Metal'],
        ['D-103', 'Level 1 Corridor', '900', '2100', '1 HR', 'Hollow Metal'],
        ['D-104', 'Office 101', '900', '2100', 'NONE', 'Wood'],
        ['D-105', 'Office 102', '900', '2100', 'NONE', 'Wood'],
        ['D-201', 'Level 2 Corridor', '900', '2100', '1 HR', 'Hollow Metal'],
        ['D-202', 'Conference Room', '1000', '2100', '1 HR', 'Wood'],
        ['D-203', 'Server Room', '900', '2100', '2 HR', 'Steel'],
    ]
    
    door_table = Table(door_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
    door_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(door_table)
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("Door Requirements:", styles['Heading4']))
    elements.append(Paragraph("• All corridor doors shall have 1-hour fire rating minimum", normal_style))
    elements.append(Paragraph("• Doors shall comply with accessibility requirements (32-inch clear width minimum)", normal_style))
    elements.append(Paragraph("• Fire-rated doors shall be self-closing with approved hardware", normal_style))
    elements.append(Paragraph("• All doors shall have lever-style handles for accessibility", normal_style))
    elements.append(PageBreak())
    
    # Section 2: Room Schedule
    elements.append(Paragraph("SECTION 2: ROOM SCHEDULE", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    room_data = [
        ['Room', 'Area (m²)', 'Floor Finish', 'Ceiling Height (m)', 'Occupancy Type'],
        ['Lobby', '45.0', 'Porcelain Tile', '3.6', 'Assembly'],
        ['Office 101', '25.0', 'Carpet Tile', '2.7', 'Business'],
        ['Office 102', '25.0', 'Carpet Tile', '2.7', 'Business'],
        ['Conference', '35.0', 'Carpet Tile', '2.7', 'Assembly'],
        ['Kitchen', '20.0', 'Vinyl Tile', '2.7', 'Business'],
        ['Corridor L1', '40.0', 'Vinyl Tile', '2.7', 'Corridor'],
        ['Office 201', '28.0', 'Carpet Tile', '2.7', 'Business'],
        ['Server Room', '15.0', 'Raised Floor', '2.7', 'Business'],
    ]
    
    room_table = Table(room_data, colWidths=[1.2*inch, 1*inch, 1.3*inch, 1.2*inch, 1.3*inch])
    room_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(room_table)
    elements.append(PageBreak())
    
    # Section 3: Fire Safety
    elements.append(Paragraph("SECTION 3: FIRE SAFETY SPECIFICATIONS", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("3.1 Corridor Partitions", styles['Heading4']))
    elements.append(Paragraph(
        "All corridor partitions shall be constructed with 1-hour fire-rated assemblies. "
        "Partitions shall extend from floor to underside of structure above. "
        "Fire-rated partition construction shall consist of metal studs with Type X gypsum board "
        "on both sides.", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("3.2 Fire Protection Systems", styles['Heading4']))
    elements.append(Paragraph("• Automatic fire sprinkler system throughout", normal_style))
    elements.append(Paragraph("• Addressable fire alarm system with voice evacuation", normal_style))
    elements.append(Paragraph("• Emergency lighting with battery backup", normal_style))
    elements.append(Paragraph("• Exit signage with LED illumination", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("3.3 Accessibility Requirements", styles['Heading4']))
    elements.append(Paragraph(
        "All spaces shall comply with accessibility standards including: "
        "minimum 32-inch clear door width, lever-style door hardware, "
        "accessible restroom facilities, accessible routes throughout, "
        "and appropriate signage.", normal_style))
    elements.append(PageBreak())
    
    # Section 4: MEP Equipment
    elements.append(Paragraph("SECTION 4: MEP EQUIPMENT SCHEDULE", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    mep_data = [
        ['Type', 'Description', 'Model', 'Location', 'Specifications'],
        ['HVAC', 'Roof Top Unit', 'RTU-10', 'Roof', '10 Ton, 460V-3Ph'],
        ['HVAC', 'Air Handler', 'AHU-01', 'Mechanical Room', '5000 CFM'],
        ['Electrical', 'Main Panel', 'MP-01', 'Electrical Room', '400A, 208V'],
        ['Electrical', 'Emergency Generator', 'GEN-01', 'Exterior', '100kW, Diesel'],
        ['Plumbing', 'Water Heater', 'WH-01', 'Mechanical Room', '50 Gal, Gas'],
        ['Fire', 'Fire Pump', 'FP-01', 'Sprinkler Room', '500 GPM'],
    ]
    
    mep_table = Table(mep_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1.3*inch, 1.5*inch])
    mep_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(mep_table)
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("4.1 HVAC Systems", styles['Heading4']))
    elements.append(Paragraph(
        "The HVAC system shall consist of a roof-mounted package unit with supply and "
        "return ductwork throughout. System shall maintain 72°F ± 2°F in occupied spaces. "
        "All ductwork shall be insulated per energy code requirements.", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("4.2 Electrical Systems", styles['Heading4']))
    elements.append(Paragraph(
        "Building electrical service shall be 400A, 208V, 3-phase. Emergency generator shall "
        "provide backup power to life safety systems including emergency lighting, fire alarm, "
        "and exit signs. All wiring shall be in EMT conduit.", normal_style))
    elements.append(PageBreak())
    
    # Section 5: Finishes
    elements.append(Paragraph("SECTION 5: FINISH SPECIFICATIONS", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("5.1 Lobby Flooring", styles['Heading4']))
    elements.append(Paragraph(
        "Lobby flooring shall be 24x24 inch porcelain tile, color as selected by architect. "
        "Tile shall be installed over concrete substrate with thin-set adhesive. "
        "All transitions shall be ADA-compliant.", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("5.2 Office Flooring", styles['Heading4']))
    elements.append(Paragraph(
        "Office spaces shall have carpet tile, 24x24 inches, commercial grade with minimum "
        "10-year warranty. Carpet shall be installed with adhesive per manufacturer's "
        "specifications.", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("5.3 Wall Finishes", styles['Heading4']))
    elements.append(Paragraph(
        "Interior walls shall receive two coats of latex paint over primed gypsum board. "
        "Corridor walls shall have wainscot protection to 42 inches above finished floor. "
        "Colors per finish schedule.", normal_style))
    
    # Build PDF
    doc.build(elements)
    print(f"Sample PDF created: {filename}")
    return filename

if __name__ == "__main__":
    try:
        # Try to import reportlab
        create_sample_construction_pdf()
        print("\n✅ Sample construction specification PDF created successfully!")
        print("📄 Location: sample_docs/sample_construction_specs.pdf")
        print("\n📝 You can now:")
        print("1. Start the backend and frontend servers")
        print("2. Login with test credentials")
        print("3. Upload this PDF in the Documents tab")
        print("4. Start asking questions in the Chat tab")
    except ImportError:
        print("❌ Error: reportlab library not found")
        print("\nPlease install it:")
        print("  pip install reportlab")
        print("\nThen run this script again:")
        print("  python generate_sample_docs.py")
