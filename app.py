import streamlit as st
import pandas as pd
import os
import io
import json
import base64
import html
from datetime import datetime
import streamlit.components.v1 as components

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 1. Page Configuration
st.set_page_config(page_title="AC - Audit Checklist", layout="wide", initial_sidebar_state="collapsed")

# 2. State Initialization
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = "LIGHT MODE"
if 'is_mobile_view' not in st.session_state:
    st.session_state.is_mobile_view = False
if 'audit_data' not in st.session_state:
    st.session_state.audit_data = None
if 'show_upload_modal' not in st.session_state:
    st.session_state.show_upload_modal = True
if 'deck_version' not in st.session_state:
    st.session_state.deck_version = 0

header_fields = ["lead_auditor", "co_auditor", "entity_name", "entity_location", "pocs", "type_of_audit", "custom_audit_type"]
for field in header_fields:
    if field not in st.session_state:
        st.session_state[field] = ""

is_dark = (st.session_state.theme_mode == "DARK MODE")
is_mobile = st.session_state.is_mobile_view

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### SYSTEM CONTROLS")
    
    st.markdown("<p style='font-size: 11px; font-weight: 900; margin-bottom: 4px;'>THEME SELECTOR</p>", unsafe_allow_html=True)
    theme_btn_label = "SWITCH TO DARK" if not is_dark else "SWITCH TO LIGHT"
    if st.button(theme_btn_label, key="trigger_theme_toggle", use_container_width=True):
        st.session_state.theme_mode = "DARK MODE" if not is_dark else "LIGHT MODE"
        st.rerun()

    st.markdown("<hr style='margin: 10px 0; border: 1px solid #000;'>", unsafe_allow_html=True)

    st.markdown("<p style='font-size: 11px; font-weight: 900; margin-bottom: 4px;'>DEVICE ENGINE</p>", unsafe_allow_html=True)
    device_btn_label = "SWITCH TO MOBILE" if not is_mobile else "SWITCH TO DESKTOP"
    if st.button(device_btn_label, key="trigger_device_toggle", use_container_width=True):
        st.session_state.is_mobile_view = not is_mobile
        st.rerun()

    st.markdown("<hr style='margin: 10px 0; border: 1px solid #000;'>", unsafe_allow_html=True)
    if st.button("UPLOAD QUESTIONNAIRE", use_container_width=True):
        st.session_state.show_upload_modal = True
        st.session_state.audit_data = None
        st.session_state.deck_version += 1
        st.rerun()
        
    st.markdown("<hr style='margin: 10px 0; border: 1px solid #000;'>", unsafe_allow_html=True)
    metric_placeholder = st.empty()
    questions_placeholder = st.empty()

# 3. Dynamic Neo-Brutalist Theme Variables
if st.session_state.theme_mode == "LIGHT MODE":
    bg_color = "#F3F4F6"        
    text_color = "#000000"      
    card_bg = "#FF9F43"         
    sidebar_bg = "#FF9F43"      
    sidebar_card_bg = "#FF6B6B" 
    sidebar_card_text = "#000000"
    sidebar_text = "#000000"
    shadow_color = "#00FFC6"    
else:
    bg_color = "#121212"        
    text_color = "#FFFFFF"      
    card_bg = "#2D3748"         
    sidebar_bg = "#1E293B"      
    sidebar_card_bg = "#B83B5E" 
    sidebar_card_text = "#FFFFFF"
    sidebar_text = "#FFFFFF"    
    shadow_color = "#00FFC6"    

# Field shading & text remain locked to Light Mode styling across all modes
field_bg = "#FFFFFF"
field_text_color = "#000000"
field_placeholder_color = "#4A5568"
field_border_color = "#000000"
field_shadow_color = "#000000"

# 4. Global CSS Stylesheet
MODAL_OVERRIDE_CSS = """
<style>
div[data-testid="stDialog"],
div[data-testid="stModal"],
[data-baseweb="modal"],
[role="dialog"] {
    --primary-color: #000000 !important;
    --background-color: #E2E8F0 !important;
    --secondary-background-color: #FFFFFF !important;
    --text-color: #000000 !important;
    color-scheme: light !important;
}

div[data-testid="stDialog"] > div,
div[data-testid="stModal"] > div,
[data-baseweb="modal"] > div,
[data-baseweb="modal"] > div > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    max-width: none !important;
    width: auto !important;
    overflow: visible !important;
}

body div[data-testid="stDialog"] [role="dialog"],
body div[data-testid="stModal"] [role="dialog"],
body [data-baseweb="modal"] [role="dialog"] {
    background-color: #E2E8F0 !important;
    background: #E2E8F0 !important;
    border-radius: 36px !important;
    border: 3px solid rgba(0, 0, 0, 0.25) !important;
    box-shadow: 0px 24px 60px rgba(0, 0, 0, 0.5) !important;
    padding: 40px 32px 30px 32px !important;
    width: 680px !important;
    max-width: 92vw !important;
    margin: 0 auto !important;
    box-sizing: border-box !important;
    color: #000000 !important;
}

body div[data-testid="stDialog"] h1,
body div[data-testid="stDialog"] h2,
body div[data-testid="stDialog"] h3,
body div[data-testid="stDialog"] p,
body div[data-testid="stDialog"] span,
body div[data-testid="stDialog"] label {
    color: #000000 !important;
}

body div[data-testid="stDialog"] button[aria-label="Close"] {
    display: none !important;
}

body div[data-testid="stDialog"] section[data-testid*="Dropzone"],
body div[data-testid="stDialog"] [data-testid="stFileUploader"] section {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 3px solid #000000 !important;
    border-radius: 12px !important;
    box-shadow: 4px 4px 0px #000000 !important;
    padding: 24px 20px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    color: #000000 !important;
}

body div[data-testid="stDialog"] section[data-testid*="Dropzone"] * {
    color: #000000 !important;
    fill: #000000 !important;
    stroke: #000000 !important;
    opacity: 1 !important;
}

body div[data-testid="stDialog"] section[data-testid*="Dropzone"] button,
body div[data-testid="stDialog"] button[kind="secondary"] {
    background-color: #4D96FF !important;
    background: #4D96FF !important;
    color: #000000 !important;
    border: 2px solid #000000 !important;
    box-shadow: 2px 2px 0px #000000 !important;
    border-radius: 6px !important;
    font-weight: 900 !important;
}

body div[data-testid="stDialog"] section[data-testid*="Dropzone"] button * {
    color: #000000 !important;
    font-weight: 900 !important;
}

.modal-link-download {
    text-align: right;
    margin-top: 14px;
}
.modal-link-download a {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-size: 11px !important;
    font-weight: 900 !important;
    color: #000000 !important;
    text-decoration: underline !important;
    letter-spacing: 0.5px !important;
}
</style>
"""

