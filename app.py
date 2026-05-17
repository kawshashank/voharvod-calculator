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

# Reverse lookup dictionaries for direct profile entry
REVERSE_MONTHS = {v: k for k, v in KASHMIRI_MONTHS.items()}
REVERSE_TITHIS = {v: k for k, v in TITHI_NAMES.items()}
MONTH_OPTIONS = ["Chetra", "Vaisakh", "Zeth", "Haar", "Shravun", "Bhadrapeth", "Ashid", "Kartik", "Monjhor", "Poh", "Magh", "Phagun"]

SRINAGAR_SUNRISE_UTC = {
    1: 1.75, 2: 1.50, 3: 1.00, 4: 0.50, 5: 0.00, 6: -0.15,
    7: 0.00, 8: 0.25, 9: 0.75, 10: 1.00, 11: 1.50, 12: 1.80
}

# --- THE ACCURATE ASTRONOMICAL ENGINE ---
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

# --- APP BACKGROUND & TITANIUM PRO UI SETUP ---
def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as image:
            encoded_string = base64.b64encode(image.read()).decode()
        
        st.markdown(
        f"""
        <style>
        /* Main Background Setup */
        .stApp {{
            background-image: linear-gradient(rgba(248, 248, 250, 0.96), rgba(248, 248, 250, 0.96)), url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-position: top center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            color: #121212;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        }}
        
        /* Monochromatic Headings */
        h1, h2, h3, .stHeader {{
            color: #1C1C1E !important; 
            font-weight: 700 !important;
            border-bottom: 2px solid #E5E5EA;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{ border-bottom: none; text-align: center; }}
        h3 {{ margin-top: 30px; border-bottom: 1px solid rgba(0, 0, 0, 0.1); padding-bottom: 15px;}}
        
        /* Structural Cards */
        .stHorizontalBlock {{
            background-color: #FDFDFD;
            border: 1px solid #E5E5EA;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
            margin-bottom: 25px;
        }}
        
        /* INPUT BOXES: Clean, crisp borders */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border: 1px solid #D1D1D6 !important;
            border-radius: 6px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02) !important;
            transition: border 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
            color: #121212 !important;
        }}
        
        div[data-baseweb="input"] > div:hover, 
        div[data-baseweb="select"] > div:hover {{
            border: 1px solid #8E8E93 !important; 
        }}
        div[data-baseweb="input"] > div:focus-within, 
        div[data-baseweb="select"] > div:focus-within {{
            border: 2px solid #3A3A3C !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        }}
        
        /* PRIMARY BUTTON */
        .stButton > button {{
            background-color: #1C1C1E !important;
            color: #FFFFFF !important;
            border: 1px solid #1C1C1E !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            padding: 12px 24px !important;
            width: 100% !important;
            margin-top: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
            transition: all 0.2s ease-in-out;
        }}
        .stButton > button:hover {{
            background-color: #3A3A3C !important;
            border: 1px solid #3A3A3C !important;
            box-shadow: 0 6px 15px rgba(0,0,0,0.15) !important;
        }}

        /* Secondary Buttons */
        .stDownloadButton > button, .stLinkButton > a {{
            background-color: #F2F2F7 !important;
            color: #1C1C1E !important;
            border-radius: 8px !important;
            border: 1px solid #D1D1D6 !important;
            font-weight: 600 !important;
            width: 100% !important;
        }}

        /* TRANSPARENT MODAL / GUIDE WINDOW SETTINGS */
        div[data-testid="stModal"] > div[role="dialog"] {{
            background-color: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
        }}

        /* Dark Mode */
        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background-image: linear-gradient(rgba(14, 14, 16, 0.95), rgba(14, 14, 16, 0.95)), url(data:image/jpeg;base64,{encoded_string});
                color: #F2F2F7;
            }}
            h1, h2, h3, .stHeader {{ color: #F8F8FA !important; border-bottom: 2px solid #3A3A3C; }}
            h3 {{ border-bottom: 1px solid #2C2C2E; padding-bottom: 15px; }}
            
            .stHorizontalBlock {{ background-color: #1C1C1E; border: 1px solid #2C2C2E; }}
            
            div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{
                background-color: #2C2C2E !important; border: 1px solid #48484A !important; color: #F8F8FA !important;
            }}
            div[data-baseweb="input"] > div:hover, div[data-baseweb="select"] > div:hover {{ border: 1px solid #8E8E93 !important; }}
            div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {{ border: 2px solid #AEAEB2 !important; }}

            .stButton > button {{ background-color: #3A3A3C !important; border: 1px solid #48484A !important; color: #FFFFFF !important; }}
            .stButton > button:hover {{ background-color: #48484A !important; border: 1px solid #636366 !important; }}

            .stDownloadButton > button, .stLinkButton > a {{ background-color: #2C2C2E !important; color: #F2F2F7 !important; border: 1px solid #48484A !important; }}
            
            .calc-success {{
                background-color: #1C1C1E !important; 
                border-left: 4px solid #8E8E93 !important; 
                color: #F8F8FA !important;
                border-radius: 6px; padding: 20px; margin-top: 25px; margin-bottom: 20px;
            }}
            .calc-success H1 {{
                color: #FFFFFF !important; font-weight: 700 !important; border-bottom: none !important; margin: 10px 0 !important;
                text-shadow: 0px 2px 4px rgba(0,0,0,0.5) !important; 
            }}
            
            /* Dark Mode Transparent Guide Overlay */
            div[data-testid="stModal"] > div[role="dialog"] {{
                background-color: rgba(28, 28, 30, 0.65) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
        )

# --- WELCOME GUIDE DIALOG ---
@st.dialog("🙏 Welcome to the Voharvod Calculator")
def welcome_guide():
    st.markdown("""
    **What does this app do?**
    This tool accurately calculates your traditional Kashmiri lunar birthday (**Voharvod**) for any target year. It perfectly mirrors the authentic **Vijayshwar Jantri**, mathematically handling complex rules like *Adhik Maas* (Leap Months) and *Kshaya Tithis* (Skipped Sunrises).
    
    ### 🔍 Important Fields to Know:
    - **Actual Birth Date:** Your standard English date of birth. *Providing this also calculates your Nakshatra and Rashi!*
    - **Approximate Time:** In the lunar calendar, a day can change in the middle of the afternoon. If unsure, leave it on **Default** — the app will safely check a wide window (12 PM to 10 PM) to prevent errors.
    - **Known Birth Tithi:** If you already know your exact lunar phase (e.g., *Ashtami*), select it here.
    - **🔄 Direct Profile Toggle:** Don't know your English birth date? Flip this switch to directly construct your Kashmiri birth profile (e.g., *Chetra Gatta Pachh Dahom*).
    
    *Once your date is calculated, you can instantly sync it to your Apple or Google Calendar.*
    """)
    if st.button("Get Started ✨", use_container_width=True):
        st.session_state.guide_shown = True
        st.rerun()

# --- APP UI ---
st.set_page_config(page_title="Voharvod Calculator Bot", page_icon="ॐ")
add_bg_from_local("mahadev.jpg")

if "guide_shown" not in st.session_state:
    st.session_state.guide_shown = False

if not st.session_state.guide_shown:
    welcome_guide()

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

# --- EXECUTE CALCULATION ON CLICK ---
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

# --- RENDER RESULTS ---
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
            # Formatting the main heading dynamically
            header_name = f"{person_name.strip().split()[0]}'s Voharvod" if person_name.strip() else "Kashmiri Voharvod"
            
            astro_html = ""
            if r.get('nakshatra') and r.get('rashi'):
                emoji = r.get('rashi_emoji', '🌙')
                astro_html = f"<p style='color: #8E8E93; font-size: 0.95rem; margin-top: 10px; margin-bottom: 15px;'>{emoji} <strong>Rashi:</strong> {r['rashi']} &nbsp;|&nbsp; ✨ <strong>Nakshatra:</strong> {r['nakshatra']}</p>"
            
            # Additional formatting if there is a split descriptor
            desc_html = f"<p style='color: #D4AF37; font-weight: 600; font-size: 0.95rem; margin-top: 5px;'>{r['desc']}</p>" if r.get('desc') else ""

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
            # Clean fallback for missing dates
            st.error(f"Astronomical match not found. Please verify the target year.")

st.markdown("<p style='text-align: center; color: #888888; font-size: 13px;'>🔒 <b>Privacy First:</b> This calculator runs safely in your browser. We do not save, store, or track any names, birth dates, or personal information.</p>", unsafe_allow_html=True)