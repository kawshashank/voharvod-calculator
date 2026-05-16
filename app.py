import streamlit as st
import swisseph as swe
import base64
import os
import urllib.parse
from datetime import date, time, timedelta

# --- CONFIGURE SWISS EPHEMERIS ---
swe.set_sid_mode(swe.SIDM_LAHIRI)

# --- KASHMIRI TRADITIONAL DATA ---
MONTHS = [
    "Navreh", "Vaisakh", "Zeth", "Haar", "Shravun", "Bhadrapeth",
    "Ashid", "Kartik", "Monjhor", "Poh", "Magh", "Phagun"
]

TITHI_NAMES = {
    1: "Pratipada", 2: "Duya", 3: "Truya", 4: "Chorum", 5: "Ponchum",
    6: "Sheyam", 7: "Satam", 8: "Ashtam", 9: "Navam", 10: "Dahom",
    11: "Kahyom", 12: "Duvahsh", 13: "Truvahsh", 14: "Chodah", 15: "Purnima/Amavasya"
}

# Seasonal Sunrise in UTC for Srinagar (IST - 5.5 hours)
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
    month_idx = int(s_lon / 30)
    
    jd_sunrise = swe.julday(year, month, day, SRINAGAR_SUNRISE_UTC[month])
    
    for h in range(1, 32 * 24):
        jd_search = jd_sunrise + (h / 24.0)
        s_pos_f, _ = swe.calc_ut(jd_search, swe.SUN, flags)
        m_pos_f, _ = swe.calc_ut(jd_search, swe.MOON, flags)
        
        f_diff = (m_pos_f[0] - s_pos_f[0]) % 360
        
        if f_diff < last_diff and last_diff > 350:
            month_idx = int(s_pos_f[0] / 30)
            break
        last_diff = f_diff
        
    if tithi > 15:
        month_idx = (month_idx + 1) % 12
        
    return tithi, month_idx

# --- APP BACKGROUND SETUP ---
def add_bg_from_local(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as image:
            encoded_string = base64.b64encode(image.read()).decode()
        
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)), url(data:image/jpeg;base64,{encoded_string});
            background-size: cover;
            background-position: top center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background-image: linear-gradient(rgba(14, 17, 23, 0.95), rgba(14, 17, 23, 0.95)), url(data:image/jpeg;base64,{encoded_string});
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
        )

# --- APP UI ---
st.set_page_config(page_title="Voharvod Calculator Bot", page_icon="ॐ")

add_bg_from_local("mahadev.jpg")

