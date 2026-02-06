import streamlit as st
import streamlit.components.v1 as components
import re
import requests

# --- Custom Styling ---
st.set_page_config(page_title="Ref to XML", page_icon="🧬", layout="wide")

col1, col2 = st.columns([2, 3])

with col1:
    st.image('TNQTech-Logo_CROPPED.png', width=250)
    
with col2:
    st.markdown(f"""
        <div style='text-align: left; padding-right: 20px;'>
            <h2 style='font-size: 42px; font-weight: 700; color: #1a1a1a; margin-bottom: -30px;'>
                 Reference to XML Tagging Tool 
            </h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border: 4px solid #e0e0e0; margin-bottom: 0px; margin-top: 0px;'>", unsafe_allow_html=True)


st.markdown("""
    <style>
    /* Main Background */
    .main {
        background-color: #f8f9fa;
    }
    /* Code Box Wrap */
    code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
        color: #d63384 !important;
    }
    /* Card Style for Output */
    .output-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.1);
    }
    /* Gradient Title */
    .title-text {
        background: -webkit-linear-gradient(#007bff, #6610f2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 40px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DOI Fetching Function ---
def fetch_doi(title, year=None, journal=None, volume=None, issue=None):
    headers = {"User-Agent": "Streamlit-DOI-Fetcher/1.0 (mailto:admin@example.com)"}
    try:
        query_parts = [title]
        if journal: query_parts.append(journal)
        if volume: query_parts.append(f"vol. {volume}")
        if year: query_parts.append(str(year))
        query = ", ".join(query_parts)

        response = requests.get(
            "https://api.crossref.org/works",
            params={"query.bibliographic": query, "rows": 1},
            headers=headers, timeout=5
        )
        if response.status_code == 200:
            items = response.json().get("message", {}).get("items", [])
            if items and "DOI" in items[0]:
                return items[0]["DOI"]
    except:
        return None
    return None

# --- Logic Functions ---
def format_authors(author_string):
    temp_authors = author_string.replace(' and ', ', ')
    clean_authors = temp_authors.split(',')
    formatted = []        
    for auth in clean_authors:
        auth = auth.strip()
        if not auth or auth.lower() == "and": continue
        parts = auth.split()
        if len(parts) >= 2:
            surname = parts[-1]
            given_parts = parts[:-1]
            given_formatted = [f"{p.replace('.', '').replace('and', '').strip()}." for p in given_parts if p.strip()]
            given = " ".join(given_formatted)
            surname = ''.join(f"&tnqx{ord(c):x};" if ord(c) > 127 else c for c in surname)
            given = ''.join(f"&tnqx{ord(c):x};" if ord(c) > 127 else c for c in given)
            if given:
                formatted.append(f"<string-name><given-names>{given}</given-names> <surname>{surname}</surname></string-name>")
            else:
                formatted.append(f"<string-name><surname>{surname}</surname></string-name>")
    
    if len(formatted) > 2:
        return ", ".join(formatted[:-1]) + ", and " + formatted[-1]
    elif len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    return formatted[0] if formatted else ""

def process_reference(raw_text):
    clean_text = raw_text.replace('\n', ' ').strip()
    
    with_title_pattern = r"^(.*?),\s*[\u201c\"\u2018\'](.*?)\s*[\u201d\"\u2019\'],?\s*([^0-9]+)\s+(\d+)(?:\((\d+)\))?,?\s*([\w\d\-–]+)\s*\((\d{4})\)"
    without_title_pattern = r"^(.*),\s+([^,0-9]+)\s+(\d+)(?:\((\d+)\))?,?\s*([\w\d\-–]+)\s*\((\d{4})\)"
    
    match = re.search(with_title_pattern, clean_text)
    if match:
        authors_raw, title_raw, journal, vol, issue, page, year = match.groups()
        title_clean = title_raw.strip().rstrip(',')
        doi_found = fetch_doi(title_clean, year, journal, vol, issue)
        title_hex = ''.join(f"&tnqx{ord(c):x};" if ord(c) > 127 else c for c in title_clean)
        f_title = f"&tnqx201c;<article-title>{title_hex}</article-title>,&tnqx201d; "
    else:
        match = re.search(without_title_pattern, clean_text)
        if match:
            authors_raw, journal, vol, issue, page, year = match.groups()
            doi_found = fetch_doi(journal, year, journal, vol, issue)
            f_title = "" 
        else:
            return None 

    f_authors = format_authors(authors_raw)
    journal_hex = ''.join(f"&tnqx{ord(c):x};" if ord(c) > 127 else c for c in journal)
    issue_part = f"(<issue>{issue}</issue>)" if issue else ""
    doi_part = f'<pub-id pub-id-type="doi" specific-use="metadata">{doi_found}</pub-id>' if doi_found else ""
    
    if '-' in page or '–' in page:
        p_parts = re.split(r'[-–]', page)
        page_xml = f"<fpage>{p_parts[0]}</fpage>&tnqx2013;<lpage>{p_parts[1]}</lpage>"
    else:
        page_xml = f"<fpage>{page}</fpage>"

    return (
        f"<tnqref>{f_authors}, {f_title}"
        f"<source>{journal_hex.strip()}</source> "
        f"<volume>{vol}</volume>{issue_part}, "
        f"{page_xml} (<year>{year}</year>).</tnqref>{doi_part}"
    )



# --- Main UI ---

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📥 Input Reference")
    input_text = st.text_area(
        "Paste your raw reference here:", 
        height=250, 
        placeholder='e.g., M. Sjödin, T. Irebo, J. Am. Chem. Soc. 128(40), 13076 (2006).',
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        process_btn = st.button("🚀 Convert to XML", use_container_width=True, type="primary")
    with btn_col2:
        # Clear button logic (Refreshes the app)
        if st.button("🗑️ Clear All", use_container_width=True):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### 📤 XML Output")
    if process_btn and input_text:
        with st.spinner('Processing reference...'):
            output = process_reference(input_text)
            
            if output:
                st.code(output, language="xml")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.success("✨ Conversion Successful!")

                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    copy_js = f"""
                    <button id="copyBtn" onclick="copyFunc()" style="
                        width: 100%; height: 45px; background-color: #28a745; color: white;
                        border: none; border-radius: 8px; cursor: pointer; font-weight: bold;
                        font-size: 16px; transition: 0.3s;
                    ">📋 Copy XML</button>
                    <textarea id="val" style="display:none;">{output}</textarea>
                    
                    <script>
                    function copyFunc() {{
                        var copyText = document.getElementById("val");
                        var btn = document.getElementById("copyBtn");
                        
                        navigator.clipboard.writeText(copyText.value).then(function() {{
                            btn.innerText = "✅ Copied!";
                            btn.style.backgroundColor = "#1e7e34";
                            
                            setTimeout(function() {{
                                btn.innerText = "📋 Copy XML";
                                btn.style.backgroundColor = "#28a745";
                            }}, 2000);
                        }});
                    }}
                    </script>
                    """
                    components.html(copy_js, height=60)

                with action_col2:
                    # Professional Download Button
                    st.download_button(
                        label="💾 Download File",
                        data=output,
                        file_name="tagged_reference.xml",
                        mime="application/xml",
                        use_container_width=True
                    )
            else:
                st.error("❌ Regex match failed. Please check the reference format.")
                st.info("💡 Hint: Ensure Journal name and Volume(Issue) are clearly separated.")
                
    elif not input_text and process_btn:
        st.warning("⚠️ Please enter a reference first.")
    else:
        # Empty State
        st.markdown("""
            <div style="text-align: center; padding: 50px; border: 2px dashed #d1d3d4; border-radius: 15px; color: #a0a0a0;">
                <p style="font-size: 50px;">📄</p>
                <p>XML output will appear here once converted.</p>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<hr style='border: 4px solid #e0e0e0; margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: center;' class='header-footer'>
        <p style='font-weight: normal; font-size: 17px;' color: #5d6d7e;>©2026 TNQTech. All rights reserved.</p>
        <p style='font-weight: normal; font-size: 17px;' color: #5d6d7e;>🛠️ Developed By Logesh kumar K and Marimuthu S</p>
    </div>
    """, unsafe_allow_html=True)