st.markdown(
    f"""
    <style>
    *:focus, *:focus-visible, *:active {{
        outline: none !important;
        box-shadow: none !important;
    }}
    
    .stApp {{
        background-color: {bg_color} !important;
    }}

    h1, h2, h3, p, span:not([data-testid="stIconMaterial"]), label, .stMarkdown p {{
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: 900 !important;
        color: {text_color} !important;
    }}

    button[data-testid="stSidebarCollapseButton"] *,
    button[data-testid="stExpandSidebarButton"] * {{
        font-size: 0px !important;
        color: transparent !important;
    }}

    button[data-testid="stSidebarCollapseButton"]::after,
    button[data-testid="stExpandSidebarButton"]::after {{
        content: "" !important;
        display: inline-block !important;
        width: 22px !important;
        height: 18px !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'%3E%3Cpath d='M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
    }}

    button[data-testid="stSidebarCollapseButton"],
    button[data-testid="stExpandSidebarButton"] {{
        background-color: {field_bg} !important;
        border: 3px solid {field_border_color} !important;
        box-shadow: 4px 4px 0px {field_shadow_color} !important;
        border-radius: 0px !important;
        padding: 6px 10px !important;
        cursor: pointer !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
    }}
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span:not([data-testid="stIconMaterial"]),
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {{
        color: {sidebar_text} !important;
    }}
    
    .brutal-logo {{
        display: inline-block;
        background-color: #000000;
        color: #FFFFFF !important;
        font-family: 'Impact', 'Arial Black', sans-serif !important;
        font-size: 64px !important;
        padding: 10px 25px;
        border: 5px solid {text_color};
        box-shadow: 8px 8px 0px {shadow_color};
        margin-bottom: 5px;
        letter-spacing: 2px;
    }}
    
    .brutal-card {{
        background-color: {card_bg} !important;
        border: 4px solid {"#000000" if not is_dark else "#4A5568"};
        box-shadow: 8px 8px 0px {"#000000" if not is_dark else "#00FFC6"};
        padding: 24px;
        margin-bottom: 25px;
        border-radius: 0px !important;
    }}
    .brutal-card * {{
        color: {text_color} !important;
    }}

    .nested-indent {{
        margin-left: 36px !important;
        border-left: 8px solid {"#000000" if not is_dark else "#00FFC6"} !important;
    }}
    
    .brutal-sidebar-card {{
        background-color: {sidebar_card_bg} !important;
        border: 3px solid #000000;
        box-shadow: 4px 4px 0px #000000;
        padding: 12px 14px;
        margin-bottom: 15px;
    }}

    /* Form Controls: Retain Light-Mode Shading & Typography Across All Modes */
    div[data-testid="stToggle"] {{
        background-color: {field_bg} !important;
        padding: 8px 12px !important;
        border: 3px solid {field_border_color} !important;
        box-shadow: 4px 4px 0px {field_shadow_color} !important;
        border-radius: 0px !important;
    }}

    div.stRadio > div {{
        background-color: {field_bg} !important;
        padding: 10px;
        border: 3px solid {field_border_color} !important;
        box-shadow: 4px 4px 0px {field_shadow_color} !important;
        border-radius: 0px !important;
    }}
    div.stRadio label, div.stRadio p, div.stRadio span {{
        color: {field_text_color} !important;
    }}

    div[data-testid="stRadioGap"] {{
        font-size: 0px !important;
        color: transparent !important;
        width: 16px !important;
        background-color: #000000 !important;
        margin: 0px 10px !important;
        border: 1px solid #000000 !important;
    }}
    
    div.stTextInput > div > div > input {{
        background-color: {field_bg} !important;
        border: 3px solid {field_border_color} !important;
        box-shadow: 4px 4px 0px {field_shadow_color} !important;
        border-radius: 0px !important;
        color: {field_text_color} !important;
        -webkit-text-fill-color: {field_text_color} !important;
        font-weight: 900 !important;
    }}

    div.stTextInput > div > div > input::placeholder {{
        color: {field_placeholder_color} !important;
        -webkit-text-fill-color: {field_placeholder_color} !important;
        opacity: 1 !important;
    }}
    
    div.stTextInput > div > div > input:focus {{
        border: 3px solid {field_border_color} !important;
        box-shadow: 4px 4px 0px {field_shadow_color} !important;
    }}

    div.stSelectbox > div > div {{
        border: 3px solid {field_border_color} !important;
        box-shadow: 4px 4px 0px {field_shadow_color} !important;
        border-radius: 0px !important;
        background-color: {field_bg} !important;
        color: {field_text_color} !important;
    }}

    div.stSelectbox > div > div * {{
        color: {field_text_color} !important;
        fill: {field_text_color} !important;
    }}

    ul[data-baseweb="menu"] {{
        background-color: {field_bg} !important;
        border: 3px solid {field_border_color} !important;
        border-radius: 0px !important;
    }}
    ul[data-baseweb="menu"] li, ul[data-baseweb="menu"] li * {{
        color: {field_text_color} !important;
        background-color: {field_bg} !important;
    }}
    ul[data-baseweb="menu"] li:hover {{
        background-color: #FFD93D !important;
    }}
    
    div.stButton > button, div.stDownloadButton > button {{
        background-color: {"#4D96FF" if not is_dark else "#00FFC6"} !important; 
        color: #000000 !important;
        font-weight: 900 !important;
        border: 4px solid #000000 !important;
        box-shadow: 5px 5px 0px #000000 !important;
        border-radius: 0px !important;
        transition: none !important;
    }}
    div.stButton > button:active, div.stDownloadButton > button:active {{
        box-shadow: 0px 0px 0px #000000 !important;
        transform: translate(5px, 5px);
    }}
    
    .status-sticker {{
        display: inline-block;
        padding: 6px 12px;
        border: 2px solid #000000;
        font-weight: 900;
        color: #000000 !important;
        text-transform: uppercase;
        box-shadow: 2px 2px 0px #000000;
    }}
    .safe {{ background-color: #6BCB77; }}
    .vuln {{ background-color: #FFA45B; }}
    .breach {{ background-color: #FF6B6B; }}
    .pending {{ background-color: #CCCCCC; }}

    .badge-cue {{
        display: inline-block;
        padding: 3px 8px;
        border: 2px solid #000000;
        font-weight: 900;
        color: #000000 !important;
        box-shadow: 2px 2px 0px #000000;
        font-size: 11px;
        margin-right: 8px;
        margin-top: 6px;
    }}
    .target-cue {{ background-color: #FFD93D; }}
    .info-cue {{ background-color: #FFFFFF; font-weight: bold; width: fit-content; max-width: 100%; }}
    </style>
    """ + MODAL_OVERRIDE_CSS, 
    unsafe_allow_html=True
)

FINDING_OPTIONS = ["SELECT FINDING CATEGORY", "Major NC", "Minor NC", "Observation", "Information"]

# 5. SANITIZATION & TEMPLATE UTILITIES
def sanitize_csv_cell(val):
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{s}"
    return s

