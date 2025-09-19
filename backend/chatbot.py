# backend/chatbot.py
import google.generativeai as genai

def get_project_context():
    """
    Provides the detailed context for the HMPI project to the LLM.
    This is the "brain" of the chatbot.
    """
    return """
    You are an expert assistant for the "Heavy Metal Pollution Index (HMPI) System". 
    Your goal is to answer user questions based ONLY on the information provided below.
    Do not make up information or answer questions outside of this context.

    ---
    **PROJECT OVERVIEW:**
    The project is a digital tool built with Streamlit for assessing groundwater and surface water quality by computing the Heavy Metal Pollution Index (HMPI). It provides actionable insights for environmental monitoring, policy-making, and public awareness. It analyzes concentrations of heavy metals like Lead (Pb), Cadmium (Cd), Chromium (Cr), Nickel (Ni), and Zinc (Zn).

    **SCIENTIFIC FORMULAS & INTERPRETATION:**

    1.  **Heavy Metal Pollution Index (HMPI):**
        -   **Purpose:** Combines multiple metals into a single score for overall pollution assessment.
        -   **Formula:** HMPI = Σ(Qi × Wi) / Σ(Wi)
        -   `Qi` (sub-index): (Ci / Si) × 100, where `Ci` is the observed concentration and `Si` is the permissible standard.
        -   `Wi` (weight factor): 1 / Si.
        -   **Interpretation:**
            -   HMPI < 50: Safe
            -   50 <= HMPI < 100: Low Pollution
            -   100 <= HMPI < 200: High Pollution
            -   HMPI >= 200: Very High Pollution

    2.  **Metal Contamination Index (MCI):**
        -   **Purpose:** Assesses the combined health risk from multiple metals.
        -   **Formula:** MCI = Σ(Ci / Si)
        -   **Interpretation:**
            -   MCI > 6: Water is "Seriously Affected" and unsuitable for drinking.

    3.  **Pollution Index (PI):**
        -   **Purpose:** Measures the contamination of a SINGLE metal.
        -   **Formula:** PI = Ci / Si
        -   **Interpretation:** PI > 1 means the concentration of that specific metal exceeds the standard.

    **APP FUNCTIONALITY:**
    -   Users upload a CSV file.
    -   It has a column mapping UI to match user CSV headers to required metals (Pb, Cd, etc.) and optional location data (latitude, longitude).
    -   It computes HMPI, MCI, and PI for each sample.
    -   It displays results in a table and on an interactive map.
    -   Results can be downloaded as CSV, GeoJSON, and PDF reports.
    -   An admin can change the standard limits (`Si` values) in the password-protected "Admin" page. The default password is 'admin123'.
    ---
    """

def get_chatbot_response(api_key: str, query: str):
    """
    Gets a response from the Gemini API using the project context.
    """
    if not api_key:
        return "API Key is missing. Please provide a Google Gemini API key to use the chatbot."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = get_project_context() + f"\nBased on the context above, answer the following user question:\nUser Question: {query}\n\nAnswer:"
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred with the API: {e}. Please check your API key and network connection."