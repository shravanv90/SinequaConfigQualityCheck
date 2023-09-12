import os
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd

# Configure Streamlit page settings
st.set_page_config(
    page_title="Sinequa Config Quality Checker",
    layout="wide",
    initial_sidebar_state="expanded",
)

def element_hash(element):
    # Convert dictionary to a tuple of sorted items
    attrib_tuple = tuple(sorted(element.attrib.items()))
    return hash((element.tag, element.text, attrib_tuple))

@st.cache_resource
def load_xml(filepath):
    try:
        tree = ET.parse(filepath)
        return tree
    except ET.ParseError:
        return None

def validate_forcereindexation(root):
    force_reindex = root.find('ForceReindexation')
    if force_reindex is None or force_reindex.text != 'false':
        return 'FAIL'
    return 'PASS'

def validate_loglevel(root):
    log_level = root.find('./System/LogLevel')
    if log_level is None or log_level.text is None or int(log_level.text) >= 10:
        return 'FAIL'
    return 'PASS'

def validate_index_name(root):
    index_name = root.find('Index')
    if index_name is None or index_name.text is None or not index_name.text.startswith('@'):
        return 'FAIL'
    return 'PASS'

def validate_indexer_name(root):
    indexer_names = [indexer.text for indexer in root.findall('Indexers/Indexer')]
    for name in indexer_names:
        if not name.startswith('@'):
            return 'FAIL'
    return 'PASS'

def run_validations(filepath):
    tree = load_xml(filepath)
    if tree is None:
        return {
            'ForceReindexation': 'ERROR',
            'LogLevel': 'ERROR',
            'IndexName': 'ERROR',
            'IndexerName': 'ERROR'
        }

    root = tree.getroot()
    
    # Run validations
    results = {
        'ForceReindexation': validate_forcereindexation(root),
        'LogLevel': validate_loglevel(root),
        'IndexName': validate_index_name(root),
        'IndexerName': validate_indexer_name(root)
    }

    return results

def validate_folder(folderpath):
    results = []

    for root, subfolders, files in os.walk(folderpath):
        for file in files:
            if file.endswith('.xml'):
                filepath = os.path.join(root, file)
                file_result = run_validations(filepath)
                results.append([filepath] + list(file_result.values()))

    df = pd.DataFrame(results, columns=['Filepath', 'ForceReindexation', 'LogLevel', 'IndexName', 'IndexerName'])
    return df

def style_table(df):
    """
    Function to apply styles to the dataframe.
    """
    def color_cells(val):
        if val == "FAIL":
            return 'background-color: lightcoral'
        elif val == "PASS":
            return 'background-color: #4CAF50'
        else:
            return ''

    styled = df.style.applymap(color_cells, subset=pd.IndexSlice[:, 'ForceReindexation':'IndexerName']).hide_index()
    
    # Convert styled DF to HTML
    return styled.render()

# Main Application
st.title('Sinequa Config Quality Checker')

st.write("""
This tool validates specific attributes in XML configuration files within the provided folder. 
Enter the folder path and click on the "Validate" button to check for configurations that might need attention.
""")

folderpath = st.text_input('Enter folder path')

if st.button('Validate'):
    with st.spinner('Validating XML files...'):
        result = validate_folder(folderpath)
    
    # Check if the result dataframe is empty or not
    if not result.empty:
        st.write("Validation Results:")
        html_table = style_table(result)
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.success('Validation passed for all XML files!')

# Sidebar details
st.sidebar.title("Validation Details")
st.sidebar.write("""
The tool checks XML files for the following configurations:
- `ForceReindexation` should be 'false'
- System `LogLevel` should be less than 10
- `Index` name should be an alias and start with '@'
- All `Indexers` should be an alias and start with '@'

Each XML file is checked against these rules, and the results are displayed in the main panel.
""")

st.sidebar.header("How to Use")
st.sidebar.write("""
1. Input the folder path containing XML files.
2. Click on the "Validate" button.
3. Review the results in the table.
""")
