import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from groq import Groq
import plotly.graph_objects as go

# Load API key securely
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in Streamlit Secrets or a .env file.")
    st.stop()

# Streamlit UI Setup
st.set_page_config(page_title="Sankey Analyzer + Email Insights", page_icon="📧", layout="wide")
st.title("📈 Custom Sankey Chart + AI Email Generator")
st.write("Upload your Excel file, choose flow columns, and generate a Sankey diagram with shareable insights.")

uploaded_file = st.file_uploader("📤 Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ File uploaded successfully.")

        # Column selection
        headers = df.columns.tolist()
        st.markdown("### 🧩 Select Columns for Sankey Nodes")
        selected_columns = st.multiselect(
            "Pick the sequence of columns (at least 2):",
            options=headers,
            default=headers[:2] if len(headers) >= 2 else []
        )

        if len(selected_columns) < 2:
            st.warning("Please select at least two columns.")
            st.stop()

        st.markdown("### 📊 Sankey Chart")

        sankey_df = df[selected_columns].dropna()
        labels = []
        label_to_index = {}
        index = 0

        for col in selected_columns:
            for val in sankey_df[col].unique():
                if val not in label_to_index:
                    label_to_index[val] = index
                    labels.append(val)
                    index += 1

        source = []
        target = []
        value = []

        for i in range(len(selected_columns) - 1):
            grouped = sankey_df.groupby([selected_columns[i], selected_columns[i + 1]]).size().reset_index(name='count')
            for _, row in grouped.iterrows():
                source.append(label_to_index[row[selected_columns[i]]])
                target.append(label_to_index[row[selected_columns[i + 1]]])
                value.append(row['count'])

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            )
        )])

        fig.update_layout(title_text="📈 Sankey Diagram", font_size=12)
        st.plotly_chart(fig, use_container_width=True)

        # AI Commentary
        st.markdown("### 🧠 AI Analysis of Flow Data")
        client = Groq(api_key=GROQ_API_KEY)

        grouped_data_json = sankey_df[selected_columns].value_counts().reset_index(name='count').to_json(orient="records")

        ai_prompt = f"""
        You are a business analyst. Here is a flow of data between the following stages:
        {selected_columns}

        The data shows how entities move from one stage to another. Please analyze the data:
        - Identify dominant paths and bottlenecks
        - Suggest any surprising trends
        - Recommend actions based on the data flow

        Data:
        {grouped_data_json}
        """

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a data flow and business analysis expert."},
                {"role": "user", "content": ai_prompt}
            ],
            model="llama3-8b-8192",
        )

        ai_commentary = response.choices[0].message.content
        st.markdown("#### 📘 AI Insight")
        st.write(ai_commentary)

        # --- Generate Email ---
        st.markdown("### 📧 Email Draft to Share Insights")

        email_prompt = f"""
        Write a concise, professional email to a CFO that summarizes the analysis of this data flow. Use the Pyramid Principle:
        - Start with the key insight
        - Then explain the main observations
        - Close with recommendations
        The tone should be formal and executive-friendly.

        Here is the analysis:
        {ai_commentary}
        """

        email_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a strategic finance expert skilled at writing executive-level communication."},
                {"role": "user", "content": email_prompt}
            ],
            model="llama3-8b-8192",
        )

        email_body = email_response.choices[0].message.content
        st.text_area("✉️ Email Draft", value=email_body, height=300)
        st.download_button("📥 Download Email as .txt", email_body, file_name="insight_email.txt")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
