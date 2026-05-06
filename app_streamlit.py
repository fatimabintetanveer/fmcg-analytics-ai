import streamlit as st
import requests
from datetime import datetime

# --- SETTINGS & CONFIG ---
API_URL = "http://127.0.0.1:8000"
DEFAULT_ORG_ID = 4
DEFAULT_DATA_TYPE_ID = 104

st.set_page_config(
    page_title="FMCG Insight AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .answer-card {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False
if "selected_rating" not in st.session_state:
    st.session_state.selected_rating = 5

# --- HEADER ---
st.title("📊 FMCG Insight AI")
st.markdown("Query your retail data using natural language.")

# --- SEARCH AREA ---
with st.container():
    query_col, btn_col = st.columns([5, 1])
    with query_col:
        question = st.text_input("", placeholder="e.g. Compare volume sales of COFIQUE and TIM HORTONS", label_visibility="collapsed")
    with btn_col:
        if st.button("Analyze", use_container_width=True, type="primary"):
            if question:
                with st.spinner("Analyzing data..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/ask",
                            json={
                                "question": question,
                                "org_id": DEFAULT_ORG_ID,
                                "data_type_id": DEFAULT_DATA_TYPE_ID
                            }
                        )
                        if response.status_code == 200:
                            st.session_state.last_response = response.json()
                            st.session_state.feedback_submitted = False 
                        else:
                            st.error(f"Error: {response.status_code}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

st.write("---")

# --- RESULTS AREA ---
if st.session_state.last_response:
    data = st.session_state.last_response
    
    if "error" in data:
        st.error(f"❌ {data.get('error')}")
        st.info(data.get("details", ""))
    else:
        # 1. Main Answer
        st.markdown('<div class="answer-card">', unsafe_allow_html=True)
        st.subheader("✅ AI Analysis Result")
        if data.get("calculated_results"):
            st.table(data["calculated_results"])
        else:
            st.write("Data retrieved successfully, but no metrics were calculated.")
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. Feedback Workflow
        st.write("### 📝 Rate this analysis")
        if not st.session_state.feedback_submitted:
            
            # Step 1: Star Selection (Horizontal row)
            st.write("Step 1: Select your rating")
            cols = st.columns([1,1,1,1,1,6])
            for i in range(1, 6):
                # Highlight the selected star
                btn_type = "primary" if st.session_state.selected_rating == i else "secondary"
                if cols[i-1].button(f"{i} ⭐", key=f"rate_{i}", type=btn_type, use_container_width=True):
                    st.session_state.selected_rating = i
                    st.rerun()
            
            # Step 2: Comment Box 
            st.write("Step 2: Add details")
            user_comment = st.text_area("", key="feedback_comment", placeholder="What could be improved?", label_visibility="collapsed")
            
            # Step 3: Dedicated Submit Button
            if st.button("Submit Feedback", type="primary"):
                trace_id = data.get("trace_id")
                if trace_id:
                    try:
                        res = requests.post(
                            f"{API_URL}/feedback",
                            json={
                                "trace_id": trace_id, 
                                "score": float(st.session_state.selected_rating), 
                                "comment": user_comment if user_comment else f"Rated {st.session_state.selected_rating} stars"
                            }
                        )
                        if res.status_code == 200:
                            st.session_state.feedback_submitted = True
                            st.success("Thank you! Feedback submitted.")
                            st.rerun()
                        else:
                            st.error(f"Error: {res.text}")
                    except Exception as e:
                        st.error(f"Submission failed: {e}")
        else:
            st.success("✅ Thank you! Your feedback has been sent to Langfuse.")

        st.write("---")

        # 3. Technical Details
        with st.expander("🔍 View Technical Details"):
            tab1, tab2 = st.tabs(["SQL Queries", "Raw JSON Data"])
            with tab1:
                st.code(data.get("numerator_sql", ""), language="sql")
                if data.get("denominator_sql"):
                    st.code(data.get("denominator_sql"), language="sql")
            with tab2:
                st.json(data.get("numerator_data"))
                if data.get("denominator_data"):
                    st.json(data.get("denominator_data"))
