import streamlit as st
import swisseph as swe
import base64
import os
import calendar
import urllib.parse
import time as ptime
from datetime import date, time, timedelta

# --- PAGE CONFIG (must be the very first Streamlit call) ---
st.set_page_config(page_title="Voharvod Calculator", page_icon="ॐ", layout="centered")

# --- CONFIGURE SWISS EPHEMERIS ---
swe.set_sid_mode(swe.SIDM_LAHIRI)

# ─────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────
KASHMIRI_MONTHS = {
    11: "Chetra", 0: "Vaisakh", 1: "Zeth",  2: "Haar",
     3: "Shravun", 4: "Bhadrapeth", 5: "Ashid", 6: "Kartik",
     7: "Monjhor", 8: "Poh", 9: "Magh", 10: "Phagun"
}

TITHI_NAMES = {
    1: "Pratipada", 2: "Duya",      3: "Truya",     4: "Chorum",  5: "Ponchum",
    6: "Sheyam",    7: "Satam",     8: "Ashtami",   9: "Navam",  10: "Dahom",
   11: "Kahyom",   12: "Duvadashi",13: "Truvahsh", 14: "Chodah", 15: "Purnima/Amavasya"
}

RASHI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)", 
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)", 
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

RASHI_EMOJIS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", 
    "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

ASTRO_DETAILS = {
    "rashi": {
        0: {"ruler": "Mars (Mangal)", "traits": "Energetic, dynamic, courageous, natural leader"},
        1: {"ruler": "Venus (Shukra)", "traits": "Patient, artistic, reliable, loves stability"},
        2: {"ruler": "Mercury (Budh)", "traits": "Expressive, witty, highly adaptable, intellectual"},
        3: {"ruler": "Moon (Chandra)", "traits": "Intuitive, nurturing, deeply emotional, imaginative"},
        4: {"ruler": "Sun (Surya)", "traits": "Confident, generous, fiercely loyal, charismatic"},
        5: {"ruler": "Mercury (Budh)", "traits": "Analytical, precise, helpful, methodical observer"},
        6: {"ruler": "Venus (Shukra)", "traits": "Harmonious, charming, diplomatic, values justice"},
        7: {"ruler": "Mars/Ketu", "traits": "Intense, passionate, deeply perceptive, resilient"},
        8: {"ruler": "Jupiter (Guru)", "traits": "Optimistic, philosophical, freedom-loving, wise"},
        9: {"ruler": "Saturn (Shani)", "traits": "Disciplined, ambitious, practical, highly organized"},
        10: {"ruler": "Saturn (Shani)", "traits": "Humanitarian, independent, original thinker, loyal"},
        11: {"ruler": "Jupiter (Guru)", "traits": "Empathetic, artistic, deeply intuitive, spiritual"}
    }
}

TRANSITION_LABELS = {
    "⚠️ Time Transition: If born before": "Before Transition",
    "⚠️ Time Transition: If born after": "After Transition"
}

MONTH_OPTIONS = ["Chetra", "Vaisakh", "Zeth", "Haar", "Shravun", "Bhadrapeth", "Ashid", "Kartik", "Monjhor", "Poh", "Magh", "Phagun"]
REVERSE_MONTHS = {v: k for k, v in KASHMIRI_MONTHS.items()}
REVERSE_TITHIS = {v: k for k, v in TITHI_NAMES.items()}

SRINAGAR_SUNRISE_UTC = {
    1: 1.75, 2: 1.50, 3: 1.00, 4: 0.50, 5: 0.00, 6: -0.15,
    7: 0.00, 8: 0.25, 9: 0.75, 10: 1.00, 11: 1.50, 12: 1.80
}

