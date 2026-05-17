import streamlit as st
import swisseph as swe
import base64
import os
import urllib.parse
from datetime import date, time, timedelta

# --- CONFIGURE SWISS EPHEMERIS ---
swe.set_sid_mode(swe.SIDM_LAHIRI)

# --- BULLETPROOF KASHMIRI MONTH MAPPING ---
KASHMIRI_MONTHS = {
    11: "Chetra", 0: "Vaisakh", 1: "Zeth", 2: "Haar",
    3: "Shravun", 4: "Bhadrapeth", 5: "Ashid", 6: "Kartik",
    7: "Monjhor", 8: "Poh", 9: "Magh", 10: "Phagun"
}

TITHI_NAMES = {
    1: "Pratipada", 2: "Duya", 3: "Truya", 4: "Chorum", 5: "Ponchum",
    6: "Sheyam", 7: "Satam", 8: "Ashtami", 9: "Navam", 10: "Dahom",
    11: "Kahyom", 12: "Duvadashi", 13: "Truvahsh", 14: "Chodah", 15: "Purnima/Amavasya"
}

RASHI_NAMES = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)", 
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)", 
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

RASHI_EMOJIS = [
    "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", 
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", 
    "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", 
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

REVERSE_MONTHS = {v: k for k, v in KASHMIRI_MONTHS.items()}
REVERSE_TITHIS = {v: k for k, v in TITHI_NAMES.items()}
MONTH_OPTIONS = ["Chetra", "Vaisakh", "Zeth", "Haar", "Shravun", "Bhadrapeth", "Ashid", "Kartik", "Monjhor", "Poh", "Magh", "Phagun"]

SRINAGAR_SUNRISE_UTC = {
    1: 1.75, 2: 1.50, 3: 1.00, 4: 0.50, 5: 0.00, 6: -0.15,
    7: 0.00, 8: 0.25, 9: 0.75, 10: 1.00, 11: 1.50, 12: 1.80
}

def get_precise_panchang(check_date, exact_time=None):
    year = check_date.year
    month = check_date.month
    day = check_date.day
    
    if exact_time:
        ist_decimal = exact_time.hour + (exact_time.minute / 60.0)
        utc_hour = ist_decimal - 5.5
    else:
        utc_hour = SRINAGAR_SUNRISE_UTC[month]
        
    jd_check = swe.julday(year, month, day, utc_hour)
    flags = swe.FLG_SIDEREAL
    
    sun_pos, _ = swe.calc_ut(jd_check, swe.SUN, flags)
    moon_pos, _ = swe.calc_ut(jd_check, swe.MOON, flags)
    
    s_lon = sun_pos[0]
    m_lon = moon_pos[0]
    
    diff = (m_lon - s_lon) % 360
    tithi = int(diff / 12) + 1
    
    last_diff = diff
    month_idx = int(sun_pos[0] / 30)
    
    for h in range(1, 35 * 24):
        jd_search = jd_check - (h / 24.0)
        s_pos_b, _ = swe.calc_ut(jd_search, swe.SUN, flags)
        m_pos_b, _ = swe.calc_ut(jd_search, swe.MOON, flags)
        
        b_diff = (m_pos_b[0] - s_pos_b[0]) % 360
        
        if b_diff > 345 and last_diff < 15:
            month_idx = int(s_pos_b[0] / 30)
            break
        last_diff = b_diff
        
    if tithi > 15:
        month_idx = (month_idx + 1) % 12
        
    return tithi, month_idx

def get_astro_details(check_date, exact_time=None):
    year = check_date.year
    month = check_date.month
    day = check_date.day
    
    if exact_time:
        ist_decimal = exact_time.hour + (exact_time.minute / 60.0)
        utc_hour = ist_decimal - 5.5
    else:
        utc_hour = SRINAGAR_SUNRISE_UTC[month]
        
    jd_check = swe.julday(year, month, day, utc_hour)
    flags = swe.FLG_SIDEREAL
    
    moon_pos, _ = swe.calc_ut(jd_check, swe.MOON, flags)
    m_lon = moon_pos[0]
    
    nakshatra_idx = int(m_lon / (360 / 27.0))
    rashi_idx = int(m_lon / 30.0)
    
    return nakshatra_idx, rashi_idx

def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as image:
            encoded_string = base64.b64encode(image.read()).decode()
        
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(248, 248, 250, 0.96), rgba(248, 248, 250, 0.96)), url(data:image/jpeg;base64,{encoded_string});
            background-size: cover; background-position: top center; background-repeat: no-repeat; background-attachment: fixed;
            color: #121212; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        }}
        h1, h2, h3, .stHeader {{ color: #1C1C1E !important; font-weight: 700 !important; border-bottom: 2px solid #E5E5EA; padding-bottom: 10px; margin-bottom: 20px; }}
        h2 {{ border-bottom: none; text-align: center; }}
        h3 {{ margin-top: 30px; border-bottom: 1px solid rgba(0, 0, 0, 0.1); padding-bottom: 15px;}}
        .stHorizontalBlock {{ background-color: #FDFDFD; border: 1px solid #E5E5EA; border-radius: 12px; padding: 25px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04); margin-bottom: 25px; }}
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important; border: 1px solid #D1D1D6 !important; border-radius: 6px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important; transition: border 0.3s ease-in-out, box-shadow 0.3s ease-in-out; color: #121212 !important;
        }}
        div[data-baseweb="input"] > div:hover, div[data-baseweb="select"] > div:hover {{ border: 1px solid #8E8E93 !important; }}
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {{ border: 2px solid #3A3A3C !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important; }}
        .stButton > button {{
            background-color: #1C1C1E !important; color: #FFFFFF !important; border: 1px solid #1C1C1E !important; border-radius: 8px !important;
            font-weight: 600 !important; font-size: 16px !important; padding: 12px 24px !important; width: 100% !important; margin-top: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; transition: all 0.2s ease-in-out;
        }}
        .stButton > button:hover {{ background-color: #3A3A3C !important; border: 1px solid #3A3A3C !important; box-shadow: 0 6px 15px rgba(0,0,0,0.15) !important; }}
        .stDownloadButton > button, .stLinkButton > a {{ background-color: #F2F2F7 !important; color: #1C1C1E !important; border-radius: 8px !important; border: 1px solid #D1D1D6 !important; font-weight: 600 !important; width: 100% !important; }}
        div[data-testid="stModal"] > div[role="dialog"] {{
            background-color: rgba(255, 255, 255, 0.7) !important; backdrop-filter: blur(20px) saturate(180%) !important; -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border: 1px solid rgba(255, 255, 255, 0.4) !important; border-radius: 16px !important; box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
        }}
        
        /* THE FIX: Absolute Floating Icons safe from Streamlit Header */
        .float-share-top-right {{
            position: fixed;
            top: 70px; /* Safely below Streamlit's hidden navbar */
            right: 20px;
            z-index: 999999; /* Forces to the absolute front */
            display: flex;
            gap: 12px;
        }}
        .top-icon-btn {{
            width: 40px; height: 40px;
            border-radius: 50%;
            display: flex; justify-content: center; align-items: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.25);
            transition: all 0.2s;
            text-decoration: none;
        }}
        .top-icon-btn:hover {{ opacity: 0.85; transform: scale(1.1); box-shadow: 0 6px 14px rgba(0,0,0,0.3); }}
        .top-icon-btn svg {{ width: 22px; height: 22px; fill: white; }}

        /* Mobile Adjustments for Top Bar */
        @media (max-width: 768px) {{
            .float-share-top-right {{
                top: 65px;
                right: 15px;
                gap: 10px;
            }}
            .top-icon-btn {{
                width: 36px; height: 36px;
            }}
            .top-icon-btn svg {{ width: 18px; height: 18px; }}
        }}

        /* Bottom Share Animation */
        .share-btn-bottom:hover {{ opacity: 0.85; transform: scale(1.02); }}
        .share-btn-bottom:active {{ transform: scale(0.98); }}

        @media (prefers-color-scheme: dark) {{
            .stApp {{ background-image: linear-gradient(rgba(14, 14, 16, 0.95), rgba(14, 14, 16, 0.95)), url(data:image/jpeg;base64,{encoded_string}); color: #F2F2F7; }}
            h1, h2, h3, .stHeader {{ color: #F8F8FA !important; border-bottom: 2px solid #3A3A3C; }}
            h3 {{ border-bottom: 1px solid #2C2C2E; padding-bottom: 15px; }}
            .stHorizontalBlock {{ background-color: #1C1C1E; border: 1px solid #2C2C2E; }}
            div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{ background-color: #2C2C2E !important; border: 1px solid #48484A !important; color: #F8F8FA !important; }}
            div[data-baseweb="input"] > div:hover, div[data-baseweb="select"] > div:hover {{ border: 1px solid #8E8E93 !important; }}
            div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {{ border: 2px solid #AEAEB2 !important; }}
            .stButton > button {{ background-color: #3A3A3C !important; border: 1px solid #48484A !important; color: #FFFFFF !important; }}
            .stButton > button:hover {{ background-color: #48484A !important; border: 1px solid #636366 !important; }}
            .stDownloadButton > button, .stLinkButton > a {{ background-color: #2C2C2E !important; color: #F2F2F7 !important; border: 1px solid #48484A !important; }}
            .calc-success {{ background-color: #1C1C1E !important; border-left: 4px solid #8E8E93 !important; color: #F8F8FA !important; border-radius: 6px; padding: 20px; margin-top: 25px; margin-bottom: 20px; }}
            .calc-success H1 {{ color: #FFFFFF !important; font-weight: 700 !important; border-bottom: none !important; margin: 10px 0 !important; text-shadow: 0px 2px 4px rgba(0,0,0,0.5) !important; }}
            div[data-testid="stModal"] > div[role="dialog"] {{ background-color: rgba(28, 28, 30, 0.65) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True
        )

@st.dialog("🙏 Welcome to the Voharvod Calculator")
def welcome_guide():
    st.markdown("""
    **What does this app do?**
    This tool accurately calculates your traditional Kashmiri lunar birthday (**Voharvod**) for any target year. It perfectly mirrors the authentic **Vijayshwar Jantri**, mathematically handling complex rules like *Adhik Maas* (Leap Months) and *Kshaya Tithis* (Skipped Sunrises).
    
    ### 🔍 Important Fields to Know:
    - **Actual Birth Date:** Your standard English date of birth. *Providing this also calculates your Nakshatra and Rashi!*
    - **Approximate Time:** In the lunar calendar, a day can change in the middle of the afternoon. If unsure, leave it on **Default** — the app will safely check a wide window (12 PM to 10 PM) to prevent errors.
    - **Known Birth Tithi:** If you already know your exact lunar phase (e.g., *Ashtami*), select it here.
    - **🔄 Direct Profile Toggle:** Don't know your English birth date? Flip this switch to directly construct your Kashmiri birth profile.
    
    *Once your date is calculated, you can instantly sync it to your Apple or Google Calendar.*
    """)
    if st.button("Get Started ✨", use_container_width=True):
        st.session_state.guide_shown = True
        st.rerun()

st.set_page_config(page_title="Voharvod Calculator Bot", page_icon="ॐ")
add_bg_from_local("mahadev.jpg")

if "guide_shown" not in st.session_state:
    st.session_state.guide_shown = False

if not st.session_state.guide_shown:
    welcome_guide()

# --- APP URL & SHARING LINKS CONFIGURATION ---
APP_URL = "https://voharvod-alert.streamlit.app"
whatsapp_msg = urllib.parse.quote(f"Check out the Kashmiri Voharvod Calculator! Save this link to easily find traditional birthdays: {APP_URL}")
fb_url = urllib.parse.quote(APP_URL)

# BRAND-COLORED ICONS (Simplified SVG paths for true icons)
wa_svg = '<svg viewBox="0 0 448 512"><path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3 18.7-68.1-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-5.5-2.8-23.2-8.5-44.2-27.1-16.4-14.6-27.4-32.6-30.6-37.9-3.2-5.5-.3-8.5 2.5-11.2 2.5-2.5 5.5-6.6 8.3-9.9 2.8-3.3 3.7-5.6 5.6-9.2 1.9-3.7.9-6.6-.5-9.2-1.4-2.8-12.5-30.1-17.1-41.1-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 13.2 5.7 23.5 9.2 31.6 11.8 13.3 4.2 25.4 3.6 35 2.2 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>'
fb_svg = '<svg viewBox="0 0 512 512"><path d="M504 256C504 119 393 8 256 8S8 119 8 256c0 123.78 90.69 226.38 209.25 245.26V312.6h-66.38V256h66.38V212.87c0-65.51 38.89-101.62 98.45-101.62 28.53 0 58.31 5.1 58.31 5.1v64h-32.81c-32.36 0-42.48 20.06-42.48 40.63V256h72.06l-11.51 56.6h-60.55v188.66C413.31 482.38 504 379.78 504 256z"/></svg>'
ig_svg = '<svg viewBox="0 0 448 512"><path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"/></svg>'

# --- TOP RIGHT FLOATING BAR (PAGE LEVEL) ---
share_html_float = f"""
<div class="float-share-top-right">
    <a href="https://wa.me/?text={whatsapp_msg}" target="_blank" class="top-icon-btn" style="background-color: #25D366;" title="Share on WhatsApp">{wa_svg}</a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={fb_url}" target="_blank" class="top-icon-btn" style="background-color: #1877F2;" title="Share on Facebook">{fb_svg}</a>
    <a href="https://instagram.com" target="_blank" class="top-icon-btn" style="background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);" title="Share on Instagram">{ig_svg}</a>
</div>
"""
st.markdown(share_html_float, unsafe_allow_html=True)

# --- CLEAN HEADER ---
st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'> Voharvod Calculator </h2>", unsafe_allow_html=True)

col_top1, col_top2 = st.columns(2)
with col_top1:
    person_name = st.text_input("Name (Optional)", placeholder="e.g. Shashank")
    st.caption("📝 *Enter a name to personalize your calendar invite.*")
with col_top2:
    target_year = st.number_input("Target Year", min_value=2024, max_value=2100, value=2026)

st.divider()

direct_mode = st.toggle("🔄 I don't know my exact birth date, but I know my Kashmiri Birth Profile")

if direct_mode:
    st.info("Select your exact traditional birth profile below:")
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        sel_month = st.selectbox("Month", MONTH_OPTIONS)
    with col_d2:
        sel_paksha = st.selectbox("Paksha", ["Zoon Pachh (Bright)", "Gatta Pachh (Dark)"])
    with col_d3:
        sel_tithi = st.selectbox("Tithi", list(TITHI_NAMES.values()))
        
    dob = None
    time_block = None
    override_tithi_name = None
    input_key = f"{person_name}-{target_year}-direct-{sel_month}-{sel_paksha}-{sel_tithi}"

else:
    col1, col2 = st.columns(2)
    with col1:
        dob = st.date_input("Actual Birth Date", value=date(2000, 12, 31), min_value=date(1940, 1, 1), max_value=date.today())
        time_block = st.selectbox("Approximate Time of Birth", ["Default (Safest bet)", "Early Morning (Before 8 AM)", "Late Morning (8 AM - 12 PM)", "Afternoon (12 PM - 4 PM)", "Evening (4 PM - 8 PM)", "Night (After 8 PM)"], index=0)
        
        if time_block != "Default (Safest bet)":
            st.warning("⚠️ Change the time only if you are reasonably sure about it. If in doubt, keeping it on 'Default' is the safest bet.")

        with st.expander("💡 Why does time matter?"):
            st.write("The Kashmiri calendar doesn't change at midnight like a normal clock. A traditional 'day' can actually change in the middle of the afternoon! If changing your time shifts your birthday by one day, it just means you were born exactly when the calendar was turning over.")

    with col2:
        known_tithi_options = ["Unknown / Calculate for me"] + list(TITHI_NAMES.values())
        override_tithi_name = st.selectbox("Known Birth Tithi (Optional)", known_tithi_options)
        st.caption("✨ *Tip: If you already know your exact Tithi name, select it here to skip the guesswork!*")

    sel_month = None
    sel_paksha = None
    sel_tithi = None
    input_key = f"{person_name}-{target_year}-calc-{dob}-{time_block}-{override_tithi_name}"

TIME_MAP = {
    "Early Morning (Before 8 AM)": time(6, 0),   
    "Late Morning (8 AM - 12 PM)": time(10, 0), 
    "Afternoon (12 PM - 4 PM)": time(14, 0),     
    "Evening (4 PM - 8 PM)": time(18, 0), 
    "Night (After 8 PM)": time(22, 0)            
}

if "last_input_key" in st.session_state and st.session_state.last_input_key != input_key:
    if "calc_results" in st.session_state:
        del st.session_state.calc_results

st.divider()

if st.button("Calculate My Kashmiri Birthday (Before relatives remind me!) ☎️"):
    st.session_state.last_input_key = input_key
    with st.spinner("Aligning birth data with Jantri..."):
        try:
            profiles_to_check = []
            mode_flag = "standard"
            
            if direct_mode:
                mode_flag = "direct"
                b_m_idx = REVERSE_MONTHS[sel_month]
                b_num = REVERSE_TITHIS[sel_tithi]
                is_krishna = "Gatta Pachh" in sel_paksha
                b_tithi = b_num + 15 if is_krishna else b_num
                profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": None, "nakshatra": None, "rashi": None, "rashi_emoji": None})
                
            else:
                if override_tithi_name != "Unknown / Calculate for me":
                    mode_flag = "override"
                    b_tithi, b_m_idx = get_precise_panchang(dob, time(12, 0)) 
                    n_idx, r_idx = get_astro_details(dob, time(12, 0))
                    for num, name in TITHI_NAMES.items():
                        if name == override_tithi_name:
                            is_krishna = b_tithi > 15
                            b_tithi = num + 15 if is_krishna else num
                            break
                    profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": None, "nakshatra": NAKSHATRA_NAMES[n_idx], "rashi": RASHI_NAMES[r_idx], "rashi_emoji": RASHI_EMOJIS[r_idx]})
                
                elif time_block == "Default (Safest bet)":
                    t1, m1 = get_precise_panchang(dob, time(12, 0)) 
                    t2, m2 = get_precise_panchang(dob, time(22, 0)) 
                    
                    if t1 != t2 or m1 != m2:
                        mode_flag = "default_split"
                        low = 12 * 60
                        high = 22 * 60
                        transition_min = high
                        while low <= high:
                            mid = (low + high) // 2
                            test_t = time(mid // 60, mid % 60)
                            t_test, m_test = get_precise_panchang(dob, test_t)
                            if t_test != t1 or m_test != m1:
                                transition_min = mid
                                high = mid - 1
                            else:
                                low = mid + 1
                                
                        transition_time_str = time(transition_min // 60, transition_min % 60).strftime("%I:%M %p").lstrip("0")
                        
                        n1, r1 = get_astro_details(dob, time(12, 0))
                        n2, r2 = get_astro_details(dob, time(22, 0))
                        
                        profiles_to_check.append({"tithi": t1, "m_idx": m1, "desc": f"⚠️ Time Transition: If born before {transition_time_str}", "nakshatra": NAKSHATRA_NAMES[n1], "rashi": RASHI_NAMES[r1], "rashi_emoji": RASHI_EMOJIS[r1]})
                        profiles_to_check.append({"tithi": t2, "m_idx": m2, "desc": f"⚠️ Time Transition: If born after {transition_time_str}", "nakshatra": NAKSHATRA_NAMES[n2], "rashi": RASHI_NAMES[r2], "rashi_emoji": RASHI_EMOJIS[r2]})
                    else:
                        mode_flag = "default_single"
                        n1, r1 = get_astro_details(dob, time(16, 0))
                        profiles_to_check.append({"tithi": t1, "m_idx": m1, "desc": None, "nakshatra": NAKSHATRA_NAMES[n1], "rashi": RASHI_NAMES[r1], "rashi_emoji": RASHI_EMOJIS[r1]})
                
                else:
                    anchor_time = TIME_MAP[time_block]
                    b_tithi, b_m_idx = get_precise_panchang(dob, exact_time=anchor_time)
                    n1, r1 = get_astro_details(dob, exact_time=anchor_time)
                    profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": None, "nakshatra": NAKSHATRA_NAMES[n1], "rashi": RASHI_NAMES[r1], "rashi_emoji": RASHI_EMOJIS[r1]})

            results_list = []
            
            for prof in profiles_to_check:
                b_tithi = prof["tithi"]
                b_m_idx = prof["m_idx"]
                
                b_paksha = "Gatta Pachh" if b_tithi > 15 else "Zoon Pachh"
                b_num = b_tithi - 15 if b_tithi > 15 else b_tithi
                tithi_string = f"{KASHMIRI_MONTHS.get(b_m_idx, 'Unknown')} {b_paksha} {TITHI_NAMES.get(b_num, str(b_num))}"
                
                raw_matches = []
                start_search = date(target_year, 1, 1)
                
                prev_tithi = None
                prev_date = None
                prev_m_idx = None
                
                for d in range(0, 400):
                    curr = start_search + timedelta(days=d)
                    c_tithi, c_m_idx = get_precise_panchang(curr, exact_time=None)
                    
                    is_match = False
                    match_date = curr
                    
                    if c_tithi == b_tithi:
                        is_match = True
                    elif prev_tithi is not None:
                        def continuous(t): return t if t >= prev_tithi else t + 30
                        cont_c = continuous(c_tithi)
                        cont_b = continuous(b_tithi)
                        if prev_tithi < cont_b < cont_c and (cont_c - prev_tithi) <= 2:
                            is_match = True
                            match_date = prev_date
                            
                    if is_match:
                        if c_m_idx == b_m_idx or (prev_m_idx is not None and prev_m_idx == b_m_idx):
                            if match_date not in raw_matches:
                                raw_matches.append(match_date)
                                
                    prev_tithi = c_tithi
                    prev_date = curr
                    prev_m_idx = c_m_idx
                
                events = []
                for m in raw_matches:
                    if not events: events.append(m)
                    elif (m - events[-1]).days > 2: events.append(m)
                    else: events[-1] = m 
                        
                valid_events = [e for e in events if e.year == target_year or (e.year == target_year + 1 and e.month < 4)]
                
                found_date = None
                if valid_events:
                    found_date = valid_events[-1] 
                
                results_list.append({
                    "success": found_date is not None,
                    "tithi_string": tithi_string,
                    "found_date": found_date,
                    "is_leap_month": len(valid_events) > 1,
                    "desc": prof["desc"],
                    "nakshatra": prof.get("nakshatra"),
                    "rashi": prof.get("rashi"),
                    "rashi_emoji": prof.get("rashi_emoji")
                })

            st.session_state.calc_results = {
                "mode": mode_flag,
                "results": results_list,
                "show_balloons": True
            }
                
        except Exception as e:
            st.error(f"Error: {e}")

if "calc_results" in st.session_state:
    res_data = st.session_state.calc_results
    mode = res_data["mode"]
    
    if mode == "default_split":
        st.error("⚠️ **Lunar Phase Transition Detected!** A traditional lunar day changed between 12:00 PM and 10:00 PM on your actual birth date. We have pinpointed the exact transition time. Please select the profile below that matches your birth time or family records.")
    elif mode == "default_single":
        st.markdown("<p style='color: #8E8E93; font-size: 14px; margin-top: 10px; margin-bottom: 25px;'>ℹ️ **Note:** This birthday profile is calculated using a default birth time window of **12:00 PM to 10:00 PM**. If this doesn't match your known traditional profile, use the *Known Birth Tithi* or the *Direct Profile* toggle.</p>", unsafe_allow_html=True)
    
    if res_data["show_balloons"]:
        st.balloons()
        st.session_state.calc_results["show_balloons"] = False

    for idx, r in enumerate(res_data["results"]):
        if r["success"]:
            header_name = f"{person_name.strip().split()[0]}'s Voharvod" if person_name.strip() else "Kashmiri Voharvod"
            
            astro_html = ""
            if r.get('nakshatra') and r.get('rashi'):
                emoji = r.get('rashi_emoji', '🌙')
                astro_html = f"<p style='color: #8E8E93; font-size: 0.95rem; margin-top: 10px; margin-bottom: 15px;'>{emoji} <strong>Rashi:</strong> {r['rashi']} &nbsp;|&nbsp; ✨ <strong>Nakshatra:</strong> {r['nakshatra']}</p>"
            
            desc_html = f"<p style='color: #8E8E93; font-weight: 600; font-size: 0.95rem; margin-top: 5px;'>{r['desc']}</p>" if r.get('desc') else ""

            html_block = f"""<div class='result-block' style='margin-top:30px; border-bottom: 1px solid rgba(150, 150, 150, 0.2); padding-bottom: 30px;'>
<h3 style='margin-bottom: 0px;'>📋 Profile: {header_name}</h3>
{desc_html}
{astro_html}
<p>Matches <strong>{r['tithi_string']}</strong> for this year.</p>
<div class='calc-success'>
✅<span style='font-weight:600; font-size:1.1rem; margin-left:10px;'> {target_year} Kashmiri Birthday</span>
<h1>{r['found_date'].strftime('%A, %d %B %Y')}</h1>
</div>
</div>"""
            st.markdown(html_block, unsafe_allow_html=True)
            
            if r.get("is_leap_month"):
                st.caption(f"🌟 **Leap Month Detected!** Automatically bridged the calendar gap to provide the pure 'Banamas' date for {r['tithi_string']}.")
            
            btn_col1, btn_col2 = st.columns(2)
            
            start_str = r['found_date'].strftime("%Y%m%d")
            gcal_end_str = (r['found_date'] + timedelta(days=1)).strftime("%Y%m%d")
            date_suffix = r['found_date'].strftime("%d%b")
            
            event_title = f"{person_name.strip().split()[0]}'s Kashmiri Birthday {date_suffix}" if person_name.strip() else f"Kashmiri Birthday {date_suffix}"
            
            event_details = f"Traditional Profile: {r['tithi_string']}"
            if r.get('nakshatra'):
                event_details += f" | Rashi: {r['rashi']} | Nakshatra: {r['nakshatra']}"
            
            gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(event_title)}&dates={start_str}/{gcal_end_str}&details={urllib.parse.quote(event_details)}"
            ics_content = f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Kashmiri Voharvod Calculator Pro//EN\nBEGIN:VEVENT\nDTSTART;VALUE=DATE:{start_str}\nDURATION:P1D\nSUMMARY:{event_title}\nDESCRIPTION:{event_details}\nEND:VEVENT\nEND:VCALENDAR"
            
            with btn_col1:
                st.link_button("📅 Add to Google Calendar", gcal_url, use_container_width=True, key=f"gcal_{idx}")
            with btn_col2:
                st.download_button("🍎 Add to Apple / Outlook Calendar", data=ics_content.replace('\n', '\r\n'), file_name=f"voharvod_{idx}.ics", mime="text/calendar", use_container_width=True, key=f"ics_{idx}")
            
        else:
            st.error(f"Astronomical match not found. Please verify the target year.")

# --- BOTTOM SHARE SECTION ---
st.divider()
st.markdown("<h3 style='text-align: center; border-bottom: none; margin-top: 0px;'>Share this App</h3>", unsafe_allow_html=True)

wa_svg_small = '<svg viewBox="0 0 448 512" style="width: 18px; height: 18px; fill: white; margin-right: 8px; vertical-align: middle;"><path d="M380.9 97.1C339 55.1 283.2 32 223.9 32c-122.4 0-222 99.6-222 222 0 39.1 10.2 77.3 29.6 111L0 480l117.7-30.9c32.4 17.7 68.9 27 106.1 27h.1c122.3 0 224.1-99.6 224.1-222 0-59.3-25.2-115-67.1-157zm-157 341.6c-33.2 0-65.7-8.9-94-25.7l-6.7-4-69.8 18.3 18.7-68.1-4.4-7c-18.5-29.4-28.2-63.3-28.2-98.2 0-101.7 82.8-184.5 184.6-184.5 49.3 0 95.6 19.2 130.4 54.1 34.8 34.9 56.2 81.2 56.1 130.5 0 101.8-84.9 184.6-186.6 184.6zm101.2-138.2c-5.5-2.8-32.8-16.2-37.9-18-5.1-1.9-8.8-2.8-12.5 2.8-3.7 5.6-14.3 18-17.6 21.8-3.2 3.7-6.5 4.2-12 1.4-5.5-2.8-23.2-8.5-44.2-27.1-16.4-14.6-27.4-32.6-30.6-37.9-3.2-5.5-.3-8.5 2.5-11.2 2.5-2.5 5.5-6.6 8.3-9.9 2.8-3.3 3.7-5.6 5.6-9.2 1.9-3.7.9-6.6-.5-9.2-1.4-2.8-12.5-30.1-17.1-41.1-4.5-10.8-9.1-9.3-12.5-9.5-3.2-.2-6.9-.2-10.6-.2-3.7 0-9.7 1.4-14.8 6.9-5.1 5.6-19.4 19-19.4 46.3 0 27.3 19.9 53.7 22.6 57.4 2.8 3.7 39.1 59.7 94.8 83.8 13.2 5.7 23.5 9.2 31.6 11.8 13.3 4.2 25.4 3.6 35 2.2 10.7-1.6 32.8-13.4 37.4-26.4 4.6-13 4.6-24.1 3.2-26.4-1.3-2.5-5-3.9-10.5-6.6z"/></svg>'
fb_svg_small = '<svg viewBox="0 0 512 512" style="width: 18px; height: 18px; fill: white; margin-right: 8px; vertical-align: middle;"><path d="M504 256C504 119 393 8 256 8S8 119 8 256c0 123.78 90.69 226.38 209.25 245.26V312.6h-66.38V256h66.38V212.87c0-65.51 38.89-101.62 98.45-101.62 28.53 0 58.31 5.1 58.31 5.1v64h-32.81c-32.36 0-42.48 20.06-42.48 40.63V256h72.06l-11.51 56.6h-60.55v188.66C413.31 482.38 504 379.78 504 256z"/></svg>'
ig_svg_small = '<svg viewBox="0 0 448 512" style="width: 18px; height: 18px; fill: white; margin-right: 8px; vertical-align: middle;"><path d="M224.1 141c-63.6 0-114.9 51.3-114.9 114.9s51.3 114.9 114.9 114.9S339 319.5 339 255.9 287.7 141 224.1 141zm0 189.6c-41.1 0-74.7-33.5-74.7-74.7s33.5-74.7 74.7-74.7 74.7 33.5 74.7 74.7-33.6 74.7-74.7 74.7zm146.4-194.3c0 14.9-12 26.8-26.8 26.8-14.9 0-26.8-12-26.8-26.8s12-26.8 26.8-26.8 26.8 12 26.8 26.8zm76.1 27.2c-1.7-35.9-9.9-67.7-36.2-93.9-26.2-26.2-58-34.4-93.9-36.2-37-2.1-147.9-2.1-184.9 0-35.8 1.7-67.6 9.9-93.9 36.1s-34.4 58-36.2 93.9c-2.1 37-2.1 147.9 0 184.9 1.7 35.9 9.9 67.7 36.2 93.9s58 34.4 93.9 36.2c37 2.1 147.9 2.1 184.9 0 35.9-1.7 67.7-9.9 93.9-36.2 26.2-26.2 34.4-58 36.2-93.9 2.1-37 2.1-147.8 0-184.8zM398.8 388c-7.8 19.6-22.9 34.7-42.6 42.6-29.5 11.7-99.5 9-132.1 9s-102.7 2.6-132.1-9c-19.6-7.8-34.7-22.9-42.6-42.6-11.7-29.5-9-99.5-9-132.1s-2.6-102.7 9-132.1c7.8-19.6 22.9-34.7 42.6-42.6 29.5-11.7 99.5-9 132.1-9s102.7-2.6 132.1 9c19.6 7.8 34.7 22.9 42.6 42.6 11.7 29.5 9 99.5 9 132.1s2.7 102.7-9 132.1z"/></svg>'

share_html_bottom = f"""
<div style="display: flex; gap: 12px; justify-content: center; margin-top: 10px; margin-bottom: 15px; flex-wrap: wrap;">
    <a href="https://wa.me/?text={whatsapp_msg}" target="_blank" class="share-btn-bottom" style="text-decoration: none; background-color: #25D366; color: white; padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: all 0.2s; white-space: nowrap;">{wa_svg_small}WhatsApp</a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={fb_url}" target="_blank" class="share-btn-bottom" style="text-decoration: none; background-color: #1877F2; color: white; padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: all 0.2s; white-space: nowrap;">{fb_svg_small}Facebook</a>
    <a href="https://instagram.com" target="_blank" class="share-btn-bottom" style="text-decoration: none; background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); color: white; padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); transition: all 0.2s; white-space: nowrap;">{ig_svg_small}Instagram</a>
</div>
"""
st.markdown(share_html_bottom, unsafe_allow_html=True)

st.markdown("<p style='text-align: center; color: #8E8E93; font-size: 12px; margin-top:-5px; margin-bottom: 10px;'><i>To share on Instagram, copy the link below and paste it into your Story or DM!</i></p>", unsafe_allow_html=True)
st.code(APP_URL, language=None)

st.markdown("<p style='text-align: center; color: #888888; font-size: 13px; margin-top: 30px;'>🔒 <b>Privacy First:</b> This calculator runs safely in your browser. We do not save, store, or track any names, birth dates, or personal information.</p>", unsafe_allow_html=True)