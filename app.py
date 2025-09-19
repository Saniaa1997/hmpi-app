# app.py
import streamlit as st
import pandas as pd
import json
import os
from backend.utils import load_limits, validate_dataframe, categorize_hmpi, categorize_mci
from backend.indices import calculate_hmpi, calculate_mci, calculate_pi_table
from backend.geo_utils import build_gdf, folium_map_from_gdf
from backend.chatbot import get_chatbot_response
from streamlit_folium import st_folium

# --- Page Configuration ---
st.set_page_config(
    page_title="HMPI Water Quality System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for UI Enhancement ---
def load_css():
    st.markdown("""
    <style>
        /* Main background animation */
        body {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            height: 100vh;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Styling for Streamlit components */
        .stApp {
            background-color: rgba(255, 255, 255, 0.1); /* Slightly transparent background for the app */
        }
        .st-emotion-cache-16txtl3 {
            padding: 2rem 2rem;
        }
        h1, h2, h3 {
            color: #FFFFFF; /* White text for titles */
        }
        .st-emotion-cache-1y4p8pa {
             max-width: 95%;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Authentication State ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- Load initial data ---
limits = load_limits("limits.json")
required_metals = list(limits.keys())

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📈 Analysis", "🗺️ Map", "🤖 Chatbot", "🔑 Admin"])
st.sidebar.markdown("---")
st.sidebar.info("This app calculates the Heavy Metal Pollution Index (HMPI) for water quality assessment.")


# ===============================================
# ANALYSIS PAGE
# ===============================================
if page == "📈 Analysis":
    st.title("📈 Water Quality Analysis")
    st.markdown("Upload your CSV data, map the columns, and compute pollution indices in seconds.")

    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"], help="Ensure your CSV has columns for heavy metal concentrations.")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.subheader("Data Preview")
        st.dataframe(df.head())

        st.subheader("Column Mapping")
        with st.form("mapping_form"):
            cols = ["<Select Column>"] + df.columns.tolist()
            c1, c2 = st.columns(2)
            col_map = {}
            for i, metal in enumerate(required_metals):
                container = c1 if i % 2 == 0 else c2
                default_index = cols.index(metal) if metal in cols else 0
                mapped_col = container.selectbox(f"Column for `{metal}`", options=cols, index=default_index, key=f"map_{metal}")
                col_map[metal] = mapped_col if mapped_col != "<Select Column>" else None

            lat_col = st.selectbox("Latitude column (optional)", options=["<Select Column>"] + cols)
            lon_col = st.selectbox("Longitude column (optional)", options=["<Select Column>"] + cols)
            
            submitted = st.form_submit_button("Apply Mapping & Validate")

        if submitted:
            with st.spinner('Validating data...'):
                mapped_df = df.copy()
                rename_map = {v: k for k, v in col_map.items() if v}
                if lat_col != "<Select Column>": rename_map[lat_col] = "latitude"
                if lon_col != "<Select Column>": rename_map[lon_col] = "longitude"
                
                mapped_df = mapped_df.rename(columns=rename_map)
                st.session_state['mapped_df'] = mapped_df

                valid, report = validate_dataframe(mapped_df, required_metals)
                st.subheader("Validation Report")
                if not valid:
                    st.error("Validation failed. Please map all required metal columns.")
                    st.json(report)
                else:
                    st.success("Validation passed!")
                    st.json(report)

    if 'mapped_df' in st.session_state and st.button("Compute Indices", type="primary"):
        with st.spinner('Calculating HMPI, MCI, and PI... This might take a moment.'):
            results_df = st.session_state['mapped_df'].copy()
            
            results_df["HMPI"] = calculate_hmpi(results_df, limits)
            results_df["HMPI_Category"] = results_df["HMPI"].apply(categorize_hmpi)
            results_df["MCI"] = calculate_mci(results_df, limits)
            results_df["MCI_Category"] = results_df["MCI"].apply(categorize_mci)
            pi_df = calculate_pi_table(results_df, limits)
            results_df = pd.concat([results_df, pi_df], axis=1)

            st.session_state["last_results"] = results_df
            st.success("🎉 Calculation Complete!")
    
    if "last_results" in st.session_state:
        # --- START: Summary Dashboard Code ---
        st.subheader("Analysis Summary")
        results_df = st.session_state["last_results"]
        
        # Calculate counts (we'll define 'polluted' as HMPI >= 100)
        polluted_count = len(results_df[results_df['HMPI'] >= 100])
        safe_count = len(results_df) - polluted_count

        # Display in styled columns
        col1, col2 = st.columns(2)
        
        col1.markdown(f"""
        <div style="background-color: #28a745; padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <h3 style="color: white;">💧 Safe Samples</h3>
            <h1 style="color: white; font-size: 2.5em;">{safe_count}</h1>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div style="background-color: #dc3545; padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <h3 style="color: white;">☣️ Polluted Samples</h3>
            <h1 style="color: white; font-size: 2.5em;">{polluted_count}</h1>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True) # Add some space
        # --- END: Summary Dashboard Code ---
        st.subheader("Analysis Results")
        st.dataframe(st.session_state["last_results"])

        st.subheader("Download Results")
        c1, c2 = st.columns(2)
        csv = st.session_state["last_results"].to_csv(index=False).encode("utf-8")
        c1.download_button("Download as CSV", csv, "hmpi_results.csv", "text/csv", use_container_width=True)
        # Note: PDF generation would require the 'reporting.py' file from the previous response.
        # pdf_buffer = generate_pdf_report(st.session_state["last_results"])
        # c2.download_button("Download PDF Report", pdf_buffer, "hmpi_report.pdf", "application/pdf", use_container_width=True)

# ===============================================
# MAP PAGE
# ===============================================
elif page == "🗺️ Map":
    st.title("🗺️ Geospatial Map View")
    if "last_results" not in st.session_state:
        st.info("Please run an analysis first to view the map.")
    else:
        res = st.session_state["last_results"]
        try:
            with st.spinner("Building map..."):
                gdf = build_gdf(res)
                def palette(val):
                    if pd.isna(val): return "gray"
                    if val < 50: return "green"
                    if val < 100: return "orange"
                    if val < 200: return "red"
                    return "darkred"
                
                popup_fields = [col for col in ["SampleID", "HMPI", "HMPI_Category", "MCI", "MCI_Category"] if col in gdf.columns]
                m = folium_map_from_gdf(gdf, value_col="HMPI", palette=palette, popup_fields=popup_fields)
                st_folium(m, width=1200, height=700, returned_objects=[])
        except ValueError as e:
            st.error(f"Could not build map: {e}. Ensure your data has 'latitude' and 'longitude' columns.")

# ===============================================
# CHATBOT PAGE
# ===============================================
elif page == "🤖 Chatbot":
    st.title("🤖 Project Chatbot Assistant")
    st.info("This chatbot uses the Google Gemini API. Please provide your API key to begin.")

    api_key = st.text_input("Enter your Google Gemini API Key", type="password", key="chatbot_api_key")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you understand the HMPI project?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    if prompt := st.chat_input("Ask about HMPI formulas, app usage, etc."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_chatbot_response(api_key, prompt)
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ===============================================
# ADMIN PAGE
# ===============================================
elif page == "🔑 Admin":
    st.title("🔑 Admin Configuration")

    if not st.session_state['authenticated']:
        st.warning("Please enter the password to access admin settings.")
        password = st.text_input("Password", type="password")
        ADMIN_PASSWORD = os.environ.get("HMPI_ADMIN_PASSWORD", "admin123")
        if st.button("Login"):
            if password == ADMIN_PASSWORD:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("The password you entered is incorrect.")
    
    if st.session_state['authenticated']:
        st.success("Authenticated Successfully.")
        st.subheader("Edit Permissible Limits (mg/L)")
        
        current_limits_str = json.dumps(limits, indent=2)
        edited_limits_str = st.text_area("Edit limits in JSON format:", value=current_limits_str, height=250)

        if st.button("Save Changes"):
            try:
                new_limits = json.loads(edited_limits_str)
                with open("limits.json", "w") as f:
                    json.dump(new_limits, f, indent=2)
                st.success("Limits updated successfully! They will be applied on the next analysis.")
            except json.JSONDecodeError:
                st.error("Invalid JSON format. Please check your syntax.")
        
        if st.button("Logout"):
            st.session_state['authenticated'] = False

            st.rerun()