# ─────────────────────────────────────────────────────────────
#  CACHED CORE MATH FUNCTIONS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_precise_panchang(check_date, exact_time=None):
    year, month, day = check_date.year, check_date.month, check_date.day
    if exact_time:
        utc_hour = (exact_time.hour + (exact_time.minute / 60.0)) - 5.5
    else:
        utc_hour = SRINAGAR_SUNRISE_UTC[month]
        
    jd_check = swe.julday(year, month, day, utc_hour)
    sun_pos, _ = swe.calc_ut(jd_check, swe.SUN, swe.FLG_SIDEREAL)
    moon_pos, _ = swe.calc_ut(jd_check, swe.MOON, swe.FLG_SIDEREAL)
    
    diff = (moon_pos[0] - sun_pos[0]) % 360
    tithi = int(diff / 12) + 1
    
    last_diff = diff
    month_idx = int(sun_pos[0] / 30)
    
    for h in range(1, 35 * 24):
        jd_search = jd_check - (h / 24.0)
        s_pos_b, _ = swe.calc_ut(jd_search, swe.SUN, swe.FLG_SIDEREAL)
        m_pos_b, _ = swe.calc_ut(jd_search, swe.MOON, swe.FLG_SIDEREAL)
        b_diff = (m_pos_b[0] - s_pos_b[0]) % 360
        
        if b_diff > 345 and last_diff < 15:
            month_idx = int(s_pos_b[0] / 30)
            break
        last_diff = b_diff
        
    if tithi > 15:
        month_idx = (month_idx + 1) % 12
    return tithi, month_idx

@st.cache_data(ttl=3600)
def get_astro_details(check_date, exact_time=None):
    year, month, day = check_date.year, check_date.month, check_date.day
    utc_hour = (exact_time.hour + (exact_time.minute / 60.0)) - 5.5 if exact_time else SRINAGAR_SUNRISE_UTC[month]
    jd_check = swe.julday(year, month, day, utc_hour)
    moon_pos, _ = swe.calc_ut(jd_check, swe.MOON, swe.FLG_SIDEREAL)
    return int(moon_pos[0] / (360 / 27.0)), int(moon_pos[0] / 30.0)

@st.cache_data(ttl=3600)
def find_voharvod_for_year(b_tithi, b_m_idx, target_year, dob_month=None, dob_day=None):
    if dob_month and dob_day:
        if dob_month == 2 and dob_day == 29:
            expected_anchor = date(target_year, 2, 28) if not calendar.isleap(target_year) else date(target_year, 2, 29)
        else:
            expected_anchor = date(target_year, dob_month, dob_day)
    else:
        expected_month = ((b_m_idx + 4) % 12) or 12
        expected_anchor = date(target_year, expected_month, 15)

    start_search = expected_anchor - timedelta(days=125)
    raw_matches = []
    prev_tithi, prev_date, prev_m_idx = None, None, None
    
    for d in range(0, 250):
        curr = start_search + timedelta(days=d)
        c_tithi, c_m_idx = get_precise_panchang(curr, exact_time=None)
        is_match = False
        match_date = curr
        
        if c_tithi == b_tithi:
            is_match = True
        elif prev_tithi is not None:
            cont_c = c_tithi if c_tithi >= prev_tithi else c_tithi + 30
            cont_b = b_tithi if b_tithi >= prev_tithi else b_tithi + 30
            if prev_tithi < cont_b < cont_c and (cont_c - prev_tithi) <= 2:
                is_match = True
                match_date = prev_date
                
        if is_match and (c_m_idx == b_m_idx or (prev_m_idx is not None and prev_m_idx == b_m_idx)):
            if match_date not in raw_matches:
                raw_matches.append(match_date)
                    
        prev_tithi, prev_date, prev_m_idx = c_tithi, curr, c_m_idx
    
    events = []
    for m in raw_matches:
        if not events: events.append(m)
        elif (m - events[-1]).days > 2: events.append(m)
        else: events[-1] = m 
            
    return (events[-1], len(events) > 1) if events else (None, False)

