import streamlit as st
import pandas as pd
import openai
import os

# Initialize folders for input, output, and logs
input_excel_folder = "input_excel_folder"
output_responses_folder = "output_responses_folder"
log_folder = "log_folder"
os.makedirs(input_excel_folder, exist_ok=True)
os.makedirs(output_responses_folder, exist_ok=True)
os.makedirs(log_folder, exist_ok=True)

# Initialize session state for conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Streamlit Interface
st.title("Excel Dashboard Interpreter - Powered by Gemini AI")

# API Key Input
api_key = st.text_input("Enter your Gemini API Key:", type="password")
if api_key:
    openai.api_key = api_key

# File Upload
uploaded_file = st.file_uploader("Upload an Excel file containing a dashboard extract", type=['xlsx'])

# Instructions Input
instructions = st.text_area("Enter your query or instructions regarding the Excel dashboard:")

# Display the conversation history
st.subheader("Conversation History")
for entry in st.session_state.conversation_history:
    st.markdown(f"**User:** {entry['user']}")
    st.markdown(f"**AI:** {entry['ai']}")

# New prompt input
new_prompt = st.text_area("Enter your next query:")

if st.button("Send"):
    if not new_prompt and not instructions and not uploaded_file:
        st.error("Please enter a query or upload an Excel file to continue.")
    else:
        combined_text = ""
        dashboard_structure = ""
        if uploaded_file:
            # Save and read the Excel file
            filename = uploaded_file.name
            filepath = os.path.join(input_excel_folder, filename)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Read the Excel file into pandas
            try:
                # Read the Excel file
                excel_data = pd.ExcelFile(filepath)
                dashboard_sheets = excel_data.sheet_names

                # Iterate through each sheet to parse grids and visual data
                for sheet in dashboard_sheets:
                    df = pd.read_excel(excel_data, sheet_name=sheet)
                    combined_text += f"\nSheet: {sheet}\n"
                    combined_text += df.to_string()

                    # Generate a summary of the sheet's structure for the AI prompt
                    dashboard_structure += f"\nSheet: {sheet}\n"
                    dashboard_structure += f"Number of rows: {df.shape[0]}, Number of columns: {df.shape[1]}\n"
                    dashboard_structure += "This sheet contains data typically displayed in grids and charts.\n"

                st.write(f"Data extracted from the uploaded Excel dashboard:\n{combined_text[:500]}...")  # Display a preview

            except Exception as e:
                st.error(f"Error reading the Excel file: {e}")

        # Construct the detailed prompt
        prompt = f"""
        You are analyzing an Excel file that serves as an extract from a business dashboard. The dashboard contains various sheets 
        with data represented in grids and visualized through charts. Below is a detailed description of the dashboard:

        {dashboard_structure}

        The user has provided the following instructions: {instructions}

        Additionally, consider this context extracted from the data: {combined_text[:1000]} (truncated for brevity).

        Please provide insights on:
        - The trends and patterns visible in the dashboard.
        - Observations from the legends and any notable differences between data points.
        - Recommendations or high-level summaries based on the data visualization.
        """

        # Send the prompt to the Gemini API (using OpenAI as a placeholder)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            ai_response = response.choices[0].message['content']

            # Save the interaction to the session state
            st.session_state.conversation_history.append({
                "user": new_prompt,
                "ai": ai_response
            })

            # Display AI response
            st.write("Conversation Response:")
            st.write(ai_response)

            # Logging
            today = pd.Timestamp.now().strftime("%Y-%m-%d")
            log_file = os.path.join(log_folder, f"{today}.log")
            with open(log_file, 'a') as log:
                log.write(f"User: {new_prompt}\nAI: {ai_response}\n")

            # Save response
            output_filename = f"Conversation_Output_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt"
            output_path = os.path.join(output_responses_folder, output_filename)
            with open(output_path, 'w') as output_file:
                output_file.write(ai_response)

            st.success("Conversation updated. Check the log and output files.")

        except openai.error.APIError as e:
            st.error(f"OpenAI API error: {e}")

if st.button("Clear Conversation History"):
    st.session_state.conversation_history = []
    st.success("Conversation history cleared successfully.")
