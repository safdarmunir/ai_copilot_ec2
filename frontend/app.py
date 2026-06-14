import streamlit as st
import requests
import plotly.express as px
import pandas as pd
import os
import requests
import streamlit as st
# API_URL = "http://127.0.0.1:8000"
import os

#API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
import streamlit as st
import os

#API_URL = os.getenv(
#    "API_URL",
#    st.secrets.get(
#        "API_URL",#
#        "http://127.0.0.1:8000"
#    )
#)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI Business Copilot",
    layout="wide"
)

st.title("AI Business Operations Copilot")
documents_response = requests.get(
    f"{API_URL}/documents"
)

documents = []

if documents_response.status_code == 200:
    documents = documents_response.json().get(
        "documents",
        []
    )

if "copilot_history" not in st.session_state:
    st.session_state["copilot_history"] = []


tab1, tab2, tab3, tab4,tab5, tab6, tab7 = st.tabs(
    ["Upload", "Ask", "Documents", "Analytics","Copilot","Dashboard","Reports"]
)

with tab1:

    st.subheader("Upload Document")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=[".pdf", ".docx", ".txt", ".csv", ".xlsx"]
    )

    if st.button("Upload"):

        if uploaded_file:

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file,
                    uploaded_file.type
                )
            }

            response = requests.post(
                f"{API_URL}/upload",
                files=files
            )

            if response.status_code == 200:
                st.success(
                    response.json()["message"]
                )
            else:
                st.error(
                    response.text
                )

with tab2:

    st.subheader("Ask Questions")

    question = st.text_area(
        "Enter your question"
    )

    if st.button("Ask AI"):

        response = requests.post(
            f"{API_URL}/ask",
            json={
                "question": question
            }
        )

        if response.status_code == 200:

            data = response.json()

            st.markdown("### Answer")

            st.write(
                data["answer"]
            )

            st.markdown("### Sources")

            for source in data["sources"]:

                st.expander(
                    f"{source['filename']} - Chunk {source['chunk_index']}"
                ).write(
                    source["content"]
                )

        else:
            st.error(
                response.text
            )

with tab3:

    st.subheader("Uploaded Documents")

    response = requests.get(
        f"{API_URL}/documents"
    )

    if response.status_code == 200:

        docs = response.json()["documents"]

        for doc in docs:

            col1, col2, col3 = st.columns(
                [4, 2, 1]
            )

            col1.write(
                doc["filename"]
            )

            col2.write(
                f"{doc['size_kb']} KB"
            )

            if col3.button(
                "Delete",
                key=doc["filename"]
            ):

                requests.delete(
                    f"{API_URL}/document/{doc['filename']}"
                )

                st.rerun()

with tab4:
    st.subheader("Business Data Analytics")

    filename = st.text_input(
        "Enter CSV/XLSX filename",
        placeholder="dummy_sales.csv"
    )

    question = st.text_area(
        "Ask a business analytics question",
        placeholder="Which products generate the highest revenue?"
    )

    if st.button("Analyze Data"):
        response = requests.post(
            f"{API_URL}/analyze",
            json={
                "filename": filename,
                "question": question
            }
        )

        if response.status_code == 200:
            st.session_state["analysis_data"] = response.json()
            st.session_state["analysis_filename"] = filename
            st.session_state["analysis_question"] = question
        else:
            st.error(response.text)

    if "analysis_data" in st.session_state:
        data = st.session_state["analysis_data"]

        st.markdown("### Answer")
        st.write(data["answer"])

        st.markdown("### Calculated Table")
        st.dataframe(data["table"])

        if data.get("chart_path"):
            st.markdown("### Chart")
            chart_url = f"{API_URL}{data['chart_path']}"
            st.image(chart_url)

        if st.button("Generate DOCX Report"):
            report_response = requests.post(
                f"{API_URL}/generate-report",
                json={
                    "filename": st.session_state["analysis_filename"],
                    "question": st.session_state["analysis_question"],
                    "answer": data["answer"],
                    "table": data["table"],
                    "chart_path": data.get("chart_path")
                }
            )

            if report_response.status_code == 200:
                report_data = report_response.json()
                report_url = f"{API_URL}{report_data['report_path']}"

                st.success("Report generated successfully")
                st.markdown(f"[Download Report]({report_url})")
            else:
                st.error(report_response.text)

        st.markdown("### Metadata")
        st.write(f"Analysis Type: `{data['analysis_type']}`")
        st.write(f"Rows: `{data['rows']}`")


