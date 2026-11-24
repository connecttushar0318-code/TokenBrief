# scripts/build_full_minor_report.py
"""
Master compiler script for Tushar Bansal's Minor Project Report.
Assembles the complete 63-page academic report in python-docx, applies
all ADGIPS institutional guidelines, and converts directly to PDF via Microsoft Word LTSC.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
import win32com.client
import pypdf

# Import modular content
from report_content_front import (
    PROJECT_TITLE, STUDENT_NAME, ENROLMENT_NO, SECTION, SEMESTER,
    DEGREE, BRANCH, SUPERVISOR_NAME, SUPERVISOR_DESIG, DEPARTMENT,
    INSTITUTE, INSTITUTE_ADDRESS, AFFILIATION, ACADEMIC_SESSION,
    YEAR_OF_SUBMISSION, SUBMISSION_DATE, DECLARATION_TEXT, CERTIFICATE_TEXT,
    ABSTRACT_TEXT, ACKNOWLEDGEMENT_TEXT, FIGURES_LIST, TABLES_LIST,
    ABBREVIATIONS_LIST, TOC_ENTRIES
)
from report_content_ch1_ch2 import CH1_SECTIONS, CH2_SECTIONS, TABLE_2_1_DATA, TABLE_2_2_DATA
from report_content_ch3 import CH3_SECTIONS, TABLE_3_1_DATA, TABLE_3_2_DATA
from report_content_ch4 import CH4_SECTIONS, TABLE_4_1_DATA
from report_content_ch5 import CH5_SECTIONS, TABLE_5_1_DATA, TABLE_5_2_DATA
from report_content_ch6_back import (
    CH6_SECTIONS, REFERENCES_DATA, APPENDIX_A_CONTENT,
    APPENDIX_B_CONTENT, APPENDIX_C_CONTENT, APPENDIX_D_CONTENT, ANNEXURE_CONTENT
)

# Styling and XML helpers
def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_page_number_field(run):
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

def format_run(run, font_name="Times New Roman", size_pt=12, bold=False, italic=False, color_rgb=(0,0,0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)

def add_p(doc, text="", font_name="Times New Roman", size_pt=12, bold=False, italic=False,
          align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=6, line_spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        r = p.add_run(text)
        format_run(r, font_name, size_pt, bold, italic)
    return p

def add_h1(doc, text):
    return add_p(doc, text, size_pt=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=18, space_after=12)

def add_h2(doc, text):
    return add_p(doc, text, size_pt=14, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=14, space_after=6)

def add_h3(doc, text):
    return add_p(doc, text, size_pt=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=10, space_after=4)

def add_styled_table(doc, data, col_widths=None, caption=None):
    if caption:
        add_p(doc, caption, size_pt=11, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=12, space_after=4)
    
    rows = len(data)
    cols = len(data[0])
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            
            if r_idx == 0:
                set_cell_background(cell, "1E3A8A") # Navy header
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(str(val))
                format_run(r, size_pt=9.5, bold=True, color_rgb=(255, 255, 255))
            else:
                if r_idx % 2 == 1:
                    set_cell_background(cell, "F8FAFC") # Soft zebra row
                else:
                    set_cell_background(cell, "FFFFFF")
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                r = p.add_run(str(val))
                format_run(r, size_pt=9, bold=(c_idx == 0))
                
            if col_widths and c_idx < len(col_widths):
                cell.width = col_widths[c_idx]
                
    add_p(doc, "", space_before=0, space_after=8)
    return table

def add_figure(doc, img_path, caption, width_in=5.6):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(10)
        p_img.paragraph_format.space_after = Pt(4)
        run = p_img.add_run()
        run.add_picture(img_path, width=Inches(width_in))
        
        p_cap = add_p(doc, caption, size_pt=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=12)
        return p_img, p_cap
    else:
        print(f"Warning: Image {img_path} not found.")
        return None

def build_report():
    print("Initializing docx Document...")
    doc = docx.Document()
    
    # Configure default style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = RGBColor(0, 0, 0)
    
    # -------------------------------------------------------------
    # SECTION 1: FRONT MATTER
    # -------------------------------------------------------------
    sec1 = doc.sections[0]
    sec1.page_width = Cm(21.0)
    sec1.page_height = Cm(29.7)
    sec1.left_margin = Cm(3.5)
    sec1.top_margin = Cm(2.5)
    sec1.right_margin = Cm(1.25)
    sec1.bottom_margin = Cm(1.25)
    sec1.different_first_page_header_footer = True
    
    # Page numbering for front matter: lowerRoman starting at 0 (page 2 becomes i)
    pgNumType1 = OxmlElement('w:pgNumType')
    pgNumType1.set(qn('w:fmt'), 'lowerRoman')
    pgNumType1.set(qn('w:start'), '0')
    sec1._sectPr.append(pgNumType1)
    
    # Section 1 Header (Right-aligned page number)
    header1 = sec1.header
    p_h1 = header1.paragraphs[0]
    p_h1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_h1 = p_h1.add_run()
    format_run(r_h1, size_pt=10)
    add_page_number_field(r_h1)
    
    # -------------------------------------------------------------
    # PAGE 1: OUTER COVER PAGE
    # -------------------------------------------------------------
    print("Writing Page 1: Outer Cover...")
    add_p(doc, PROJECT_TITLE, size_pt=20, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=12, line_spacing=1.2)
    add_p(doc, "MINOR PROJECT REPORT", size_pt=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=10)
    add_p(doc, "SUBMITTED IN PARTIAL FULFILMENT OF THE REQUIREMENTS FOR THE AWARD OF THE DEGREE OF",
          size_pt=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=6)
    add_p(doc, DEGREE, size_pt=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=4)
    add_p(doc, f"({BRANCH})", size_pt=11.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=14)
    
    # Logo
    logo_path = 'report_assets/college_logo.png'
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(14)
        run_logo = p_logo.add_run()
        run_logo.add_picture(logo_path, width=Inches(1.4))
    
    # Submission Details
    add_p(doc, f"Submitted by:\n{STUDENT_NAME}\nRoll No.: {ENROLMENT_NO}\nSection: {SECTION}\nSemester: {SEMESTER}",
          size_pt=11, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=10, line_spacing=1.2)
    
    add_p(doc, f"Under the Supervision of:\n{SUPERVISOR_NAME}\nDesignation: {SUPERVISOR_DESIG}\nDepartment of AI & DS\nADGIPS, Delhi",
          size_pt=11, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=12, line_spacing=1.2)
    
    add_p(doc, f"Academic Session: {ACADEMIC_SESSION}", size_pt=11, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=4)
    add_p(doc, DEPARTMENT, size_pt=11.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_p(doc, INSTITUTE, size_pt=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_p(doc, INSTITUTE_ADDRESS, size_pt=10, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_p(doc, AFFILIATION, size_pt=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=2)
    add_p(doc, f"Year of Submission: {YEAR_OF_SUBMISSION}", size_pt=11, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=0, space_after=0)
    
    # -------------------------------------------------------------
    # PAGE 2: DECLARATION BY STUDENT (Page i)
    # -------------------------------------------------------------
    print("Writing Page 2: Declaration by Student...")
    doc.add_page_break()
    add_h1(doc, "DECLARATION BY THE STUDENT")
    for para in DECLARATION_TEXT.split("\n\n"):
        add_p(doc, para, space_before=0, space_after=12)
    
    add_p(doc, "\nStudent Signature: ____________________\n", bold=True, space_before=18, space_after=6)
    add_p(doc, f"Student Name: {STUDENT_NAME}\nEnrolment No.: {ENROLMENT_NO}\nDate: {SUBMISSION_DATE}\nPlace: Delhi",
          bold=True, space_before=0, space_after=0, line_spacing=1.2)
    
    # -------------------------------------------------------------
    # PAGE 3: CERTIFICATE BY SUPERVISOR (Page ii)
    # -------------------------------------------------------------
    print("Writing Page 3: Certificate by Supervisor...")
    doc.add_page_break()
    add_h1(doc, "CERTIFICATE BY THE SUPERVISOR")
    for para in CERTIFICATE_TEXT.split("\n\n"):
        add_p(doc, para, space_before=0, space_after=12)
        
    add_p(doc, "\nSignature of Supervisor: ____________________\n", bold=True, space_before=18, space_after=6)
    add_p(doc, f"Supervisor Name: {SUPERVISOR_NAME}\nDesignation: {SUPERVISOR_DESIG}\nDepartment: {DEPARTMENT}\n{INSTITUTE}, Delhi\nDate: {SUBMISSION_DATE}",
          bold=True, space_before=0, space_after=0, line_spacing=1.2)
          
    # -------------------------------------------------------------
    # PAGE 4: ABSTRACT (Page iii)
    # -------------------------------------------------------------
    print("Writing Page 4: Abstract...")
    doc.add_page_break()
    add_h1(doc, "ABSTRACT")
    for para in ABSTRACT_TEXT.split("\n\n"):
        add_p(doc, para, size_pt=11.5, space_before=0, space_after=8, line_spacing=1.35)
        
    # -------------------------------------------------------------
    # PAGE 5: ACKNOWLEDGEMENT (Page iv)
    # -------------------------------------------------------------
    print("Writing Page 5: Acknowledgement...")
    doc.add_page_break()
    add_h1(doc, "ACKNOWLEDGEMENT")
    for para in ACKNOWLEDGEMENT_TEXT.split("\n\n"):
        add_p(doc, para, space_before=0, space_after=10)
        
    add_p(doc, f"\n{STUDENT_NAME}\nB.Tech. ({BRANCH})\nEnrolment No.: {ENROLMENT_NO}\n{DEPARTMENT}\n{INSTITUTE}, Delhi",
          bold=True, space_before=16, space_after=0, line_spacing=1.2)
          
    # -------------------------------------------------------------
    # PAGE 6: LIST OF FIGURES (Page v)
    # -------------------------------------------------------------
    print("Writing Page 6: List of Figures...")
    doc.add_page_break()
    add_h1(doc, "LIST OF FIGURES")
    fig_table_data = [["Figure No.", "Figure Description", "Page No."]]
    for fig_no, desc, page in FIGURES_LIST:
        fig_table_data.append([fig_no, desc, page])
    add_styled_table(doc, fig_table_data, [Inches(1.3), Inches(4.2), Inches(0.9)])
    
    # -------------------------------------------------------------
    # PAGE 7: LIST OF TABLES (Page vi)
    # -------------------------------------------------------------
    print("Writing Page 7: List of Tables...")
    doc.add_page_break()
    add_h1(doc, "LIST OF TABLES")
    tbl_table_data = [["Table No.", "Table Description", "Page No."]]
    for tbl_no, desc, page in TABLES_LIST:
        tbl_table_data.append([tbl_no, desc, page])
    add_styled_table(doc, tbl_table_data, [Inches(1.3), Inches(4.2), Inches(0.9)])
    
    # -------------------------------------------------------------
    # PAGE 8: LIST OF ABBREVIATIONS (Page vii)
    # -------------------------------------------------------------
    print("Writing Page 8: List of Abbreviations...")
    doc.add_page_break()
    add_h1(doc, "LIST OF ABBREVIATIONS")
    abbr_table_data = [["Abbreviation", "Full Form"]]
    for abbr, full in ABBREVIATIONS_LIST:
        abbr_table_data.append([abbr, full])
    add_styled_table(doc, abbr_table_data, [Inches(1.8), Inches(4.6)])
    
    # -------------------------------------------------------------
    # PAGES 9-10: TABLE OF CONTENTS (Pages viii - ix)
    # -------------------------------------------------------------
    print("Writing Pages 9-10: Table of Contents...")
    doc.add_page_break()
    add_h1(doc, "TABLE OF CONTENTS")
    toc_table_data = [["Particulars", "Page No."]]
    for item, page in TOC_ENTRIES:
        toc_table_data.append([item, page])
    add_styled_table(doc, toc_table_data, [Inches(5.4), Inches(1.0)])
    
    # -------------------------------------------------------------
    # SECTION 2: MAIN BODY (Chapters 1 to 6, References, Appendices)
    # -------------------------------------------------------------
    print("Starting Section 2: Main Chapters (Page 1 in Arabic)...")
    sec2 = doc.add_section(docx.enum.section.WD_SECTION_START.NEW_PAGE)
    sec2.page_width = Cm(21.0)
    sec2.page_height = Cm(29.7)
    sec2.left_margin = Cm(3.5)
    sec2.top_margin = Cm(2.5)
    sec2.right_margin = Cm(1.25)
    sec2.bottom_margin = Cm(1.25)
    sec2.header.is_linked_to_previous = False
    
    # Restart page numbering at 1 in decimal format
    pgNumType2 = OxmlElement('w:pgNumType')
    pgNumType2.set(qn('w:fmt'), 'decimal')
    pgNumType2.set(qn('w:start'), '1')
    sec2._sectPr.append(pgNumType2)
    
    header2 = sec2.header
    p_h2 = header2.paragraphs[0]
    p_h2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_h2 = p_h2.add_run()
    format_run(r_h2, size_pt=10)
    add_page_number_field(r_h2)
    
    # -------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # -------------------------------------------------------------
    print("Writing Chapter 1: Introduction...")
    for ch_title, sections in CH1_SECTIONS:
        add_h1(doc, ch_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
                
    # -------------------------------------------------------------
    # CHAPTER 2: REQUIREMENT ANALYSIS AND SYSTEM SPECIFICATION
    # -------------------------------------------------------------
    print("Writing Chapter 2: Requirement Analysis...")
    doc.add_page_break()
    for ch_title, sections in CH2_SECTIONS:
        add_h1(doc, ch_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
            if sec_title.startswith("2.4"):
                add_styled_table(doc, TABLE_2_1_DATA, caption="Table 2.1: Comparison of Existing Systems versus TokenBrief Platform")
            elif sec_title.startswith("2.7"):
                add_styled_table(doc, TABLE_2_2_DATA, caption="Table 2.2: Hardware and Software Specification and Requirements")

    # -------------------------------------------------------------
    # CHAPTER 3: SYSTEM DESIGN
    # -------------------------------------------------------------
    print("Writing Chapter 3: System Design...")
    doc.add_page_break()
    for ch_title, sections in CH3_SECTIONS:
        add_h1(doc, ch_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
            if sec_title.startswith("3.1"):
                add_figure(doc, "report_assets/fig3_1_architecture.png", "Figure 3.1: High-Level System Architecture of TokenBrief Platform")
            elif sec_title.startswith("3.2"):
                add_figure(doc, "report_assets/fig3_2_workflow.png", "Figure 3.2: System Data Flow and Machine Learning Inference Pipeline Workflow")
            elif sec_title.startswith("3.4"):
                add_styled_table(doc, TABLE_3_1_DATA, caption="Table 3.1: Document Chunking and Dense Embedding Specifications")
            elif sec_title.startswith("3.8"):
                add_styled_table(doc, TABLE_3_2_DATA, caption="Table 3.2: Relational Database Schema Specifications for PostgreSQL")

    # -------------------------------------------------------------
    # CHAPTER 4: IMPLEMENTATION, TESTING AND MAINTENANCE
    # -------------------------------------------------------------
    print("Writing Chapter 4: Implementation and Testing...")
    doc.add_page_break()
    for ch_title, sections in CH4_SECTIONS:
        add_h1(doc, ch_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
            if sec_title.startswith("4.4"):
                add_figure(doc, "report_assets/ui_auth_otp.png", "Figure 4.1: Secure User Authentication & Passwordless Email OTP Verification")
                add_figure(doc, "report_assets/ui_workspace_chat.png", "Figure 4.2: Document Workspace, Conversational Q&A and Grounded Citation Highlighting")
                add_figure(doc, "report_assets/ui_quiz_studio.png", "Figure 4.3: Interactive Quiz Studio with Question Count Slider and Spaced Repetition")
                add_figure(doc, "report_assets/ui_doc_comparison.png", "Figure 4.4: Multi-Document Structured Comparison Matrix Interface")
                add_figure(doc, "report_assets/ui_email_template.png", "Figure 4.5: Transactional Email OTP Relay Template via Google Apps Script Webhook")
            elif sec_title.startswith("4.6"):
                add_styled_table(doc, TABLE_4_1_DATA, caption="Table 4.1: System Verification Test Cases and Execution Outcomes")

    # -------------------------------------------------------------
    # CHAPTER 5: RESULTS AND DISCUSSIONS
    # -------------------------------------------------------------
    print("Writing Chapter 5: Results and Discussions...")
    doc.add_page_break()
    for ch_title, sections in CH5_SECTIONS:
        add_h1(doc, ch_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
            if sec_title.startswith("5.2"):
                add_figure(doc, "report_assets/fig5_1_latency.png", "Figure 5.1: Latency Benchmark Comparison Across RAG Pipeline Configurations")
            elif sec_title.startswith("5.3"):
                add_figure(doc, "report_assets/ui_knowledge_graph.png", "Figure 5.2: Interactive Entity Knowledge Graph Visualisation Canvas")
                add_figure(doc, "report_assets/ui_analytics_dashboard.png", "Figure 5.3: Real-Time Analytics Telemetry Dashboard and Gemini Model Distribution")
            elif sec_title.startswith("5.4"):
                add_styled_table(doc, TABLE_5_1_DATA, caption="Table 5.1: Retrieval Accuracy, Grounding Precision, and Hallucination Abstention Metrics")
            elif sec_title.startswith("5.5"):
                add_styled_table(doc, TABLE_5_2_DATA, caption="Table 5.2: Latency, Cache Hit Rate, and Token Cost Optimization Benchmarks")
                add_figure(doc, "report_assets/fig5_5_cache_hit_ratio.png", "Figure 5.4: Impact of Semantic Cache Warm-Up on Query Response Latency and Throughput")

    # -------------------------------------------------------------
    # CHAPTER 6: CONCLUSION AND FUTURE SCOPE
    # -------------------------------------------------------------
    print("Writing Chapter 6: Conclusion and Future Scope...")
    doc.add_page_break()
    for ch_title, sections in CH6_SECTIONS:
        add_h1(doc, ch_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)

    # -------------------------------------------------------------
    # REFERENCES
    # -------------------------------------------------------------
    print("Writing References...")
    doc.add_page_break()
    add_h1(doc, "REFERENCES")
    for ref in REFERENCES_DATA:
        add_p(doc, ref, size_pt=10, space_before=2, space_after=6, line_spacing=1.15)

    # -------------------------------------------------------------
    # APPENDICES & ANNEXURE
    # -------------------------------------------------------------
    print("Writing Appendices A to D and Annexure...")
    # Appendix A
    doc.add_page_break()
    for app_title, sections in APPENDIX_A_CONTENT:
        add_h1(doc, app_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
                
    # Appendix B
    doc.add_page_break()
    for app_title, sections in APPENDIX_B_CONTENT:
        add_h1(doc, app_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
                
    # Appendix C
    doc.add_page_break()
    for app_title, sections in APPENDIX_C_CONTENT:
        add_h1(doc, app_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
                
    # Appendix D
    doc.add_page_break()
    for app_title, sections in APPENDIX_D_CONTENT:
        add_h1(doc, app_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)
                
    # Annexure
    doc.add_page_break()
    for ann_title, sections in ANNEXURE_CONTENT:
        add_h1(doc, ann_title)
        for sec_title, paras in sections:
            add_h2(doc, sec_title)
            for p_text in paras:
                add_p(doc, p_text)

    # Save docx
    docx_filename = "TokenBrief_Minor_Project_Report_Tushar_Bansal.docx"
    pdf_filename = "TokenBrief_Minor_Project_Report_Tushar_Bansal.pdf"
    docx_path = os.path.abspath(docx_filename)
    pdf_path = os.path.abspath(pdf_filename)
    
    print(f"Saving compiled DOCX to {docx_path}...")
    doc.save(docx_path)
    print("DOCX saved successfully!")
    
    # Convert to PDF via Word COM
    print("Starting Word COM Automation for PDF compilation...")
    word = win32com.client.Dispatch('Word.Application')
    word.Visible = False
    try:
        wb = word.Documents.Open(docx_path)
        wb.SaveAs(pdf_path, FileFormat=17) # 17 is wdFormatPDF
        wb.Close()
        print(f"PDF exported successfully to {pdf_path}!")
    finally:
        word.Quit()
        
    # Analyze compiled PDF
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"\n=======================================================")
    print(f"REPORT COMPILATION COMPLETE:")
    print(f"• Total Pages: {total_pages}")
    print(f"• PDF File Size: {file_size_mb:.2f} MB")
    print(f"• Target Output: {pdf_path}")
    print(f"=======================================================\n")
    
    # Copy to Artifact directory
    artifact_dir = r"C:\Users\pc\.gemini\antigravity\brain\7dc4efa0-6a8a-43ed-a734-d9d82ca0f281"
    artifact_pdf = os.path.join(artifact_dir, "TokenBrief_Minor_Project_Report_Tushar_Bansal.pdf")
    import shutil
    shutil.copy(pdf_path, artifact_pdf)
    print(f"Copied to artifact directory: {artifact_pdf}")

if __name__ == "__main__":
    build_report()