def get_demo_template():
    demo_df = pd.DataFrame({
        "ID": ["1", "2", "3", "4", "5"],
        "Domain": ["Physical Security", "Physical Security", "Physical Security", "Access Control", "Access Control"],
        "Control Mapping // Source": ["ISO 27001 A.11.1.2", "ISO 27001 A.11.1.2", "ISO 27001 A.11.1.3", "ISO 27001 A.9.1.1", "ISO 27001 A.9.1.2"],
        "Questions": [
            "Is an automated clean-agent fire suppression system installed?",
            "Are manual clean-agent fire extinguishers present within 15 meters of all server racks?",
            "Are annual pressure test and maintenance logs verified for the clean-agent system?",
            "Is biometric authentication enforced at the main facility perimeter?",
            "Is a strict 100% visitor manual escort policy enforced with physical badge logs?"
        ],
        "Target": ["Facility Manager", "Safety Officer", "Facility Engineer", "Security Lead", "Reception / Guards"],
        "Expectation": ["Yes", "Yes", "Yes", "Yes", "Yes"],
        "Parent_ID": ["", "1", "1", "", "4"],
        "Trigger_Value": ["", "No", "Yes", "", "No"],
        "Info": [
            "Verify installation of FM-200, Novec 1230, or Inergen systems.",
            "Physically check gauge levels and inspect inspection tags.",
            "Request vendor maintenance logs for the previous 12 months.",
            "Verify dual-factor authentication or biometric readers at perimeter.",
            "Check visitor logbook for timestamped entries and physical escort badges."
        ]
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        demo_df.to_excel(writer, index=False, sheet_name="AuditChecklist")
    return buf.getvalue()

def clean_id_str(val, fallback_idx=None):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() in ("nan", "none"):
        return None
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str if val_str.startswith("ID-") else f"ID-{val_str}"

def parse_df_records(df):
    """Normalize dataframe columns and build checklist records with strict logic preservation."""
    df = df.dropna(how='all')
    if df.empty:
        return []

    # Detect header presence
    first_row = [str(c).strip().lower() for c in df.iloc[0].values]
    if any(h in first_row for h in ['id', 'domain', 'questions', 'question', 'expectation']):
        df.columns = [str(c).strip() for c in df.iloc[0].values]
        df = df.iloc[1:].copy()
    else:
        df = df.copy()

    # Column name mapping lookup
    col_map = {}
    for idx, c in enumerate(df.columns):
        cl = str(c).strip().lower()
        if cl in ['id', 'ref', 'reference']:
            col_map['id'] = c
        elif cl in ['domain', 'sector']:
            col_map['domain'] = c
        elif 'control' in cl or 'mapping' in cl or 'source' in cl:
            col_map['source'] = c
        elif 'question' in cl:
            col_map['question'] = c
        elif 'target' in cl:
            col_map['target'] = c
        elif 'expectation' in cl:
            col_map['expectation'] = c
        elif 'parent' in cl:
            col_map['parent_id'] = c
        elif 'trigger' in cl:
            col_map['trigger_value'] = c
        elif 'info' in cl or 'detail' in cl or 'guidance' in cl:
            col_map['info'] = c

    # Fallback to absolute positional indexing (Columns A to I: 0 to 8)
    cols = list(df.columns)
    id_col = col_map.get('id', cols[0] if len(cols) > 0 else None)
    domain_col = col_map.get('domain', cols[1] if len(cols) > 1 else None)
    source_col = col_map.get('source', cols[2] if len(cols) > 2 else None)
    question_col = col_map.get('question', cols[3] if len(cols) > 3 else None)
    target_col = col_map.get('target', cols[4] if len(cols) > 4 else None)
    expectation_col = col_map.get('expectation', cols[5] if len(cols) > 5 else None)
    parent_col = col_map.get('parent_id', cols[6] if len(cols) > 6 else None)
    trigger_col = col_map.get('trigger_value', cols[7] if len(cols) > 7 else None)
    info_col = col_map.get('info', cols[8] if len(cols) > 8 else None)

    processed_records = []
    for idx, (_, row) in enumerate(df.iterrows()):
        raw_id = row[id_col] if id_col else f"{idx+1}"
        raw_domain = row[domain_col] if domain_col else "General"
        raw_source = row[source_col] if source_col else ""
        raw_question = row[question_col] if question_col else "Requirement missing."
        raw_target = row[target_col] if target_col else ""
        raw_expectation = row[expectation_col] if expectation_col else "Yes"
        raw_parent = row[parent_col] if parent_col else None
        raw_trigger = row[trigger_col] if trigger_col else "Yes"
        raw_info = row[info_col] if info_col else ""

        clean_id = clean_id_str(raw_id, idx+1) or f"ROW-{idx+1}"
        clean_domain = str(raw_domain).strip() if pd.notna(raw_domain) else "General"
        clean_source = str(raw_source).strip() if pd.notna(raw_source) and str(raw_source).lower() != "nan" else ""
        clean_question = str(raw_question).strip() if pd.notna(raw_question) else "Requirement detail missing."
        clean_target = str(raw_target).strip() if pd.notna(raw_target) and str(raw_target).lower() != "nan" else ""
        clean_expectation = str(raw_expectation).strip().upper() if pd.notna(raw_expectation) else "YES"
        clean_parent = clean_id_str(raw_parent)
        clean_trigger = str(raw_trigger).strip().upper() if pd.notna(raw_trigger) and str(raw_trigger).strip() != "" and str(raw_trigger).lower() != "nan" else "YES"
        clean_info = str(raw_info).strip() if pd.notna(raw_info) and str(raw_info).lower() != "nan" else ""

        processed_records.append({
            "id": clean_id,
            "domain": clean_domain,
            "source": clean_source,
            "question": clean_question,
            "target": clean_target,
            "expectation": clean_expectation,
            "parent_id": clean_parent,
            "trigger_value": clean_trigger,
            "info": clean_info,
            "key": f"ctrl_{idx}_{clean_id.replace(' ', '_')}"
        })
    return processed_records

def parse_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, header=None, nrows=2000)
        else:
            df = pd.read_excel(uploaded_file, header=None, nrows=2000)
        records = parse_df_records(df)
        if not records:
            st.error("Uploaded checklist contains no valid rows.")
            return None
        return records
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None

EXCEL_FILE = "iso_checklist.xlsx"
CSV_FILE = "iso_checklist.csv"

def load_default_checklist():
    df = None
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, header=None, nrows=2000)
    elif os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, header=None, nrows=2000)
        
    if df is not None and not df.empty:
        records = parse_df_records(df)
        if records:
            return records
            
    return [
        {
            "id": f"ID-{i}",
            "domain": "Domain Name",
            "source": "Control Name",
            "question": f"Question {i}",
            "target": "",
            "expectation": "YES",
            "parent_id": None,
            "trigger_value": "YES",
            "info": "",
            "key": f"ctrl_{i-1}_ID-{i}"
        }
        for i in range(1, 4)
    ]

