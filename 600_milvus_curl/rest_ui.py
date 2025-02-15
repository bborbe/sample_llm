import streamlit as st
import requests

# FastAPI URL for generating answers
API_URL = "http://localhost:5001/generate"

st.title("LangGraph Streamlit UI")
st.write("Ask your question, and let the system analyze it!")

# Input field for the user's question
question = st.text_input("Enter your question:")

if st.button("Submit"):
    if question.strip():
        st.write("Processing your question... Please wait.")
        try:
            # Call the FastAPI endpoint
            response = requests.post(API_URL, json={"question": question})
            response.raise_for_status()  # Raise exception for HTTP errors

            # Display results from the API
            result = response.json()
            st.success("Analysis completed!")
            st.write("Result:", result["result"][-1]["generate"]["generation"])
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a question before submitting.")
