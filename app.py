import streamlit as st
import os
import json
from dotenv import load_dotenv

# Set page config first so error reporting can render UI components
st.set_page_config(
    page_title="ContentForge AI",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from modules.loader import load_documents
    from modules.vectorstore import create_vectorstore, is_vectorstore_empty
    from modules.generator import generate_content
    from modules.database import (
        init_db,
        save_generation,
        get_history,
        delete_history_item,
        clear_history
    )
except Exception as e:
    import traceback
    st.error("### 🚨 Import Error Traceback")
    st.code(traceback.format_exc())
    st.stop()

# Load environment variables
load_dotenv()

# Initialize SQLite database
init_db()

# Custom CSS for Premium Design Aesthetics
st.markdown("""
<style>
    /* Gradient headers */
    .main-title {
        background: linear-gradient(135deg, #6C63FF 0%, #3F3D56 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        color: #6C63FF;
        font-weight: 500;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Modern card boxes */
    .premium-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Styled buttons with hover animations */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Stat badges */
    .stat-badge {
        background-color: rgba(108, 99, 255, 0.15);
        color: #6C63FF;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-right: 0.8rem;
    }
    
    /* Source expanders */
    .source-header {
        font-weight: 600;
        color: #6C63FF;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Initialize Session State
# -----------------------------
if "generated_content" not in st.session_state:
    st.session_state.generated_content = None
if "sources" not in st.session_state:
    st.session_state.sources = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0
if "view_history_item" not in st.session_state:
    st.session_state.view_history_item = None

# Header Section
st.markdown("<h1 class='main-title'>✍️ ContentForge AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>RAG-Powered AI Content Generator & Writer</div>", unsafe_allow_html=True)

# -----------------------------
# API Key Verification
# -----------------------------
google_api_key = os.getenv("GOOGLE_API_KEY")
api_key_valid = True

if not google_api_key or google_api_key.startswith("YOUR_") or len(google_api_key) < 10:
    st.error("⚠️ **Google Gemini API Key is missing or invalid!**")
    st.info("Please set the `GOOGLE_API_KEY` environment variable in your `.env` file to start generating content.")
    api_key_valid = False

# -----------------------------
# Sidebar Setup
# -----------------------------
with st.sidebar:
    st.image("https://img.icons8.com/illustrations/external-pack-flat-line-design-circle/100/external-ai-artificial-intelligence-pack-flat-line-design-circle.png", width=80)
    st.title("Settings Panel")
    
    # Knowledge Base Status Indicator
    st.markdown("### 📊 Knowledge Base Status")
    is_kb_empty = is_vectorstore_empty()
    if is_kb_empty:
        st.markdown("<span style='color:#FF4B4B; font-weight:bold;'>🔴 Empty (No Documents Loaded)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#00E676; font-weight:bold;'>🟢 Active (Ready for RAG)</span>", unsafe_allow_html=True)
        
    st.divider()
    
    st.markdown("### 📄 Document Uploader")
    uploaded_files = st.file_uploader(
        "Upload PDF, DOCX, or TXT reference files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="These files will be split, embedded, and added to your Vector store as context for RAG."
    )
    
    # KB update mode option
    append_mode = st.checkbox("Append to existing documents", value=False, 
                              help="If unchecked, the existing Knowledge Base is cleared and rebuilt from scratch.")
    
    if st.button("🔄 Build/Update Knowledge Base", use_container_width=True):
        if not uploaded_files:
            st.warning("Please upload at least one document.")
        else:
            with st.spinner("Processing files and writing embeddings..."):
                try:
                    documents = load_documents(uploaded_files)
                    create_vectorstore(documents, overwrite=not append_mode)
                    st.success("Knowledge Base updated successfully! 🎉")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error building vector store: {e}")
                    
    st.divider()
    
    # Advanced Model Settings
    with st.expander("⚙️ Advanced Model Configurations", expanded=False):
        model_name = st.selectbox(
            "Gemini Model",
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0,
            help="gemini-2.5-flash is extremely fast; gemini-2.5-pro offers superior reasoning and logic."
        )
        
        temperature = st.slider(
            "Creativity (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            help="Lower values are more structured and factual. Higher values are more creative."
        )

# -----------------------------
# Main Application Tabs
# -----------------------------
tab_generate, tab_history = st.tabs(["🚀 Generate Content", "⏳ History Log"])

# TAB 1: GENERATE CONTENT
with tab_generate:
    col_input, col_output = st.columns([1, 1], gap="large")
    
    with col_input:
        st.subheader("Generation Parameters")
        
        content_type = st.selectbox(
            "Target Content Format",
            [
                "Blog",
                "Article",
                "LinkedIn Post",
                "Email",
                "Product Description"
            ]
        )
        
        tone = st.selectbox(
            "Writing Style & Tone",
            [
                "Professional",
                "Technical",
                "Casual",
                "Marketing",
                "Inspirational"
            ]
        )
        
        length = st.slider(
            "Approximate Word Count",
            min_value=100,
            max_value=2500,
            value=800,
            step=100
        )
        
        query = st.text_area(
            "Describe what you want to write",
            height=180,
            placeholder="Describe the topics, keywords, and goals of this content.\nExample: Explain how machine learning is optimizing smart grid electricity routing."
        )
        
        # Generation Button
        generate_btn = st.button("🚀 Generate RAG-Powered Content", use_container_width=True, disabled=not api_key_valid)
        
        if generate_btn:
            if not query.strip():
                st.warning("Please describe the content you wish to write.")
            else:
                if is_kb_empty:
                    st.warning("⚠️ **Knowledge Base is empty.** Generating content using the LLM's generic weights without RAG reference documentation.")
                
                with st.spinner("Analyzing context and generating draft..."):
                    try:
                        response, sources = generate_content(
                            query=query,
                            content_type=content_type,
                            tone=tone,
                            length=length,
                            model_name=model_name,
                            temperature=temperature
                        )
                        
                        # Serialize retrieved source files/chunks
                        serialized_sources = [
                            {
                                "content": doc.page_content,
                                "source": doc.metadata.get("source", "Unknown Reference")
                            } for doc in sources
                        ]
                        
                        # Save record to SQLite history
                        save_generation(
                            query=query,
                            content_type=content_type,
                            tone=tone,
                            length=length,
                            response=response,
                            sources=serialized_sources
                        )
                        
                        # Update session state to persist
                        st.session_state.generated_content = response
                        st.session_state.sources = serialized_sources
                        st.success("Draft created successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Generation error: {e}")
                        
    with col_output:
        st.subheader("Generated Output workspace")
        
        if st.session_state.generated_content:
            # Word Count stats
            text = st.session_state.generated_content
            words = len(text.split())
            chars = len(text)
            read_time = max(1, round(words / 200))
            
            st.markdown(
                f"<div style='margin-bottom:1rem;'>"
                f"<span class='stat-badge'>📝 {words} Words</span>"
                f"<span class='stat-badge'>🔤 {chars} Characters</span>"
                f"<span class='stat-badge'>⏱️ {read_time} Min Read</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            # Formatted Markdown Display
            st.markdown(
                f"<div class='premium-card' style='max-height: 500px; overflow-y: auto;'>\n\n"
                f"{st.session_state.generated_content}\n\n"
                f"</div>", 
                unsafe_allow_html=True
            )
            
            # Export controls
            st.download_button(
                label="📥 Download Generated Markdown",
                data=st.session_state.generated_content,
                file_name=f"contentforge_{content_type.lower().replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            # Render Retrieval Context sources
            if st.session_state.sources:
                with st.expander("🔍 Retracted RAG Reference Chunks"):
                    for idx, src in enumerate(st.session_state.sources, start=1):
                        source_filename = os.path.basename(src['source'])
                        st.markdown(f"**Source Chunk {idx}:** `{source_filename}`")
                        st.info(src['content'])
        else:
            st.info("Your generated document will appear here after clicking generation.")

# TAB 2: HISTORY LOG
with tab_history:
    st.subheader("Past Generations Archive")
    
    # Load history data
    history_records = get_history()
    
    if not history_records:
        st.info("No past generations found in database.")
    else:
        # Layout container for history item details
        col_list, col_view = st.columns([1, 1.2], gap="large")
        
        with col_list:
            st.markdown("### Generated Items list")
            
            # Clear all history
            if st.button("🗑️ Clear Entire History", type="secondary"):
                clear_history()
                st.session_state.view_history_item = None
                st.success("History database cleared.")
                st.rerun()
                
            st.divider()
            
            # Render items in list format
            for record in history_records:
                # Custom box style for item list entry
                with st.container():
                    st.markdown(
                        f"**{record['content_type']}** ({record['tone']}) — *{record['timestamp']}*\n"
                        f"Prompt: *\"{record['query'][:60]}...\"*"
                    )
                    
                    btn_col1, btn_col2 = st.columns([1, 1])
                    
                    if btn_col1.button("👁️ View Draft", key=f"view_{record['id']}"):
                        st.session_state.view_history_item = record
                        st.rerun()
                        
                    if btn_col2.button("🗑️ Delete", key=f"del_{record['id']}"):
                        delete_history_item(record["id"])
                        if st.session_state.view_history_item and st.session_state.view_history_item["id"] == record["id"]:
                            st.session_state.view_history_item = None
                        st.success(f"Deleted draft ID {record['id']}")
                        st.rerun()
                        
                    st.markdown("<hr style='margin: 0.5rem 0;' />", unsafe_allow_html=True)
                    
        with col_view:
            st.markdown("### Preview Workspace")
            selected = st.session_state.view_history_item
            
            if selected:
                # Render metadata
                hist_words = len(selected['response'].split())
                hist_chars = len(selected['response'])
                hist_read_time = max(1, round(hist_words / 200))
                
                st.markdown(
                    f"**Prompt:** *{selected['query']}*\n\n"
                    f"<span class='stat-badge'>🕒 Generated: {selected['timestamp']}</span>"
                    f"<span class='stat-badge'>📝 {hist_words} Words</span>",
                    unsafe_allow_html=True
                )
                
                st.markdown(
                    f"<div class='premium-card' style='max-height: 400px; overflow-y: auto;'>\n\n"
                    f"{selected['response']}\n\n"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                
                # Export options
                st.download_button(
                    label="📥 Download Historical Draft",
                    data=selected['response'],
                    file_name=f"history_content_{selected['content_type'].lower()}.md",
                    mime="text/markdown",
                    key=f"dl_hist_{selected['id']}",
                    use_container_width=True
                )
                
                # Load back to main editor workspace
                if st.button("🔄 Load Back to Main Generation Window", use_container_width=True):
                    st.session_state.generated_content = selected['response']
                    st.session_state.sources = selected['sources']
                    st.success("Draft loaded into the generator output workspace! Switch to the 'Generate Content' tab to view it.")
                
                # Show sources
                if selected['sources']:
                    with st.expander("🔍 Chunks Used in Generation"):
                        for idx, src in enumerate(selected['sources'], start=1):
                            filename = os.path.basename(src.get('source', 'Unknown File'))
                            st.markdown(f"**Chunk {idx}:** `{filename}`")
                            st.info(src.get('content', 'No content available'))
            else:
                st.info("Select a draft from the list to preview it here.")