# 6. POP-UP MODAL DIALOG
@st.dialog(" ")
def upload_questionnaire_dialog():
    st.markdown(MODAL_OVERRIDE_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center; margin-top: -10px; margin-bottom: 25px;">
            <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: #000000 !important;">
                PLEASE UPLOAD THE QUESTIONNAIRE
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    uploaded_file = st.file_uploader(
        "UPLOAD QUESTIONNAIRE",
        type=["xlsx", "xls", "csv"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        parsed_data = parse_uploaded_file(uploaded_file)
        if parsed_data:
            st.session_state.audit_data = parsed_data
            st.session_state.responses = {item['key']: {"status": None, "evidence": "", "finding_category": None} for item in parsed_data}
            st.session_state.show_upload_modal = False
            st.session_state.deck_version += 1
            st.rerun()

    template_b64 = base64.b64encode(get_demo_template()).decode()
    st.markdown(
        f"""
        <div class="modal-link-download">
            <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{template_b64}" download="sample_questionnaire.xlsx">
                DOWNLOAD SAMPLE QUESTIONNAIRE
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

if st.session_state.show_upload_modal and st.session_state.audit_data is None:
    upload_questionnaire_dialog()

if st.session_state.audit_data is None:
    st.session_state.audit_data = load_default_checklist()

processed_data = st.session_state.audit_data

if 'responses' not in st.session_state or not st.session_state.responses:
    st.session_state.responses = {item['key']: {"status": None, "evidence": "", "finding_category": None} for item in processed_data}
else:
    for item in processed_data:
        if item['key'] not in st.session_state.responses:
            st.session_state.responses[item['key']] = {"status": None, "evidence": "", "finding_category": None}

id_to_key_map = {item['id']: item['key'] for item in processed_data}

# Unaltered Hierarchy Trigger Logic
def is_node_active(item):
    parent_id = item.get('parent_id')
    if not parent_id:
        return True
    parent_key = id_to_key_map.get(parent_id)
    if not parent_key:
        return True
    parent_status = st.session_state.responses.get(parent_key, {}).get('status')
    required_trigger = item.get('trigger_value', 'YES').upper()
    return parent_status == required_trigger

def update_status(ctrl_key, radio_key):
    st.session_state.responses[ctrl_key]['status'] = st.session_state[radio_key]

def update_evidence(ctrl_key, ev_key):
    st.session_state.responses[ctrl_key]['evidence'] = st.session_state[ev_key]

def update_finding(ctrl_key, find_key):
    val = st.session_state[find_key]
    st.session_state.responses[ctrl_key]['finding_category'] = val if val != "SELECT FINDING CATEGORY" else None

audit_type_options = ["TYPE OF AUDIT", "Datacenter", "Field/Location", "Custom"]

def get_resolved_audit_type():
    sel = st.session_state.type_of_audit
    if sel == "Custom":
        return st.session_state.custom_audit_type.strip() or "Custom"
    if sel and sel != "TYPE OF AUDIT":
        return sel
    return ""

# =========================================================================
# 7. HEADER SCOPE SECTION
# =========================================================================
logo_col, fields_col = st.columns([2, 6])
with logo_col:
    st.markdown('<div class="brutal-logo">AC</div>', unsafe_allow_html=True)
    st.caption("AUDIT CHECKLIST")

with fields_col:
    r1_col1, r1_col2 = st.columns(2)
    with r1_col1:
        st.session_state.lead_auditor = st.text_input("Lead Auditor Label", value=st.session_state.lead_auditor, placeholder="LEAD AUDITOR", label_visibility="collapsed")
    with r1_col2:
        st.session_state.co_auditor = st.text_input("Co Auditor Label", value=st.session_state.co_auditor, placeholder="CO AUDITOR", label_visibility="collapsed")

    r2_col1, r2_col2 = st.columns(2)
    with r2_col1:
        st.session_state.entity_name = st.text_input("Entity Name Label", value=st.session_state.entity_name, placeholder="ENTITY NAME", label_visibility="collapsed")
    with r2_col2:
        st.session_state.entity_location = st.text_input("Entity Location Label", value=st.session_state.entity_location, placeholder="ENTITY LOCATION", label_visibility="collapsed")

    r3_col1, r3_col2 = st.columns(2)
    with r3_col1:
        st.session_state.pocs = st.text_input("Point of Contacts Label", value=st.session_state.pocs, placeholder="POINT OF CONTACTS / AUDITEES", label_visibility="collapsed")
    with r3_col2:
        audit_type_idx = audit_type_options.index(st.session_state.type_of_audit) if st.session_state.type_of_audit in audit_type_options else 0
        st.session_state.type_of_audit = st.selectbox("Type of Audit Label", audit_type_options, index=audit_type_idx, label_visibility="collapsed")
        if st.session_state.type_of_audit == "Custom":
            st.session_state.custom_audit_type = st.text_input(
                "Custom Audit Type Label",
                value=st.session_state.custom_audit_type,
                placeholder="SPECIFY CUSTOM TYPE OF AUDIT...",
                label_visibility="collapsed"
            )

st.markdown("---")

# =========================================================================
# 8. TARGET NODE DOMAIN & TARGET AUDITEE SELECTORS (SIDE-BY-SIDE)
# =========================================================================
domains = ["ALL SECTORS"] + sorted(list(set(item['domain'] for item in processed_data if item.get('domain'))))
available_targets = sorted(list(set(item['target'] for item in processed_data if item.get('target'))))
targets_list = ["ALL TARGETS"] + available_targets

f_col1, f_col2 = st.columns(2)
with f_col1:
    selected_domain = st.selectbox("TARGET NODE DOMAIN", domains, key=f"domain_selector_{st.session_state.deck_version}")
with f_col2:
    selected_target = st.selectbox("TARGET AUDITEE", targets_list, key=f"target_selector_{st.session_state.deck_version}")

st.markdown("---")

# Helper filter check
def matches_filters(item):
    domain_match = (selected_domain == "ALL SECTORS" or item.get('domain') == selected_domain)
    target_match = (selected_target == "ALL TARGETS" or item.get('target') == selected_target)
    return domain_match and target_match

# =========================================================================
# 9. CONDITIONAL ENGINE: MOBILE vs DESKTOP
# =========================================================================

if st.session_state.is_mobile_view:
    # ---------------------------------------------------------------------
    # MOBILE ENGINE: TOUCH DECK SWIPER
    # ---------------------------------------------------------------------
    filtered_data = [item for item in processed_data if matches_filters(item)]
    
    deck_items = [{
        "id": d["id"],
        "domain": d["domain"],
        "source": d.get("source") or "",
        "question": d["question"],
        "target": d.get("target") or "",
        "info": d.get("info") or "",
        "key": d["key"],
        "parent_id": d["parent_id"],
        "trigger_value": d["trigger_value"],
        "expectation": d["expectation"],
        "status": st.session_state.responses[d["key"]]["status"] or "UNANSWERED",
        "evidence": st.session_state.responses[d["key"]]["evidence"] or "",
        "finding_category": st.session_state.responses[d["key"]].get("finding_category") or ""
    } for d in filtered_data]
    
    meta_info = {
        "lead": st.session_state.lead_auditor or "N/A",
        "co": st.session_state.co_auditor or "N/A",
        "entity_name": st.session_state.entity_name or "N/A",
        "entity_loc": st.session_state.entity_location or "N/A",
        "pocs": st.session_state.pocs or "N/A",
        "audit_type": get_resolved_audit_type() or "N/A",
        "date": datetime.now().strftime("%d/%m/%Y")
    }
    
    deck_json_str = json.dumps(deck_items)
    meta_json_str = json.dumps(meta_info)

    standalone_swiper_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        * {{
            box-sizing: border-box;
            font-family: 'Courier New', monospace;
            user-select: none;
            -webkit-user-select: none;
        }}
        body {{
            margin: 0;
            padding: 4px 0 20px 0;
            background-color: transparent;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-y: auto;
            overflow-x: hidden;
        }}
        .hud-container {{
            display: flex;
            width: 95%;
            max-width: 360px;
            gap: 8px;
            margin-bottom: 8px;
        }}
        .hud-card {{
            flex: 1;
            background-color: #FF6B6B;
            border: 2px solid #000;
            box-shadow: 2px 2px 0 #000;
            padding: 6px 8px;
            text-align: center;
        }}
        .hud-score {{
            font-size: 14px;
            font-weight: 900;
            color: #000;
        }}
        .hud-label {{
            font-size: 9px;
            font-weight: 900;
            color: #000;
            letter-spacing: 0.5px;
        }}
        .stack-stage {{
            position: relative;
            width: 95%;
            max-width: 360px;
            min-height: 250px;
            height: auto;
        }}
        .bg-card-2 {{
            position: absolute;
            width: 90%;
            height: 220px;
            left: 5%;
            top: 18px;
            background-color: #000000;
            border: 3px solid #000;
            transform: rotate(3deg);
            z-index: 1;
        }}
        .bg-card-1 {{
            position: absolute;
            width: 92%;
            height: 220px;
            left: 4%;
            top: 9px;
            background-color: #FFA45B;
            border: 3px solid #000;
            transform: rotate(-2.5deg);
            z-index: 2;
            padding: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            text-align: center;
        }}
        .active-card {{
            position: relative;
            width: 94%;
            min-height: 220px;
            margin-left: 3%;
            background-color: #FF9F43;
            border: 3px solid #000000;
            box-shadow: 5px 5px 0px #000000;
            padding: 12px 10px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            text-align: center;
            font-weight: 900;
            color: #000000;
            touch-action: none;
            cursor: grab;
            z-index: 3;
            transition: transform 0.15s ease, background-color 0.2s, opacity 0.2s;
        }}
        .card-header {{
            display: flex;
            flex-direction: column;
            width: 100%;
            font-size: 10px;
            background: #000000;
            color: #FFFFFF;
            padding: 4px 6px;
            text-align: left;
            gap: 2px;
        }}
        .header-top-row {{
            display: flex;
            justify-content: space-between;
            width: 100%;
            font-weight: 900;
        }}
        .card-body {{
            font-size: 13px;
            line-height: 1.3;
            margin: 6px 0;
            overflow-wrap: break-word;
            width: 100%;
        }}
        .meta-cues-row {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            width: 100%;
            margin-bottom: 6px;
        }}
        .cue-pill {{
            border: 1.5px solid #000000;
            box-shadow: 2px 2px 0px #000000;
            padding: 3px 6px;
            font-size: 9.5px;
            font-weight: 900;
            text-align: left;
            color: #000000;
            line-height: 1.25;
        }}
        .card-footer {{
            font-size: 9px;
            border-top: 1.5px dashed #000000;
            padding-top: 4px;
            width: 100%;
            line-height: 1.2;
            margin-top: 4px;
        }}
        .evidence-box {{
            width: 95%;
            max-width: 360px;
            margin-top: 6px;
        }}
        .evidence-input {{
            width: 100%;
            background: #FFFFFF;
            border: 2px solid #000000;
            box-shadow: 2px 2px 0 #000000;
            padding: 6px 8px;
            font-size: 11px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            outline: none;
            box-sizing: border-box;
        }}
        .deviation-tray {{
            display: none;
            width: 95%;
            max-width: 360px;
            background-color: #FFA45B;
            border: 2px solid #000000;
            box-shadow: 3px 3px 0 #000000;
            padding: 6px 8px;
            margin-top: 6px;
            gap: 6px;
            flex-direction: column;
        }}
        .deviation-tray.active {{
            display: flex !important;
        }}
        .finding-select {{
            width: 100%;
            background: #FFFFFF;
            border: 2px solid #000000;
            padding: 6px 8px;
            font-size: 11px;
            font-weight: 900;
            font-family: 'Courier New', monospace;
            color: #000000;
            outline: none;
            box-sizing: border-box;
            cursor: pointer;
        }}
        .confirm-btn {{
            width: 100%;
            background-color: #000000;
            color: #FFFFFF;
            border: 2px solid #000000;
            padding: 6px 0;
            font-size: 11px;
            font-weight: 900;
            cursor: pointer;
            text-align: center;
        }}
        .nav-controls {{
            display: flex;
            width: 95%;
            max-width: 360px;
            gap: 6px;
            margin-top: 6px;
        }}
        .nav-btn {{
            flex: 1;
            background-color: #4D96FF;
            color: #000;
            border: 2px solid #000;
            box-shadow: 2px 2px 0 #000;
            font-weight: 900;
            font-size: 11px;
            padding: 6px 0;
            cursor: pointer;
        }}
        .nav-btn:active {{
            transform: translate(1px, 1px);
            box-shadow: 0px 0px 0 #000;
        }}
        .status-indicator {{
            width: 95%;
            max-width: 360px;
            background-color: #E2B659;
            border: 2px solid #000;
            box-shadow: 2px 2px 0 #000;
            text-align: center;
            padding: 4px;
            font-weight: 900;
            font-size: 10.5px;
            margin-top: 6px;
        }}
        .export-tray {{
            display: flex;
            width: 95%;
            max-width: 360px;
            gap: 8px;
            margin-top: 10px;
            margin-bottom: 8px;
        }}
        .export-btn {{
            flex: 1;
            background-color: #6BCB77;
            color: #000;
            border: 2px solid #000;
            box-shadow: 2px 2px 0 #000;
            font-weight: 900;
            font-size: 10.5px;
            padding: 7px 0;
            cursor: pointer;
        }}
        .export-btn:active {{
            transform: translate(1px, 1px);
            box-shadow: 0px 0px 0 #000;
        }}
    </style>
    </head>
    <body>
        <div class="hud-container">
            <div class="hud-card">
                <div id="hudScore" class="hud-score">0%</div>
                <div class="hud-label">ODOMETER</div>
            </div>
            <div class="hud-card">
                <div id="hudAnswered" class="hud-score">0/0</div>
                <div class="hud-label">EVALUATED</div>
            </div>
        </div>

        <div class="stack-stage">
            <div class="bg-card-2"></div>
            
            <div id="nextCard" class="bg-card-1">
                <div class="card-header">
                    <div class="header-top-row">
                        <span id="nextId">ID</span>
                        <span id="nextCount">0/0</span>
                    </div>
                    <div id="nextMapping" style="font-size: 8.5px; opacity: 0.85;"></div>
                </div>
                <div id="nextText" style="font-size: 12px; line-height: 1.25; margin: auto 0; opacity: 0.85;"></div>
                <div style="font-size: 8.5px; opacity: 0.7;">NEXT IN QUEUE</div>
            </div>

            <div id="swipeCard" class="active-card">
                <div class="card-header">
                    <div class="header-top-row">
                        <span id="curId">ID</span>
                        <span id="curCount">0/0</span>
                    </div>
                    <div id="curMapping" style="font-size: 8.5px; opacity: 0.95; letter-spacing: 0.3px;"></div>
                </div>

                <div id="curText" class="card-body"></div>

                <div class="meta-cues-row">
                    <div id="curTarget" class="cue-pill" style="background:#FFD93D; display:none;"></div>
                    <div id="curInfo" class="cue-pill" style="background:#FFFFFF; font-weight:normal; max-height:48px; overflow-y:auto; display:none;"></div>
                </div>

                <div class="card-footer">
                    SWIPE LEFT (NO) | SWIPE RIGHT (YES)<br>
                    DOUBLE TAP (PARTIAL)
                </div>
            </div>
        </div>

        <div class="evidence-box">
            <input type="text" id="evidenceInput" class="evidence-input" placeholder="INPUT ARTIFACT OR GAP STATEMENTS..." oninput="handleEvidenceChange(this.value)">
        </div>

        <div id="deviationTray" class="deviation-tray">
            <div style="font-size: 10px; font-weight: 900; color: #000; text-align: center;">
                DEVIATION DETECTED: CLASSIFY FINDING
            </div>
            <select id="findingSelect" class="finding-select" onchange="handleFindingChange(this.value)">
                <option value="">SELECT FINDING CATEGORY</option>
                <option value="Major NC">Major NC</option>
                <option value="Minor NC">Minor NC</option>
                <option value="Observation">Observation</option>
                <option value="Information">Information</option>
            </select>
            <button class="confirm-btn" onclick="confirmDeviationNext()">CONFIRM & NEXT</button>
        </div>

        <div class="nav-controls">
            <button class="nav-btn" onclick="goPrev()">PREV</button>
            <button class="nav-btn" style="background-color: #FFA45B;" onclick="triggerAnswer('PARTIAL')">PARTIAL</button>
            <button class="nav-btn" onclick="goNext()">NEXT</button>
        </div>

        <div id="statusBox" class="status-indicator">
            CARD 1 STATUS: UNANSWERED
        </div>

        <div class="export-tray">
            <button class="export-btn" onclick="downloadCSV()">EXPORT CSV</button>
            <button class="export-btn" style="background-color: #00FFC6;" onclick="printSummaryReport()">PRINT REPORT</button>
        </div>

        <script>
            const rawDeck = {deck_json_str};
            const meta = {meta_json_str};
            let currentIndex = 0;

            const swipeCard = document.getElementById('swipeCard');
            const nextCard = document.getElementById('nextCard');
            const statusBox = document.getElementById('statusBox');
            const evidenceInput = document.getElementById('evidenceInput');
            const deviationTray = document.getElementById('deviationTray');
            const findingSelect = document.getElementById('findingSelect');
            const hudScore = document.getElementById('hudScore');
            const hudAnswered = document.getElementById('hudAnswered');

            function getActiveVisibleDeck() {{
                const statusMap = {{}};
                rawDeck.forEach(d => {{ statusMap[d.id] = d.status; }});

                return rawDeck.filter(item => {{
                    if (!item.parent_id) return true;
                    const pStatus = statusMap[item.parent_id];
                    const reqTrigger = (item.trigger_value || 'YES').toUpperCase();
                    return pStatus === reqTrigger;
                }});
            }}

            function updateHUD() {{
                const activeDeck = getActiveVisibleDeck();
                const total = activeDeck.length;
                let answered = 0;
                for (let i = 0; i < total; i++) {{
                    if (activeDeck[i].status === 'YES' || activeDeck[i].status === 'NO' || activeDeck[i].status === 'PARTIAL') {{
                        answered++;
                    }}
                }}
                const progressPct = total > 0 ? Math.round((answered / total) * 100) : 0;
                hudScore.innerText = progressPct + '%';
                hudAnswered.innerText = answered + '/' + total;
            }}

            function renderDeck() {{
                const activeDeck = getActiveVisibleDeck();
                const total = activeDeck.length;

                if (currentIndex >= total) {{
                    currentIndex = Math.max(0, total - 1);
                }}

                if (currentIndex < total && total > 0) {{
                    const cur = activeDeck[currentIndex];
                    document.getElementById('curId').innerText = cur.id;
                    document.getElementById('curCount').innerText = (currentIndex + 1) + '/' + total;
                    
                    const srcStr = cur.source ? ' // ' + cur.source : '';
                    document.getElementById('curMapping').innerText = cur.id + ' // ' + cur.domain + srcStr;
                    
                    const prefix = cur.parent_id ? `[SUB-REQ OF ${{cur.parent_id}}] ` : '';
                    document.getElementById('curText').innerText = prefix + cur.question;
                    
                    const targetEl = document.getElementById('curTarget');
                    if (cur.target) {{
                        targetEl.innerText = 'TARGET: ' + cur.target;
                        targetEl.style.display = 'block';
                    }} else {{
                        targetEl.style.display = 'none';
                    }}

                    const infoEl = document.getElementById('curInfo');
                    if (cur.info) {{
                        infoEl.innerText = 'INFO: ' + cur.info;
                        infoEl.style.display = 'block';
                    }} else {{
                        infoEl.style.display = 'none';
                    }}

                    evidenceInput.value = cur.evidence || '';
                    statusBox.innerText = 'CARD ' + (currentIndex + 1) + ' STATUS: ' + cur.status;

                    const isDeviated = (cur.status === 'YES' || cur.status === 'NO') && (cur.status !== (cur.expectation || 'YES').toUpperCase());
                    if (isDeviated) {{
                        deviationTray.classList.add('active');
                        findingSelect.value = cur.finding_category || '';
                    }} else {{
                        deviationTray.classList.remove('active');
                        cur.finding_category = '';
                    }}

                    swipeCard.style.transition = 'none';
                    swipeCard.style.transform = 'translate(0px, 0px) rotate(0deg)';
                    swipeCard.style.opacity = '1';
                    
                    if (cur.status === 'YES') swipeCard.style.backgroundColor = '#6BCB77';
                    else if (cur.status === 'NO') swipeCard.style.backgroundColor = '#FF6B6B';
                    else if (cur.status === 'PARTIAL') swipeCard.style.backgroundColor = '#FFA45B';
                    else swipeCard.style.backgroundColor = '#FF9F43';
                }} else {{
                    document.getElementById('curId').innerText = 'COMPLETE';
                    document.getElementById('curCount').innerText = total + '/' + total;
                    document.getElementById('curMapping').innerText = '';
                    document.getElementById('curText').innerText = 'All applicable controls in this sector evaluated.';
                    document.getElementById('curTarget').style.display = 'none';
                    document.getElementById('curInfo').style.display = 'none';
                    statusBox.innerText = 'STATUS: AUDIT COMPLETED';
                    evidenceInput.value = '';
                    deviationTray.classList.remove('active');
                }}

                if (currentIndex + 1 < total) {{
                    const nxt = activeDeck[currentIndex + 1];
                    document.getElementById('nextId').innerText = nxt.id;
                    document.getElementById('nextCount').innerText = (currentIndex + 2) + '/' + total;
                    const nxtSrc = nxt.source ? ' // ' + nxt.source : '';
                    document.getElementById('nextMapping').innerText = nxt.id + ' // ' + nxt.domain + nxtSrc;
                    document.getElementById('nextText').innerText = nxt.question;
                    nextCard.style.display = 'flex';
                }} else {{
                    nextCard.style.display = 'none';
                }}
                updateHUD();
            }}

            function handleEvidenceChange(val) {{
                const activeDeck = getActiveVisibleDeck();
                if (currentIndex < activeDeck.length) {{
                    activeDeck[currentIndex].evidence = val;
                }}
            }}

            function handleFindingChange(val) {{
                const activeDeck = getActiveVisibleDeck();
                if (currentIndex < activeDeck.length) {{
                    activeDeck[currentIndex].finding_category = val;
                }}
            }}

            function confirmDeviationNext() {{
                const activeDeck = getActiveVisibleDeck();
                if (currentIndex < activeDeck.length - 1) {{
                    currentIndex++;
                }}
                renderDeck();
            }}

            function triggerAnswer(ans) {{
                const activeDeck = getActiveVisibleDeck();
                if (currentIndex >= activeDeck.length) return;
                
                const cur = activeDeck[currentIndex];
                cur.status = ans;
                
                const isDeviated = (ans === 'YES' || ans === 'NO') && (ans !== (cur.expectation || 'YES').toUpperCase());

                if (ans === 'YES') {{
                    swipeCard.style.transition = 'transform 0.2s ease, opacity 0.2s ease';
                    swipeCard.style.transform = isDeviated ? 'translate(0px, 0px)' : 'translateX(360px) rotate(25deg)';
                    if (!isDeviated) swipeCard.style.opacity = '0';
                }} else if (ans === 'NO') {{
                    swipeCard.style.transition = 'transform 0.2s ease, opacity 0.2s ease';
                    swipeCard.style.transform = isDeviated ? 'translate(0px, 0px)' : 'translateX(-360px) rotate(-25deg)';
                    if (!isDeviated) swipeCard.style.opacity = '0';
                }} else if (ans === 'PARTIAL') {{
                    swipeCard.style.transition = 'transform 0.15s ease';
                    swipeCard.style.backgroundColor = '#FFA45B';
                    swipeCard.style.transform = 'scale(0.92)';
                }}

                if (isDeviated) {{
                    renderDeck();
                }} else {{
                    setTimeout(() => {{
                        const updatedDeck = getActiveVisibleDeck();
                        if (currentIndex < updatedDeck.length - 1) {{
                            currentIndex++;
                        }}
                        renderDeck();
                    }}, 160);
                }}
            }}

            function goNext() {{
                const activeDeck = getActiveVisibleDeck();
                if (currentIndex < activeDeck.length - 1) {{
                    currentIndex++;
                    renderDeck();
                }}
            }}

            function goPrev() {{
                if (currentIndex > 0) {{
                    currentIndex--;
                    renderDeck();
                }}
            }}

            function sanitizeCSV(val) {{
                if (!val) return '""';
                let str = String(val);
                if (['=', '+', '-', '@', '\\t', '\\r'].includes(str.charAt(0))) {{
                    str = "'" + str;
                }}
                return '"' + str.replace(/"/g, '""') + '"';
            }}

            function downloadCSV() {{
                const activeDeck = getActiveVisibleDeck();
                let csvContent = "data:text/csv;charset=utf-8,";
                csvContent += "Lead Auditor,Co Auditor,Entity Name,Entity Location,Point of Contacts / Auditees,Type of Audit,Reference,Sector,Control Mapping // Source,Condition,Target,Status,Finding Category,Evidence,Info\\n";
                
                activeDeck.forEach(item => {{
                    const row = [
                        sanitizeCSV(meta.lead),
                        sanitizeCSV(meta.co),
                        sanitizeCSV(meta.entity_name),
                        sanitizeCSV(meta.entity_loc),
                        sanitizeCSV(meta.pocs),
                        sanitizeCSV(meta.audit_type),
                        sanitizeCSV(item.id),
                        sanitizeCSV(item.domain),
                        sanitizeCSV(item.source || ''),
                        sanitizeCSV(item.question),
                        sanitizeCSV(item.target || ''),
                        sanitizeCSV(item.status),
                        sanitizeCSV(item.finding_category || ''),
                        sanitizeCSV(item.evidence || ''),
                        sanitizeCSV(item.info || '')
                    ];
                    csvContent += row.join(",") + "\\n";
                }});

                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", `audit_manifest_${{(meta.entity_name || 'entity').replace(/\\s+/g, '_')}}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}

            function escapeHtml(text) {{
                const map = {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }};
                return String(text || '').replace(/[&<>"']/g, m => map[m]);
            }}

            function printSummaryReport() {{
                const activeDeck = getActiveVisibleDeck();
                let tableRows = '';
                activeDeck.forEach(r => {{
                    tableRows += `<tr>
                        <td style="border:1px solid #000;padding:4px;font-weight:bold;">${{escapeHtml(r.id)}}</td>
                        <td style="border:1px solid #000;padding:4px;">${{escapeHtml(r.domain)}}</td>
                        <td style="border:1px solid #000;padding:4px;">${{escapeHtml(r.source || '-')}}</td>
                        <td style="border:1px solid #000;padding:4px;">${{escapeHtml(r.question)}}</td>
                        <td style="border:1px solid #000;padding:4px;font-weight:bold;">${{escapeHtml(r.target || '-')}}</td>
                        <td style="border:1px solid #000;padding:4px;font-weight:bold;">${{escapeHtml(r.status)}}</td>
                        <td style="border:1px solid #000;padding:4px;font-weight:bold;">${{escapeHtml(r.finding_category || '-')}}</td>
                        <td style="border:1px solid #000;padding:4px;">${{escapeHtml(r.evidence || '-')}}</td>
                        <td style="border:1px solid #000;padding:4px;">${{escapeHtml(r.info || '-')}}</td>
                    </tr>`;
                }});

                const reportWindow = window.open('', '', 'width=950,height=600');
                reportWindow.document.write(`
                    <html>
                    <head><title>Preliminary Audit Report - ${{escapeHtml(meta.entity_name)}}</title></head>
                    <body style="font-family: monospace; padding: 20px;">
                        <h2>Audit Checklist Preliminary Report</h2>
                        <p><b>Date:</b> ${{escapeHtml(meta.date)}} | <b>Type of Audit:</b> ${{escapeHtml(meta.audit_type)}} | <b>Entity:</b> ${{escapeHtml(meta.entity_name)}} (${{escapeHtml(meta.entity_loc)}}) | <b>Auditor:</b> ${{escapeHtml(meta.lead)}}</p>
                        <table style="width:100%; border-collapse:collapse; font-size:11px;">
                            <thead>
                                <tr style="background:#000; color:#fff;">
                                    <th style="padding:6px; text-align:left;">ID</th>
                                    <th style="padding:6px; text-align:left;">Domain</th>
                                    <th style="padding:6px; text-align:left;">Source</th>
                                    <th style="padding:6px; text-align:left;">Requirement</th>
                                    <th style="padding:6px; text-align:left;">Target</th>
                                    <th style="padding:6px; text-align:left;">Status</th>
                                    <th style="padding:6px; text-align:left;">Category</th>
                                    <th style="padding:6px; text-align:left;">Evidence</th>
                                    <th style="padding:6px; text-align:left;">Info</th>
                                </tr>
                            </thead>
                            <tbody>${{tableRows}}</tbody>
                        </table>
                    </body>
                    </html>
                `);
                reportWindow.document.close();
                reportWindow.focus();
                reportWindow.print();
            }}

            let startX = 0, currentX = 0, isDragging = false, lastTap = 0;

            swipeCard.addEventListener('touchstart', (e) => {{
                startX = e.touches[0].clientX;
                isDragging = true;
                swipeCard.style.transition = 'none';
            }});

            swipeCard.addEventListener('touchmove', (e) => {{
                if (!isDragging) return;
                currentX = e.touches[0].clientX - startX;
                swipeCard.style.transform = `translateX(${{currentX}}px) rotate(${{currentX * 0.08}}deg)`;
                if (currentX > 35) swipeCard.style.backgroundColor = '#6BCB77';
                else if (currentX < -35) swipeCard.style.backgroundColor = '#FF6B6B';
                else swipeCard.style.backgroundColor = '#FF9F43';
            }});

            swipeCard.addEventListener('touchend', (e) => {{
                if (!isDragging) return;
                isDragging = false;
                const now = new Date().getTime();
                const diff = now - lastTap;

                if (diff < 320 && diff > 0) {{
                    triggerAnswer('PARTIAL');
                }} else {{
                    if (currentX > 65) {{
                        triggerAnswer('YES');
                    }} else if (currentX < -65) {{
                        triggerAnswer('NO');
                    }} else {{
                        swipeCard.style.transition = 'transform 0.15s ease';
                        swipeCard.style.transform = 'translate(0px, 0px) rotate(0deg)';
                        swipeCard.style.backgroundColor = '#FF9F43';
                    }}
                }}
                lastTap = new Date().getTime();
                currentX = 0;
            }});

            renderDeck();
        </script>
    </body>
    </html>
    """
    components.html(standalone_swiper_html, height=590)

else:
    # ---------------------------------------------------------------------
    # DESKTOP ENGINE: TABULAR MATRIX VIEW
    # ---------------------------------------------------------------------
    st.subheader("ACTIVE NODE COMPLIANCE MATRIX")

    for item in processed_data:
        if not matches_filters(item):
            continue
        
        if not is_node_active(item):
            continue

        ctrl_key = item['key']
        radio_widget_key = f"status_{ctrl_key}"
        ev_widget_key = f"ev_{ctrl_key}"
        find_widget_key = f"find_{ctrl_key}"

        if radio_widget_key not in st.session_state:
            st.session_state[radio_widget_key] = st.session_state.responses[ctrl_key]['status']
        if ev_widget_key not in st.session_state:
            st.session_state[ev_widget_key] = st.session_state.responses[ctrl_key]['evidence']
        if find_widget_key not in st.session_state:
            saved_find = st.session_state.responses[ctrl_key].get('finding_category')
            st.session_state[find_widget_key] = saved_find if saved_find in FINDING_OPTIONS else "SELECT FINDING CATEGORY"

        is_child = item.get('parent_id') is not None
        indent_class = "nested-indent" if is_child else ""
        escaped_parent = html.escape(str(item.get('parent_id') or ''))
        escaped_trigger = html.escape(str(item.get('trigger_value') or ''))
        child_prefix = f"[SUB-REQUIREMENT OF {escaped_parent} (ON {escaped_trigger})] " if is_child else ""

        escaped_question = html.escape(str(item['question']))
        escaped_id = html.escape(str(item['id']))
        escaped_domain = html.escape(str(item['domain']))
        escaped_source = html.escape(str(item.get('source') or ''))
        escaped_target = html.escape(str(item.get('target') or ''))
        escaped_info = html.escape(str(item.get('info') or ''))

        mapping_parts = [escaped_id, escaped_domain]
        if escaped_source and escaped_source != escaped_domain:
            mapping_parts.append(escaped_source)
        header_mapping_str = " // ".join(mapping_parts)

        target_badge = f'<div class="badge-cue target-cue">TARGET: {escaped_target}</div>' if escaped_target else ''
        info_badge = f'<div class="badge-cue info-cue"><b>INFO:</b> {escaped_info}</div>' if escaped_info else ''

        card_markup = (
            f'<div class="brutal-card {indent_class}">\n'
            f'<h3 style="margin: 0 0 5px 0;">{child_prefix}{escaped_question}</h3>\n'
            f'<p style="font-size: 13.5px; margin: 0 0 6px 0;"><b>{header_mapping_str}</b></p>\n'
            f'{target_badge}\n'
            f'{info_badge}\n'
            f'</div>'
        )

        st.markdown(card_markup, unsafe_allow_html=True)
        
        c_left, c_right = st.columns([6, 4])
        with c_left:
            st.text_input(
                label=f"Logs for {item['id']}", 
                key=ev_widget_key, 
                placeholder="INPUT ARTIFACT OR GAP STATEMENTS...", 
                label_visibility="collapsed",
                on_change=update_evidence,
                args=(ctrl_key, ev_widget_key)
            )
            
        with c_right:
            options = ["YES", "PARTIAL", "NO"]
            selected_status = st.radio(
                label=f"Status: {item['id']}", 
                options=options, 
                key=radio_widget_key, 
                horizontal=True, 
                label_visibility="collapsed",
                on_change=update_status,
                args=(ctrl_key, radio_widget_key)
            )
            
            expectation_val = item.get('expectation', 'YES').upper()
            is_deviated = (selected_status in ["YES", "NO"]) and (selected_status != expectation_val)

            if selected_status == "YES":
                if expectation_val == "YES":
                    st.markdown('<span class="status-sticker safe">COMPLIANT</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-sticker breach">NON-COMPLIANT</span>', unsafe_allow_html=True)
            elif selected_status == "NO":
                if expectation_val == "NO":
                    st.markdown('<span class="status-sticker safe">COMPLIANT</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-sticker breach">NON-COMPLIANT</span>', unsafe_allow_html=True)
            elif selected_status == "PARTIAL": 
                st.markdown('<span class="status-sticker vuln">EXCEPTION</span>', unsafe_allow_html=True)
            else: 
                st.markdown('<span class="status-sticker pending">UNANSWERED</span>', unsafe_allow_html=True)
                
        if is_deviated:
            current_find_idx = FINDING_OPTIONS.index(st.session_state[find_widget_key]) if st.session_state[find_widget_key] in FINDING_OPTIONS else 0
            st.selectbox(
                label=f"Finding Classification for {item['id']}",
                options=FINDING_OPTIONS,
                index=current_find_idx,
                key=find_widget_key,
                label_visibility="collapsed",
                on_change=update_finding,
                args=(ctrl_key, find_widget_key)
            )
        else:
            st.session_state.responses[ctrl_key]['finding_category'] = None

        st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 10. METRICS & REPORTS (FILTERED)
# ---------------------------------------------------------------------
applicable_data = [item for item in processed_data if matches_filters(item) and is_node_active(item)]
total_controls = len(applicable_data)

compliant_count = 0
partial_count = 0
non_compliant_count = 0
answered_count = 0

for item in applicable_data:
    ans = st.session_state.responses[item['key']]['status']
    exp = item.get('expectation', 'YES').upper()
    
    if ans is not None:
        answered_count += 1
        if ans == "PARTIAL":
            partial_count += 1
        elif ans == exp:
            compliant_count += 1
        else:
            non_compliant_count += 1

score = ((compliant_count * 1.0) + (partial_count * 0.5)) / total_controls if total_controls > 0 else 0
pct_score = int(score * 100)

pct_compliant = (compliant_count / total_controls * 100) if total_controls > 0 else 0
pct_partial = (partial_count / total_controls * 100) if total_controls > 0 else 0
pct_non_compliant = (non_compliant_count / total_controls * 100) if total_controls > 0 else 0

metric_placeholder.markdown(
f"""<div class="brutal-sidebar-card">
<div style="text-align: left; font-family: 'Courier New', Courier, monospace; font-size: 18px; font-weight: 900; color: {sidebar_card_text}; margin-bottom: 4px;">{pct_score}%</div>
<div style="width: 100%; height: 14px; background-color: #FFFFFF; border: 2px solid #000000; box-shadow: 2px 2px 0px #000000;">
<div style="width: {pct_score}%; height: 100%; background-color: #000000; transition: width 0.3s ease-in-out;"></div>
</div>
<div style="text-align: center; margin-top: 8px; font-family: 'Courier New', Courier, monospace; font-size: 11px; font-weight: 900; letter-spacing: 1px; color: {sidebar_card_text};">ODOMETER</div>
</div>""", 
    unsafe_allow_html=True
)

questions_placeholder.markdown(
f"""<div class="brutal-sidebar-card">
<div style="text-align: left; font-family: 'Courier New', Courier, monospace; font-size: 18px; font-weight: 900; color: {sidebar_card_text}; margin-bottom: 4px;">{answered_count}/{total_controls}</div>
<div style="width: 100%; height: 14px; background-color: #FFFFFF; border: 2px solid #000000; box-shadow: 2px 2px 0px #000000; display: flex; overflow: hidden;">
<div style="width: {pct_compliant}%; height: 100%; background-color: #6BCB77; transition: width 0.3s ease-in-out;"></div>
<div style="width: {pct_partial}%; height: 100%; background-color: #FFA45B; transition: width 0.3s ease-in-out;"></div>
<div style="width: {pct_non_compliant}%; height: 100%; background-color: #FF6B6B; transition: width 0.3s ease-in-out;"></div>
</div>
<div style="text-align: center; margin-top: 8px; font-family: 'Courier New', Courier, monospace; font-size: 11px; font-weight: 900; letter-spacing: 1px; color: {sidebar_card_text};">QUESTIONS</div>
</div>""", 
    unsafe_allow_html=True
)

# 11. EXTRACTION & REPORT GENERATION
if not st.session_state.is_mobile_view:
    st.markdown("---")
    resolved_audit_type = get_resolved_audit_type()
    export_rows = []
    for item in applicable_data:
        ctrl_key = item['key']
        status_val = st.session_state.responses[ctrl_key]['status']
        expectation_val = item.get('expectation', 'YES').upper()
        finding_cat = st.session_state.responses[ctrl_key].get('finding_category')
        
        if status_val == "YES":
            compliance_result = "COMPLIANT" if expectation_val == "YES" else "NON-COMPLIANT"
        elif status_val == "NO":
            compliance_result = "COMPLIANT" if expectation_val == "NO" else "NON-COMPLIANT"
        elif status_val == "PARTIAL":
            compliance_result = "EXCEPTION"
        else:
            compliance_result = "UNANSWERED"

        export_rows.append({
            "Lead Auditor": sanitize_csv_cell(st.session_state.lead_auditor),
            "Co Auditor": sanitize_csv_cell(st.session_state.co_auditor),
            "Entity Name": sanitize_csv_cell(st.session_state.entity_name),
            "Entity Location": sanitize_csv_cell(st.session_state.entity_location),
            "Point of Contacts / Auditees": sanitize_csv_cell(st.session_state.pocs),
            "Type of Audit": sanitize_csv_cell(resolved_audit_type),
            "Reference": sanitize_csv_cell(item['id']),
            "Sector": sanitize_csv_cell(item['domain']),
            "Control Mapping // Source": sanitize_csv_cell(item.get('source') or ''),
            "Condition": sanitize_csv_cell(item['question']),
            "Target": sanitize_csv_cell(item.get('target') or ''),
            "Audit Response": status_val if status_val is not None else "UNANSWERED",
            "Compliance Status": compliance_result,
            "Finding Category": sanitize_csv_cell(finding_cat) if finding_cat else "-",
            "Evidence": sanitize_csv_cell(st.session_state.responses[ctrl_key]['evidence']),
            "Info": sanitize_csv_cell(item.get('info') or '')
        })

    def generate_pdf_report(rows):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            rightMargin=36, 
            leftMargin=36, 
            topMargin=36, 
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12
        )
        
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=colors.HexColor('#000000'),
            spaceAfter=14
        )
        
        table_cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor('#000000')
        )
        
        table_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9.5,
            textColor=colors.white
        )
        
        elements = []
        elements.append(Paragraph("Audit Checklist Preliminary Report", title_style))
        
        date_str = datetime.now().strftime("%d/%m/%Y")
        entity_name = html.escape(st.session_state.entity_name or "[Entity Name]")
        entity_location = html.escape(st.session_state.entity_location or "[Entity Location]")
        lead_auditor = html.escape(st.session_state.lead_auditor or "[Lead Auditor]")
        co_auditor = html.escape(st.session_state.co_auditor or "[Co Auditor]")
        pocs = html.escape(st.session_state.pocs or "[Point of Contacts / Auditees]")
        audit_type = html.escape(get_resolved_audit_type() or "[Type of Audit]")
        
        intro_text = (
            f"On {date_str}, a <b>{audit_type}</b> audit of {entity_name} at {entity_location} was conducted by "
            f"{lead_auditor} and {co_auditor} in the presence of {pocs}. "
            f"Here are the preliminary audit results:"
        )
        elements.append(Paragraph(intro_text, body_style))
        elements.append(Spacer(1, 10))
        
        table_data = [
            [
                Paragraph("Reference", table_header_style),
                Paragraph("Domain", table_header_style),
                Paragraph("Source", table_header_style),
                Paragraph("Condition", table_header_style),
                Paragraph("Target", table_header_style),
                Paragraph("Status", table_header_style),
                Paragraph("Category", table_header_style),
                Paragraph("Evidence", table_header_style)
            ]
        ]
        
        for r in rows:
            table_data.append([
                Paragraph(html.escape(str(r["Reference"])), table_cell_style),
                Paragraph(html.escape(str(r["Sector"])), table_cell_style),
                Paragraph(html.escape(str(r["Control Mapping // Source"])), table_cell_style),
                Paragraph(html.escape(str(r["Condition"])), table_cell_style),
                Paragraph(html.escape(str(r["Target"])), table_cell_style),
                Paragraph(html.escape(str(r["Compliance Status"])), table_cell_style),
                Paragraph(html.escape(str(r["Finding Category"])), table_cell_style),
                Paragraph(html.escape(str(r["Evidence"])), table_cell_style)
            ])
            
        pdf_table = Table(table_data, colWidths=[40, 60, 60, 150, 60, 50, 50, 80])
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7FAFC')])
        ]))
        
        elements.append(pdf_table)
        doc.build(elements)
        
        buffer.seek(0)
        return buffer.getvalue()

    c_btn1, c_btn2 = st.columns([1, 1])

    with c_btn1:
        st.download_button(
            label="Download draft report (CSV)", 
            data=pd.DataFrame(export_rows).to_csv(index=False).encode('utf-8'), 
            file_name="audit_manifest.csv", 
            mime="text/csv"
        )

    with c_btn2:
        pdf_data = generate_pdf_report(export_rows)
        st.download_button(
            label="Download draft report (PDF)", 
            data=pdf_data, 
            file_name="audit_report.pdf", 
            mime="application/pdf"
        )