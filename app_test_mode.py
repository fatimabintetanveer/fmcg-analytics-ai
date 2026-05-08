import streamlit as st
import requests
from datetime import datetime

# --- SETTINGS & CONFIG ---
API_URL = "http://127.0.0.1:8000"
DEFAULT_ORG_ID = 4
DEFAULT_DATA_TYPE_ID = 104

# THE 10 EVALUATION QUESTIONS
TEST_QUESTIONS = [
    "What is the average price of TUNA in Goody?",
    "Between 200 GRAM and 400 GRAM, which pack size is growing the most in 'CANNED MUSHROOMS' in goody?",
    "How is TIM HORTONS performing in INSTANT COFFEE volume across different retailers in Jeddah?",
    "What is the monthly trend of Goody’s Tuna sales over the last 12 months?",
    "What is Goody’s volume share in the TUNA category?",
    "Compare volume sales of COFIQUE, and TIM HORTONS in the INSTANT COFFEE category",
    "What are the top 5 brands by volume sales in the CANNED VEGETABLE category?",
    "Compare Goody’s volume sales in TUNA between Riyadh and Jeddah.",
    "What is the year-over-year growth in volume sales for COFIQUE in the INSTANT COFFEE category?",
    "What is Goody’s volume share in the 80 GRAM pack size within the TUNA category?"
]

st.set_page_config(
    page_title="FMCG Insight AI - Test Mode",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .answer-card {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "test_mode_on" not in st.session_state:
    st.session_state.test_mode_on = False
if "current_test_idx" not in st.session_state:
    st.session_state.current_test_idx = 0
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False
if "selected_rating" not in st.session_state:
    st.session_state.selected_rating = 5

# --- HEADER ---
st.title("📊 FMCG Insight AI")
test_mode = st.toggle("🚀 Enable Test Mode", value=st.session_state.test_mode_on)
st.session_state.test_mode_on = test_mode

# --- PROGRESS BAR (Only in Test Mode) ---
if st.session_state.test_mode_on:
    progress = (st.session_state.current_test_idx + 1) / len(TEST_QUESTIONS)
    st.progress(progress, text=f"Evaluating Question {st.session_state.current_test_idx + 1} of {len(TEST_QUESTIONS)}")

st.write("---")

# --- CORE LOGIC ---
if st.session_state.test_mode_on:
    # --- TEST MODE UI ---
    if st.session_state.current_test_idx < len(TEST_QUESTIONS):
        current_q = TEST_QUESTIONS[st.session_state.current_test_idx]
        st.subheader(f"Current Test Question:")
        st.info(f"**{current_q}**")
        
        # Auto-run if no response for current question
        if st.session_state.last_response is None:
            with st.spinner("Executing Test Question..."):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        json={"question": current_q, "org_id": DEFAULT_ORG_ID, "data_type_id": DEFAULT_DATA_TYPE_ID}
                    )
                    if response.status_code == 200:
                        st.session_state.last_response = response.json()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.balloons()
        st.success("🎉 All test questions completed! Check your Langfuse dashboard for the scores.")
        if st.button("Reset Test Mode"):
            st.session_state.current_test_idx = 0
            st.session_state.last_response = None
            st.rerun()

else:
    # --- FREE CHAT MODE ---
    query_col, btn_col = st.columns([5, 1])
    with query_col:
        question = st.text_input("", placeholder="Ask anything about retail data...", label_visibility="collapsed")
    with btn_col:
        if st.button("Analyze", use_container_width=True, type="primary"):
            if question:
                with st.spinner("Analyzing..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/ask",
                            json={"question": question, "org_id": DEFAULT_ORG_ID, "data_type_id": DEFAULT_DATA_TYPE_ID}
                        )
                        if response.status_code == 200:
                            st.session_state.last_response = response.json()
                            st.session_state.feedback_submitted = False
                        else:
                            st.error(f"Error: {response.status_code}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

# --- DISPLAY RESULTS AREA ---
if st.session_state.last_response:
    data = st.session_state.last_response
    
    if "error" in data:
        st.error(f"❌ {data.get('error')}")
        if st.session_state.test_mode_on:
             if st.button("Skip to Next Question"):
                 st.session_state.current_test_idx += 1
                 st.session_state.last_response = None
                 st.rerun()
    else:
        # 1. Main Answer Card
        st.markdown('<div class="answer-card">', unsafe_allow_html=True)
        st.subheader("✅ AI Analysis Result")
        if data.get("calculated_results"):
            st.table(data["calculated_results"])
        else:
            st.write("No metrics calculated.")
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. Feedback Workflow (Required to progress in Test Mode)
        st.write("### 📝 Feedback & Progression")
        
        # Selection
        cols = st.columns([1,1,1,1,1,6])
        for i in range(1, 6):
            btn_type = "primary" if st.session_state.selected_rating == i else "secondary"
            if cols[i-1].button(f"{i} ⭐", key=f"rate_{i}", type=btn_type, use_container_width=True):
                st.session_state.selected_rating = i
                st.rerun()
        
        user_comment = st.text_area("Observations:", key="feedback_comment", placeholder="Optional details...")
        
        submit_btn_label = "Submit & Next Question" if st.session_state.test_mode_on else "Submit Feedback"
        
        if st.button(submit_btn_label, type="primary"):
            trace_id = data.get("trace_id")
            if trace_id:
                try:
                    requests.post(
                        f"{API_URL}/feedback",
                        json={
                            "trace_id": trace_id, 
                            "score": float(st.session_state.selected_rating), 
                            "comment": user_comment if user_comment else f"Test Mode: Q{st.session_state.current_test_idx+1}"
                        }
                    )
                    if st.session_state.test_mode_on:
                        st.session_state.current_test_idx += 1
                        st.session_state.last_response = None
                        st.session_state.selected_rating = 5 # Reset for next
                    else:
                        st.session_state.feedback_submitted = True
                    st.rerun()
                except:
                    st.error("Submission failed.")

        # 3. Technical Details
        with st.expander("🔍 View Technical Details"):
            st.code(data.get("numerator_sql", ""), language="sql")
            st.json(data.get("numerator_data"))
