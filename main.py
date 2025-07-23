import streamlit as st
from backend import get_response

st.set_page_config(page_title="Trek GPT", layout="wide")

st.title("🧭 Trek GPT: InnerTrek's Facilitator Companion")
st.markdown("Ask a question below, and Trek GPT will respond based on InnerTrek’s educator-led training transcripts.")

query = st.text_input("Your question", "")

if query:
    with st.spinner("Thinking..."):
        response, sources = get_response(query)
        st.markdown("### ✨ Answer")
        st.markdown(response)

        if sources:
            st.markdown("---")
            st.markdown("### 📚 Sources")
            for i, node in enumerate(sources, 1):
                metadata = node.metadata
                st.markdown(f"**{i}.** *{metadata.get('title', 'Untitled')}* — {metadata.get('educator', 'Unknown')}")