st.markdown(
    "<h2 style='text-align: center; margin-bottom: 20px;'>ॐ Voharvod Calculator ॐ</h2>", 
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    person_name = st.text_input(
        "Name (Optional)", 
        placeholder="e.g. Shashank"
    )
    st.caption("📝 *Enter a name to personalize your calendar invite (e.g., 'Shashank's Kashmiri Birthday').*")
    
    dob = st.date_input(
        "Actual Birth Date", 
        value=date(1990, 7, 14),
        min_value=date(1940, 1, 1),
        max_value=date.today()
    )
    
    time_block = st.selectbox(
        "Approximate Time of Birth",
        [
            "Default (Safest bet)",
            "Early Morning (Before 8 AM)",
            "Late Morning (8 AM - 12 PM)",
            "Afternoon (12 PM - 4 PM)",
            "Evening (4 PM - 8 PM)",
            "Night (After 8 PM)"
        ],
        index=0 
    )
    
    if time_block != "Default (Safest bet)":
        st.warning("⚠️ Change the time only if you are reasonably sure about it. If in doubt, keeping it on 'Default' is the safest bet.")

    with st.expander("💡 Why does time matter?"):
        st.write("The Kashmiri calendar doesn't change at midnight like a normal clock. A traditional 'day' can actually change in the middle of the afternoon! If changing your time shifts your birthday by one day, it just means you were born exactly when the calendar was turning over.")

with col2:
    target_year = st.number_input("Target Year", min_value=2024, max_value=2100, value=2026)
    
    known_tithi_options = ["Unknown / Calculate for me"] + list(TITHI_NAMES.values())
    override_tithi_name = st.selectbox("Known Birth Tithi (Optional)", known_tithi_options)
    
    st.caption("✨ *Tip: If you don't know your birth time, but you already know your exact Tithi name, select it here to skip the guesswork!*")

TIME_MAP = {
    "Default (Safest bet)": time(18, 0), 
    "Early Morning (Before 8 AM)": time(6, 0),   
    "Late Morning (8 AM - 12 PM)": time(10, 0),  
    "Afternoon (12 PM - 4 PM)": time(14, 0),     
    "Evening (4 PM - 8 PM)": time(18, 0),        
    "Night (After 8 PM)": time(22, 0)            
}

# Check if inputs changed—if they did, clear previous calculation state
input_key = f"{person_name}-{dob}-{time_block}-{target_year}-{override_tithi_name}"
if "last_input_key" in st.session_state and st.session_state.last_input_key != input_key:
    if "calc_results" in st.session_state:
        del st.session_state.calc_results

# --- EXECUTE CALCULATION ON CLICK ---
if st.button("Calculate My Kashmiri Birthday (Before relatives remind me!) ☎️"):
    st.session_state.last_input_key = input_key
    with st.spinner("Aligning birth data with Jantri..."):
        try:
            anchor_time = TIME_MAP[time_block]
            b_tithi, b_m_idx = get_precise_panchang(dob, exact_time=anchor_time)
            
            if override_tithi_name != "Unknown / Calculate for me":
                for num, name in TITHI_NAMES.items():
                    if name == override_tithi_name:
                        is_krishna = b_tithi > 15
                        b_tithi = num + 15 if is_krishna else num
                        break

            b_paksha = "Gatta Pachh" if b_tithi > 15 else "Zoon Pachh"
            b_num = b_tithi - 15 if b_tithi > 15 else b_tithi
            
            tithi_string = f"{MONTHS[b_m_idx]} {b_paksha} {TITHI_NAMES.get(b_num, str(b_num))}"
            
            found_date = None
            start_search = date(target_year, 1, 1)
            
            for d in range(0, 400):
                curr = start_search + timedelta(days=d)
                c_tithi, c_m_idx = get_precise_panchang(curr, exact_time=None)
                
                if c_tithi == b_tithi and c_m_idx == b_m_idx:
                    if curr > date(target_year, 3, 18):
                        found_date = curr
                        break
            
            st.session_state.calc_results = {
                "success": found_date is not None,
                "tithi_string": tithi_string,
                "found_date": found_date,
                "show_balloons": True
            }
                
        except Exception as e:
            st.error(f"Error: {e}")

# --- RENDER RESULTS ---
if "calc_results" in st.session_state:
    res = st.session_state.calc_results
    
    if res["success"]:
        tithi_string = res["tithi_string"]
        found_date = res["found_date"]
        
        st.markdown("### 📋 Birth Profile")
        st.info(f"**Target Tithi:** {tithi_string}")
        
        st.divider()
        st.success(f"### ✅ {target_year} Verdict")
        
        if res["show_balloons"]:
            st.balloons()
            st.session_state.calc_results["show_balloons"] = False
            
        st.header(found_date.strftime('%A, %d %B %Y'))
        st.caption(f"Matches {tithi_string} at Sunrise.")
        
        # Format dates cleanly
        start_str = found_date.strftime("%Y%m%d")
        gcal_end_str = (found_date + timedelta(days=1)).strftime("%Y%m%d")
        
        # Extract verdict short date string (e.g., "31Dec")
        date_suffix = found_date.strftime("%d%b")
        
        # NEW: Append short date string to the event title dynamically
        if person_name.strip():
            first_name = person_name.strip().split()[0]
            event_title = f"{first_name}'s Kashmiri Birthday {date_suffix}"
        else:
            event_title = f"Kashmiri Birthday {date_suffix}"
            
        event_details = f"Calculated Tithi: {tithi_string}"
        
        # 1. Google Link
        gcal_url = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={urllib.parse.quote(event_title)}"
            f"&dates={start_str}/{gcal_end_str}"
            f"&details={urllib.parse.quote(event_details)}"
        )
        
        # 2. Apple / Universal Content
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Kashmiri Voharvod Calculator//EN
BEGIN:VEVENT
DTSTART;VALUE=DATE:{start_str}
DURATION:P1D
SUMMARY:{event_title}
DESCRIPTION:{event_details}
END:VEVENT
END:VCALENDAR"""
        
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            st.link_button("📅 Add to Google Calendar", gcal_url, use_container_width=True)
            
        with btn_col2:
            st.download_button(
                label="🍎 Add to Apple / Other Calendar",
                data=ics_content.replace('\n', '\r\n'), 
                file_name="voharvod.ics",
                mime="text/calendar",
                use_container_width=True
            )
    else:
        st.error("Astronomical match not found. Please verify the year.")

# --- PRIVACY DISCLAIMER ---
st.divider()
st.markdown(
    "<p style='text-align: center; color: #888888; font-size: 13px;'>"
    "🔒 <b>Privacy First:</b> This calculator runs safely in your browser. "
    "We do not save, store, or track any names, birth dates, or personal information.</p>", 
    unsafe_allow_html=True
)