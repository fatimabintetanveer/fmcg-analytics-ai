import streamlit as st
import requests

st.title("FMCG Chat Assistant 📊")

question = st.text_input("Ask your question:")

if st.button("Submit"):
    if question:
        with st.spinner("Running query..."):

            response = requests.post(
                "http://127.0.0.1:8000/ask",
                json={"question": question}
            )

            data = response.json()

            if data.get("calculated_results"):
                st.subheader("✅ Final Answer")
                st.table(data["calculated_results"])
                

            st.subheader("📌 Generated SQL")
            st.code(data.get("numerator_sql", ""), language="sql")

            if data.get("denominator_sql"):
                st.subheader("📌 Denominator SQL")
                st.code(data.get("denominator_sql"), language="sql")

            st.subheader("📊 Result")
            st.json(data.get("numerator_data"))

            if data.get("denominator_data"):
                st.subheader("📊 Denominator Result")
                st.json(data.get("denominator_data"))