with tab5:

    st.subheader("AI Business Copilot")

    selected_file = st.selectbox(
        "Select File (Optional)",
        [""] + [doc["filename"] for doc in documents]
    )

    copilot_question = st.text_area(
        "Ask Anything",
        placeholder="Summarize llm.pdf OR Which products generate highest revenue? OR Forecast next 3 months revenue"
    )

    if st.button("Ask Copilot"):

        response = requests.post(
            f"{API_URL}/copilot",
            json={
                "question": copilot_question,
                "filename": selected_file if selected_file else None
            }
        )

        if response.status_code == 200:

            result = response.json()

            st.success(f"Routed To: {result['route']}")

            if "answer" in result:
                st.markdown("### Answer")
                st.write(result["answer"])

            if "table" in result:
                st.markdown("### Results")
                st.dataframe(result["table"])

            if result.get("chart_path"):
                chart_url = f"{API_URL}{result['chart_path']}"
                st.image(chart_url)

            if "sources" in result:
                with st.expander("Sources"):
                    st.json(result["sources"])

        else:
            st.error(response.text)

    st.markdown("### Saved Chat History")

    history_response = requests.get(
        f"{API_URL}/chat-history"
    )

    if history_response.status_code == 200:

        history = history_response.json()["history"]

        if history:
            with st.expander("View Saved Chat History"):
                for msg in history:
                    st.write(
                        f"**{msg['role'].title()}** "
                        f"| Route: `{msg['route']}` "
                        f"| File: `{msg['filename']}`"
                    )
                    st.write(msg["content"])
                    st.caption(msg["created_at"])
                    st.divider()
        else:
            st.info("No saved chat history yet.")

    else:
        st.error("Could not load chat history.")

    if st.button("Clear Saved Chat History"):
        clear_response = requests.delete(
            f"{API_URL}/chat-history"
        )

        if clear_response.status_code == 200:
            st.success("Saved chat history cleared")
            st.rerun()
        else:
            st.error("Could not clear chat history.")


with tab6:

    st.subheader("Executive Dashboard")

    selected_file = st.selectbox(
        "Select Sales File",
        [
            doc["filename"]
            for doc in documents
            if doc["filename"].endswith(
                (".csv", ".xlsx")
            )
        ]
    )

    if st.button("Load Dashboard"):

        response = requests.post(
            f"{API_URL}/dashboard",
            json={
                "filename": selected_file
            }
        )

        if response.status_code == 200:

            data = response.json()

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Total Revenue",
                f"${data['total_revenue']:,.0f}"
            )

            c2.metric(
                "Total Orders",
                data["total_orders"]
            )

            c3.metric(
                "Avg Order Value",
                f"${data['average_order_value']:,.0f}"
            )

            c4, c5, c6 = st.columns(3)

            c4.metric(
                "Top Product",
                data["top_product"]
            )

            c5.metric(
                "Top Customer",
                data["top_customer"]
            )

            c6.metric(
                "Top Region",
                data["top_region"]
            )

            chart_response = requests.post(
                f"{API_URL}/dashboard-data",
                json={
                    "filename": selected_file
                }
            )

        if chart_response.status_code == 200:

            charts = chart_response.json()

            product_df = pd.DataFrame(
                charts["products"]
            )

            region_df = pd.DataFrame(
                charts["regions"]
            )

            monthly_df = pd.DataFrame(
                charts["monthly"]
            )


            fig = px.bar(
                product_df,
                x="product",
                y="revenue",
                title="Revenue by Product"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            fig = px.pie(
                region_df,
                names="region",
                values="revenue",
                title="Revenue by Region"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            fig = px.line(
                monthly_df,
                x="order_date",
                y="revenue",
                markers=True,
                title="Monthly Revenue Trend"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )


        else:
            st.error(response.text)

        


with tab7:

    st.subheader("Generated Reports")

    reports_response = requests.get(
        f"{API_URL}/reports"
    )

    if reports_response.status_code == 200:

        reports = reports_response.json()["reports"]

        if reports:

            for report in reports:

                st.write(
                    f"**File:** {report['filename']}"
                )

                st.write(
                    f"**Question:** {report['question']}"
                )

                st.write(
                    f"**Created:** {report['created_at']}"
                )

                report_url = (
                    f"{API_URL}{report['report_path']}"
                )

                download_response = requests.get(
                    report_url
                )

                if download_response.status_code == 200:

                    st.download_button(
                        label="Download Report",
                        data=download_response.content,
                        file_name=report["report_path"].split("/")[-1],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=report["report_path"]
                    )

                st.divider()

        else:
            st.info("No reports found.")

    else:
        st.error("Could not load reports.")



st.subheader("Upload File to AWS S3")

uploaded_file = st.file_uploader(
    "Choose a file to upload to S3",
    type=["pdf", "txt", "csv", "xlsx", "docx"],
    key="s3_file_uploader"
)

if uploaded_file is not None:
    if st.button("Upload to S3"):
        try:
            api_url = os.getenv("API_URL", "http://localhost:8000")
            upload_endpoint = f"{api_url}/files/upload"

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            response = requests.post(upload_endpoint, files=files, timeout=60)

            if response.status_code == 200:
                result = response.json()

                st.success("File uploaded to S3 successfully.")
                st.write("Original filename:", result["data"]["original_filename"])
                st.write("S3 bucket:", result["data"]["bucket"])
                st.write("S3 key:", result["data"]["s3_key"])
                st.write("Content type:", result["data"]["content_type"])
            else:
                st.error("Upload failed.")
                st.write(response.text)

        except Exception as e:
            st.error(f"Upload error: {e}")