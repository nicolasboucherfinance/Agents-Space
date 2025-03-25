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

# Streamlit UI
st.set_page_config(page_title="Revenue Sankey Visualizer", page_icon="💰", layout="wide")
st.title("💸 Revenue Flow Sankey Chart Generator")
st.write("Upload an Excel file with 'Product' and 'Revenue' columns to visualize how revenue is distributed.")

uploaded_file = st.file_uploader("📤 Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Basic Validation
        if "Product" not in df.columns or "Revenue" not in df.columns:
            st.error("❌ Your file must include 'Product' and 'Revenue' columns.")
            st.stop()

        df_grouped = df.groupby("Product", as_index=False)["Revenue"].sum()

        # Sankey preparation
        st.subheader("🔗 Sankey Chart")
        labels = ["Total Revenue"] + df_grouped["Product"].tolist()
        sources = [0] * len(df_grouped)
        targets = list(range(1, len(df_grouped) + 1))
        values = df_grouped["Revenue"].tolist()

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            ))])

        fig.update_layout(title_text="Revenue Breakdown by Product", font_size=12)
        st.plotly_chart(fig, use_container_width=True)

        # AI Commentary using Groq
        st.subheader("🧠 AI Insights on Revenue")
        client = Groq(api_key=GROQ_API_KEY)

        data_for_ai = df_grouped.to_json(orient="records")

        prompt = f"""
        You are a financial analyst. Based on the following revenue data by product, provide:
        - Key revenue concentration observations
        - Any risks related to product reliance
        - Recommendations to diversify or optimize revenue.
        Data:
        {data_for_ai}
        """

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a revenue analyst and SaaS finance expert."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
        )

        ai_commentary = response.choices[0].message.content
        st.markdown("### 📘 AI-Generated Analysis")
        st.write(ai_commentary)

    except Exception as e:
        st.error(f"Something went wrong while processing the file: {e}")