# ─────────────────────────────────────────────────────────────
#  STYLING & THEMING ENVIRONMENT
# ─────────────────────────────────────────────────────────────
def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as image:
            encoded_string = base64.b64encode(image.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(248, 248, 250, 0.95), rgba(248, 248, 250, 0.95)), url(data:image/jpeg;base64,{encoded_string});
            background-size: cover; background-position: top center; background-repeat: no-repeat; background-attachment: fixed;
            color: #121212; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }}
        h1, h2, h3 {{ color: #1C1C1E !important; font-weight: 700 !important; }}
        .voharvod-card {{
            background: linear-gradient(135deg, #FF9933 0%, #FF5E62 100%);
            color: white !important; padding: 30px; border-radius: 16px;
            box-shadow: 0 10px 25px rgba(255, 94, 98, 0.3); margin: 25px 0; text-align: center;
        }}
        .voharvod-card h1 {{ color: white !important; margin: 15px 0 5px 0 !important; font-size: 2.6rem !important; border: none !important; text-shadow: 0 2px 4px rgba(0,0,0,0.15); }}
        .badge-pill {{ background: rgba(255,255,255,0.2); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; display: inline-block; margin-bottom: 10px; }}
        .astro-strip {{ background: rgba(0,0,0,0.06); padding: 12px; border-radius: 8px; margin-top: 15px; font-size: 0.9rem; text-align: left; }}
        
        div[data-baseweb="select"] input {{
            pointer-events: none !important;
            caret-color: transparent !important;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .stApp {{ background-image: linear-gradient(rgba(18, 18, 20, 0.96), rgba(18, 18, 20, 0.96)), url(data:image/jpeg;base64,{encoded_string}); color: #F2F2F7; }}
            h1, h2, h3 {{ color: #F8F8FA !important; }}
        }}
        </style>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  APP DIALOGS
# ─────────────────────────────────────────────────────────────
@st.dialog("🙏 Welcome to the Voharvod Calculator")
def welcome_guide():
    st.markdown("""
    This tool accurately calculates your traditional Kashmiri lunar birthday (**Voharvod**) for any year you choose. It perfectly mirrors the authentic **Vijayshwar Jantri**, mathematically handling complex rules like *Adhik Maas* (Leap Months) and *Kshaya Tithis* (Skipped Sunrises).
    
    ### 🔍 Important Fields to Know:
    - **Actual Birth Date:** Your standard English date of birth. *Providing this also calculates your Nakshatra and Rashi!*
    - **Approximate Time:** In the lunar calendar, a day can change in the middle of the afternoon. If unsure, leave it on **Default** — the app will safely check a wide window (12 PM to 10 PM) to prevent errors.
    - **Known Birth Tithi:** If you already know your exact lunar phase (e.g., *Ashtami*), select it here.
    - **🔄 Direct Profile Toggle:** Don't know your English birth date? Flip this switch to directly construct your Kashmiri birth profile.
    
    *Once your date is calculated, you can instantly sync it to your Apple or Google Calendar.*
    """)
    if st.button("Get Started ✨", use_container_width=True):
        st.session_state["welcome_guide_dismissed"] = True
        st.rerun()

# --- OFFICIAL COMPONENT-WRAPPED FEEDBACK BOX ---
@st.dialog("💬 Support & Feedback")
def feedback_form():
    st.components.v1.html("""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin: 0; padding: 5px;
        background-color: transparent;
    }
    .fb-container { display: flex; flex-direction: column; gap: 14px; }
    .fb-label { font-weight: 600; font-size: 14px; color: #1C1C1E; margin-bottom: 4px; display: block; }
    .fb-radio-label {
        display: flex; align-items: center; gap: 8px; font-size: 14px;
        cursor: pointer; padding: 4px 0; color: #121212;
    }
    .fb-input, .fb-textarea {
        width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #D1D1D6;
        background-color: #FFFFFF; color: #121212; font-size: 14px; box-sizing: border-box;
        font-family: inherit;
    }
    .fb-textarea { resize: none; }
    .fb-btn {
        background-color: #1C1C1E; color: white; padding: 12px; border: none;
        border-radius: 8px; font-weight: 600; font-size: 15px; cursor: pointer;
        width: 100%; margin-top: 5px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        font-family: inherit; transition: background-color 0.2s;
    }
    .fb-btn:hover { background-color: #3A3A3C; }
    
    @media (prefers-color-scheme: dark) {
        body { color: #F8F8FA; }
        .fb-label { color: #F8F8FA; }
        .fb-radio-label { color: #F8F8FA; }
        .fb-input, .fb-textarea { background-color: #2C2C2E; border-color: #48484A; color: #F8F8FA; }
        .fb-btn { background-color: #3A3A3C; border: 1px solid #48484A; }
        .fb-btn:hover { background-color: #48484A; }
    }
    </style>
    </head>
    <body>
    <div class="fb-container">
        <div>
            <label class="fb-label">What would you like to share?</label>
            <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 6px;">
                <label class="fb-radio-label">
                    <input type="radio" name="fb_type_group" id="type_general" value="general" checked onchange="stToggleFields()"> General Feedback / Suggestion
                </label>
                <label class="fb-radio-label">
                    <input type="radio" name="fb_type_group" id="type_bug" value="bug" onchange="stToggleFields()"> Report an Incorrect Date
                </label>
            </div>
        </div>
        
        <div>
            <label class="fb-label">Your Email Address (So we can reply!)</label>
            <input type="email" id="fb_email" class="fb-input" placeholder="name@example.com">
        </div>
        
        <div id="bug_fields" style="display: none; flex-direction: column; gap: 14px;">
            <div>
                <label class="fb-label">What is your actual Date of Birth?</label>
                <input type="text" id="fb_dob" class="fb-input" placeholder="e.g., 22 Jan 1960">
            </div>
            <div>
                <label class="fb-label">What is the Expected Result? (As per Jantri)</label>
                <input type="text" id="fb_expected" class="fb-input" placeholder="e.g., 10 Feb 2026">
            </div>
            <div>
                <label class="fb-label">What Result did the App give you?</label>
                <input type="text" id="fb_actual" class="fb-input" placeholder="e.g., 30 Jan 2027">
            </div>
            <div>
                <label class="fb-label">Any other details? (Time of birth, Year being checked, etc.)</label>
                <textarea id="fb_notes" class="fb-textarea" rows="2" placeholder="Provide extra context here..."></textarea>
            </div>
        </div>
        
        <div id="general_fields" style="display: flex; flex-direction: column; gap: 14px;">
            <div>
                <label class="fb-label">Your Feedback / Suggestion</label>
                <textarea id="fb_text" class="fb-textarea" rows="4" placeholder="Type your suggestion here..."></textarea>
            </div>
        </div>
        
        <button type="button" class="fb-btn" onclick="stSendFeedback()">✉️ Send Feedback via Email</button>
    </div>
    
    <script>
    function stToggleFields() {
        var type = document.querySelector('input[name="fb_type_group"]:checked').value;
        if(type === "bug") {
            document.getElementById("bug_fields").style.display = "flex";
            document.getElementById("general_fields").style.display = "none";
        } else {
            document.getElementById("bug_fields").style.display = "none";
            document.getElementById("general_fields").style.display = "flex";
        }
    }
    
    function stSendFeedback() {
        var type = document.querySelector('input[name="fb_type_group"]:checked').value;
        var email = document.getElementById("fb_email").value.trim();
        
        if(!email) {
            alert("⚠️ Please provide your email address before sending.");
            return;
        }
        
        var subject = "";
        var body = "";
        
        if(type === "bug") {
            subject = "Bug Report: Voharvod Calculator";
            var dob = document.getElementById("fb_dob").value;
            var expected = document.getElementById("fb_expected").value;
            var actual = document.getElementById("fb_actual").value;
            var notes = document.getElementById("fb_notes").value;
            
            body = "User Email: " + email + "\\n\\n--- BUG REPORT ---\\nActual DOB: " + dob + "\\nExpected Result: " + expected + "\\nApp Result: " + actual + "\\n\\nAdditional Notes:\\n" + notes;
        } else {
            subject = "Feedback: Voharvod Calculator";
            var text = document.getElementById("fb_text").value;
            
            if(!text.trim()) {
                alert("⚠️ Please type your feedback message before sending.");
                return;
            }
            body = "User Email: " + email + "\\n\\n--- FEEDBACK ---\\n" + text;
        }
        
        var mailtoUrl = "mailto:kawshashank@gmail.com?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
        window.location.href = mailtoUrl;
    }
    </script>
    </body>
    </html>
    """, height=560)

# ─────────────────────────────────────────────────────────────
#  MAIN APP INTERFACE LAYOUT
# ─────────────────────────────────────────────────────────────
add_bg_from_local("mahadev.jpg")

has_shared_params = "month" in st.query_params and "paksha" in st.query_params and "tithi" in st.query_params

if "welcome_guide_dismissed" not in st.session_state:
    st.session_state["welcome_guide_dismissed"] = False

if not st.session_state["welcome_guide_dismissed"] and not has_shared_params:
    st.session_state["welcome_guide_dismissed"] = True
    welcome_guide()

st.markdown("<h2 style='text-align: center; margin-bottom: 25px;'>Voharvod Calculator</h2>", unsafe_allow_html=True)

col_top1, col_top2, col_top3 = st.columns(3)
with col_top1:
    default_name = st.query_params["name"] if "name" in st.query_params else ""
    person_name = st.text_input("Name (Optional)", placeholder="e.g. Shashank", value=default_name)
with col_top2:
    default_year = int(st.query_params["year"]) if "year" in st.query_params else 2026
    target_year = st.number_input("Find Kashmiri birthday for year", min_value=2024, max_value=2100, value=default_year)

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
default_toggle = True if has_shared_params else False
direct_mode = st.toggle("🔄 I don't know my exact birth date, but I know my Kashmiri Birth Profile", value=default_toggle)

if direct_mode:
    with col_top3:
        st.text_input("Actual Birth Date", value="N/A (Direct Profile Mode)", disabled=True)
    
    st.info("Select your exact traditional birth profile below:")
    col_d1, col_d2, col_d3 = st.columns(3)
    
    def_m = MONTH_OPTIONS.index(st.query_params["month"]) if has_shared_params and st.query_params["month"] in MONTH_OPTIONS else 0
    def_p = ["Zoon Pachh (Bright)", "Gatta Pachh (Dark)"].index("Zoon Pachh (Bright)" if "Zoon" in st.query_params.get("paksha", "") else "Gatta Pachh (Dark)") if has_shared_params else 0
    def_t = list(TITHI_NAMES.values()).index(st.query_params["tithi"]) if has_shared_params and st.query_params["tithi"] in TITHI_NAMES.values() else 7
    
    with col_d1: sel_month = st.selectbox("Month", MONTH_OPTIONS, index=def_m)
    with col_d2: sel_paksha = st.selectbox("Paksha", ["Zoon Pachh (Bright)", "Gatta Pachh (Dark)"], index=def_p)
    with col_d3: sel_tithi = st.selectbox("Tithi", list(TITHI_NAMES.values()), index=def_t)
    
    dob_calc = None
    time_block = "Default (Safest bet)"
    override_tithi_name = "Unknown / Calculate for me"
    input_key = f"{person_name}-{target_year}-direct-{sel_month}-{sel_paksha}-{sel_tithi}"
else:
    with col_top3:
        dob = st.date_input("Actual Birth Date", value=date(2000, 12, 31), min_value=date(1940, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        time_block = st.selectbox("Approximate Time of Birth", ["Default (Safest bet)", "Early Morning (Before 8 AM)", "Late Morning (8 AM - 12 PM)", "Afternoon (12 PM - 4 PM)", "Evening (4 PM - 8 PM)", "Night (After 8 PM)"])
    with col_s2:
        override_tithi_name = st.selectbox("Known Birth Tithi (Optional)", ["Unknown / Calculate for me"] + list(TITHI_NAMES.values()))
        
    sel_month = sel_paksha = sel_tithi = None
    dob_calc = dob
    input_key = f"{person_name}-{target_year}-calc-{dob}-{time_block}-{override_tithi_name}"

st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns([4, 1])
with col_btn1:
    calc_triggered = st.button("✨ Find My Voharvod", use_container_width=True, type="primary")
with col_btn2:
    if st.button("💬 Feedback", use_container_width=True):
        feedback_form()

if calc_triggered or has_shared_params:
    st.session_state["active_key"] = input_key
    if calc_triggered:
        st.session_state["balloons_ready"] = True

# ─────────────────────────────────────────────────────────────
#  CALCULATION ENGINE RUNTIME
# ─────────────────────────────────────────────────────────────
if "active_key" in st.session_state and st.session_state["active_key"] == input_key:
    try:
        profiles_to_check = []
        mode_flag = "standard"
        if direct_mode:
            mode_flag = "direct"
            b_m_idx = REVERSE_MONTHS[sel_month]
            b_num = REVERSE_TITHIS[sel_tithi]
            b_tithi = b_num + 15 if "Gatta Pachh" in sel_paksha else b_num
            profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": None, "nakshatra": None, "rashi": None})
        else:
            if override_tithi_name != "Unknown / Calculate for me":
                mode_flag = "override"
                b_tithi, b_m_idx = get_precise_panchang(dob_calc, time(12, 0))
                n_idx, r_idx = get_astro_details(dob_calc, time(12, 0))
                for num, name in TITHI_NAMES.items():
                    if name == override_tithi_name:
                        b_tithi = num + 15 if b_tithi > 15 else num
                        break
                profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": None, "nakshatra": NAKSHATRA_NAMES[n_idx], "rashi": RASHI_NAMES[r_idx], "r_idx": r_idx})
            elif time_block == "Default (Safest bet)":
                t1, m1 = get_precise_panchang(dob_calc, time(12, 0))
                t2, m2 = get_precise_panchang(dob_calc, time(22, 0))
                n1, r1 = get_astro_details(dob_calc, time(12, 0))
                
                if t1 != t2 or m1 != m2:
                    mode_flag = "default_split"
                    low, high = 12 * 60, 22 * 60
                    transition_min = high
                    while low <= high:
                        mid = (low + high) // 2
                        test_t = time(mid // 60, mid % 60)
                        t_test, m_test = get_precise_panchang(dob_calc, test_t)
                        if t_test != t1 or m_test != m1:
                            transition_min = mid
                            high = mid - 1
                        else:
                            low = mid + 1
                    transition_time_str = time(transition_min // 60, transition_min % 60).strftime("%I:%M %p").lstrip("0")
                    
                    profiles_to_check.append({"tithi": t1, "m_idx": m1, "desc": f"⚠️ Time Transition: If born before {transition_time_str}", "nakshatra": NAKSHATRA_NAMES[n1], "rashi": RASHI_NAMES[r1], "r_idx": r1})
                    n2, r2 = get_astro_details(dob_calc, time(22, 0))
                    profiles_to_check.append({"tithi": t2, "m_idx": m2, "desc": f"⚠️ Time Transition: If born after {transition_time_str}", "nakshatra": NAKSHATRA_NAMES[n2], "rashi": RASHI_NAMES[r2], "r_idx": r2})
                else:
                    mode_flag = "default_single"
                    profiles_to_check.append({"tithi": t1, "m_idx": m1, "desc": None, "nakshatra": NAKSHATRA_NAMES[n1], "rashi": RASHI_NAMES[r1], "r_idx": r1})
            else:
                TIME_MAP = {
                    "Early Morning (Before 8 AM)": time(6, 0), "Late Morning (8 AM - 12 PM)": time(10, 0),
                    "Afternoon (12 PM - 4 PM)": time(14, 0), "Evening (4 PM - 8 PM)": time(18, 0), "Night (After 8 PM)": time(22, 0)
                }
                anchor = TIME_MAP[time_block]
                b_tithi, b_m_idx = get_precise_panchang(dob_calc, anchor)
                n1, r1 = get_astro_details(dob_calc, anchor)
                profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": None, "nakshatra": NAKSHATRA_NAMES[n1], "rashi": RASHI_NAMES[r1], "r_idx": r1})

        if mode_flag == "default_split":
            st.error("⚠️ **Lunar Phase Transition Detected!** A traditional lunar day changed between 12:00 PM and 10:00 PM on your actual birth date. We have pinpointed the exact transition time. Please select the profile below that matches your birth time or family records.")

        if st.session_state.get("balloons_ready", False):
            st.balloons()
            st.session_state["balloons_ready"] = False

        for idx, p in enumerate(profiles_to_check):
            f_date, is_leap = find_voharvod_for_year(p["tithi"], p["m_idx"], target_year, dob_month=dob_calc.month if dob_calc else None, dob_day=dob_calc.day if dob_calc else None)
            
            if f_date:
                b_num = p["tithi"] - 15 if p["tithi"] > 15 else p["tithi"]
                p_paksha = "Gatta Pachh" if p["tithi"] > 15 else "Zoon Pachh"
                tithi_str = f"{KASHMIRI_MONTHS[p['m_idx']]} {p_paksha} {TITHI_NAMES[b_num]}"
                
                date_suffix = f_date.strftime("%d %b")
                if person_name.strip():
                    event_title = f"{person_name.strip()} Kashmiri Birthday {date_suffix}"
                    header_title = f"{person_name.strip()}'s Voharvod"
                else:
                    event_title = f"Kashmiri Birthday {date_suffix}"
                    header_title = "Kashmiri Lunar Birthday"
                
                astro_meta = ""
                if p.get("rashi"):
                    r_info = ASTRO_DETAILS["rashi"].get(p["r_idx"], {"ruler": "Unknown", "traits": ""})
                    astro_meta = f"✨ <b>Rashi:</b> {p['rashi']} (Ruled by {r_info['ruler']}) <br> 🌸 <b>Traits:</b> {r_info['traits']} <br> 🌟 <b>Nakshatra:</b> {p['nakshatra']}"
                
                if p.get("desc"):
                    st.markdown(f"<p style='color: #FF5E62; font-weight: bold; font-size: 1.1rem; margin-top: 20px; margin-bottom: -15px;'>{p['desc']}</p>", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="voharvod-card">
                    <div class="badge-pill">📋 Traditional Birth Profile</div>
                    <div style="font-size: 1.2rem; opacity: 0.95; font-weight: 500;">{header_title}</div>
                    <h1>{f_date.strftime('%A, %d %B %Y')}</h1>
                    <div style="margin-top: 10px; font-weight: 600; opacity: 0.9;">Matches: {tithi_str}</div>
                    {f'<div class="astro-strip">{astro_meta}</div>' if astro_meta else ''}
                </div>
                """, unsafe_allow_html=True)
                
                if is_leap:
                    st.caption("🌟 **Leap Month Bridge:** Adjusted calendar offsets automatically to align correctly with native Jantri calculations.")
                    
                col_b1, col_b2 = st.columns(2)
                start_str = f_date.strftime("%Y%m%d")
                gcal_end_str = (f_date + timedelta(days=1)).strftime("%Y%m%d")
                gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(event_title)}&dates={start_str}/{gcal_end_str}&details=Traditional%20Profile:%20{urllib.parse.quote(tithi_str)}"
                ics_data = f"BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VEVENT\nDTSTART;VALUE=DATE:{start_str}\nDURATION:P1D\nSUMMARY:{event_title}\nDESCRIPTION:Profile: {tithi_str}\nEND:VEVENT\nEND:VCALENDAR".replace('\n', '\r\n')
                
                with col_b1: st.link_button("📅 Add to Google Calendar", gcal_url, use_container_width=True, key=f"gcal_{idx}")
                with col_b2: st.download_button("📥 Download .ics (Apple / Outlook)", data=ics_data, file_name=f"voharvod_{idx}.ics", mime="text/calendar", use_container_width=True, key=f"ics_{idx}")
                
                with st.expander("📅 View Upcoming Birthdays (Next 5 Years)", expanded=False):
                    label_suffix = " (Before Transition)" if p.get("desc") and "before" in p["desc"].lower() else " (After Transition)" if p.get("desc") else ""
                    st.write(f"Plan ahead! Here is when your Voharvod{label_suffix} falls in the coming years:")
                    for next_y in range(target_year + 1, target_year + 6):
                        ny_date, _ = find_voharvod_for_year(p["tithi"], p["m_idx"], next_y, dob_month=dob_calc.month if dob_calc else None, dob_day=dob_calc.day if dob_calc else None)
                        if ny_date:
                            st.write(f"• **{next_y}:** {ny_date.strftime('%A, %d %B %Y')}")
                            
                with st.expander("🔗 Share this calculation with family"):
                    share_params = {"month": KASHMIRI_MONTHS[p['m_idx']], "paksha": p_paksha, "tithi": TITHI_NAMES[b_num], "year": str(target_year)}
                    if person_name.strip():
                        share_params["name"] = person_name.strip()
                    share_url = f"https://voharvod-alert.streamlit.app/?{urllib.parse.urlencode(share_params)}"
                    st.code(share_url, language=None)
            else:
                st.error("Astronomical combination mismatch or target bounds exceeded.")
    except Exception as e:
        st.error(f"Execution Error Core context: {e}")
else:
    st.markdown("""
    <div style='text-align: center; padding: 40px 20px; color: #8E8E93;'>
        <div style='font-size: 3.5rem; margin-bottom: 10px;'>🌙</div>
        <div style='font-size: 1.1rem; font-weight: 500;'>Ready to align with Jantri</div>
        <div style='font-size: 0.9rem; opacity: 0.8; margin-top: 4px;'>Fill in your birth details above and click 'Find My Voharvod' to see your traditional date.</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  DISTRIBUTION & UTILITIES FOOTER
# ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("<h3 style='text-align: center; border-bottom: none; margin-top: 0px;'>Share this App</h3>", unsafe_allow_html=True)

APP_URL = "https://voharvod-alert.streamlit.app"
whatsapp_msg = urllib.parse.quote(f"Check out the Kashmiri Voharvod Calculator! Save this link to easily find traditional birthdays: {APP_URL}")
fb_url = urllib.parse.quote(APP_URL)

WA_SVG = '<svg viewBox="0 0 448 512" style="width:18px;height:18px;fill:white;margin-right:8px;vertical-align:middle;"><path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3 18.7-68.1-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-5.5-2.8-23.2-8.5-44.2-27.1-16.4-14.6-27.4-32.6-30.6-37.9-3.2-5.5-.3-8.5 2.5-11.2 2.5-2.5 5.5-6.6 8.3-9.9 2.8-3.3 3.7-5.6 5.6-9.2 1.9-3.7.9-6.6-.5-9.2-1.4-2.8-12.5-30.1-17.1-41.1-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 13.2 5.7 23.5 9.2 31.6 11.8 13.3 4.2 25.4 3.6 35 2.2 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>'
FB_SVG = '<svg viewBox="0 0 512 512" style="width:18px;height:18px;fill:white;margin-right:8px;vertical-align:middle;"><path d="M504 256C504 119 393 8 256 8S8 119 8 256c0 123.78 90.69 226.38 209.25 245.26V312.6h-66.38V256h66.38V212.87c0-65.51 38.89-101.62 98.45-101.62 28.53 0 58.31 5.1 58.31 5.1v64h-32.81c-32.36 0-42.48 20.06-42.48 40.63V256h72.06l-11.51 56.6h-60.55v188.66C413.31 482.38 504 379.78 504 256z"/></svg>'
IG_SVG = '<svg viewBox="0 0 448 512" style="width:18px;height:18px;fill:white;margin-right:8px;vertical-align:middle;"><path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7 74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"/></svg>'

st.markdown(f"""
<div style="display:flex;gap:12px;justify-content:center;margin-top:10px;margin-bottom:15px;flex-wrap:wrap;">
    <a href="https://wa.me/?text={whatsapp_msg}" target="_blank" class="share-btn-bottom" style="text-decoration:none;background-color:#25D366;color:white;padding:10px 18px;border-radius:8px;font-weight:600;font-size:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2);transition:all 0.2s;white-space:nowrap;">{WA_SVG}WhatsApp</a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={fb_url}" target="_blank" class="share-btn-bottom" style="text-decoration:none;background-color:#1877F2;color:white;padding:10px 18px;border-radius:8px;font-weight:600;font-size:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2);transition:all 0.2s;white-space:nowrap;">{FB_SVG}Facebook</a>
    <a href="https://instagram.com" target="_blank" class="share-btn-bottom" style="text-decoration:none;background:linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);color:white;padding:10px 18px;border-radius:8px;font-weight:600;font-size:15px;box-shadow:0 4px 10px rgba(0,0,0,0.2);transition:all 0.2s;white-space:nowrap;">{IG_SVG}Instagram</a>
</div>
""", unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: #8E8E93; font-size: 12px; margin-top:-5px; margin-bottom: 10px;'><i>To share on Instagram, copy the link below and paste it into your Story or DM!</i></p>", unsafe_allow_html=True)
st.code(APP_URL, language=None)

st.markdown("<p style='text-align: center; color: #888888; font-size: 13px; margin-top: 30px; margin-bottom: 15px;'>🔒 <b>Privacy First:</b> This calculator runs safely in your browser. We do not save, store, or track any names, birth dates, or personal information.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888; font-size: 12px; margin-top: 0px; margin-bottom: 4px;'>With traditional insights from Saroj Kaw</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888888; font-size: 12px; margin-top: 0px;'>Built for our community by Shashank Kaw</p>", unsafe_allow_html=True)