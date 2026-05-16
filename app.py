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

st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>ॐ Voharvod Calculator ॐ</h2>", unsafe_allow_html=True)

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
        # Changed default date to December 31, 2000
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
            
            # --- BRANCH 1: DIRECT PROFILE MODE ---
            if direct_mode:
                mode_flag = "direct"
                b_m_idx = REVERSE_MONTHS[sel_month]
                b_num = REVERSE_TITHIS[sel_tithi]
                is_krishna = "Gatta Pachh" in sel_paksha
                
                b_tithi = b_num + 15 if is_krishna else b_num
                profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": "Direct Selection"})
                
            # --- BRANCH 2: CALCULATION MODE ---
            else:
                if override_tithi_name != "Unknown / Calculate for me":
                    mode_flag = "override"
                    b_tithi, b_m_idx = get_precise_panchang(dob, time(12, 0)) # Base month off 12pm
                    for num, name in TITHI_NAMES.items():
                        if name == override_tithi_name:
                            is_krishna = b_tithi > 15
                            b_tithi = num + 15 if is_krishna else num
                            break
                    profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": "Override Selection"})
                
                # --- THE NEW WINDOW LOGIC FOR DEFAULT (12 PM to 10 PM) ---
                elif time_block == "Default (Safest bet)":
                    t1, m1 = get_precise_panchang(dob, time(12, 0)) # 12 PM Check
                    t2, m2 = get_precise_panchang(dob, time(22, 0)) # 10 PM Check
                    
                    if t1 != t2 or m1 != m2:
                        mode_flag = "default_split"
                        profiles_to_check.append({"tithi": t1, "m_idx": m1, "desc": "Possibility 1 (Active around 12:00 PM)"})
                        profiles_to_check.append({"tithi": t2, "m_idx": m2, "desc": "Possibility 2 (Active around 10:00 PM)"})
                    else:
                        mode_flag = "default_single"
                        profiles_to_check.append({"tithi": t1, "m_idx": m1, "desc": "Default Window"})
                
                # --- SPECIFIC TIME SELECTED ---
                else:
                    anchor_time = TIME_MAP[time_block]
                    b_tithi, b_m_idx = get_precise_panchang(dob, exact_time=anchor_time)
                    profiles_to_check.append({"tithi": b_tithi, "m_idx": b_m_idx, "desc": f"Time: {time_block}"})

            results_list = []
            
            # --- COMMON: SCAN TARGET YEAR FOR ALL IDENTIFIED PROFILES ---
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
                    "desc": prof["desc"]
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
    
    # --- RENDER MESSAGING BASED ON MODE ---
    if mode == "default_split":
        st.error("⚠️ **Sunset / Tithi Transition Detected!** A lunar phase changed between the 12:00 PM and 10:00 PM window on your actual birth date. To maintain transparency and ensure you have the right date, we have generated verdicts for both profiles below. Select the one that matches your known family profile.")
    elif mode == "default_single":
        st.info("ℹ️ **Note:** This profile is calculated using a default birth time window of **12:00 PM to 10:00 PM**. If this doesn't match your exact known birthprofile, use the *Known Birth Tithi* dropdown above or the *Direct Profile* toggle.")
    
    if res_data["show_balloons"]:
        st.balloons()
        st.session_state.calc_results["show_balloons"] = False

    # --- RENDER EACH GENERATED PROFILE ---
    for idx, r in enumerate(res_data["results"]):
        if r["success"]:
            tithi_string = r["tithi_string"]
            found_date = r["found_date"]
            
            st.markdown(f"### 📋 Birth Profile: {r['desc']}")
            st.info(f"**Target Tithi:** {tithi_string}")
            
            st.success(f"### ✅ {target_year} Verdict")
            st.header(found_date.strftime('%A, %d %B %Y'))
            
            if r.get("is_leap_month"):
                st.caption(f"🌟 **Leap Month Detected!** Automatically selected the pure 'Banamas' date for {tithi_string}.")
            else:
                st.caption(f"Matches {tithi_string} for this year.")
            
            start_str = found_date.strftime("%Y%m%d")
            gcal_end_str = (found_date + timedelta(days=1)).strftime("%Y%m%d")
            date_suffix = found_date.strftime("%d%b")
            
            if person_name.strip():
                first_name = person_name.strip().split()[0]
                event_title = f"{first_name}'s Kashmiri Birthday {date_suffix}"
            else:
                event_title = f"Kashmiri Birthday {date_suffix}"
                
            event_details = f"Calculated Tithi: {tithi_string}"
            
            gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={urllib.parse.quote(event_title)}&dates={start_str}/{gcal_end_str}&details={urllib.parse.quote(event_details)}"
            ics_content = f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Kashmiri Voharvod Calculator//EN\nBEGIN:VEVENT\nDTSTART;VALUE=DATE:{start_str}\nDURATION:P1D\nSUMMARY:{event_title}\nDESCRIPTION:{event_details}\nEND:VEVENT\nEND:VCALENDAR"
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.link_button("📅 Add to Google Calendar", gcal_url, use_container_width=True, key=f"gcal_{idx}")
            with btn_col2:
                st.download_button("🍎 Add to Apple / Other Calendar", data=ics_content.replace('\n', '\r\n'), file_name=f"voharvod_{idx}.ics", mime="text/calendar", use_container_width=True, key=f"ics_{idx}")
            
            st.divider()
        else:
            st.error(f"Astronomical match not found for {r['desc']}. Please verify the year.")

st.markdown("<p style='text-align: center; color: #888888; font-size: 13px;'>🔒 <b>Privacy First:</b> This calculator runs safely in your browser. We do not save, store, or track any names, birth dates, or personal information.</p>", unsafe_allow_html=True)