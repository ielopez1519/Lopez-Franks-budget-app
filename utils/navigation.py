import streamlit as st

def safe_rerun():
    """
    Safely rerun the Streamlit app using the best available method.
    - st.rerun() works on newer Streamlit versions.
    - st.experimental_rerun() works on older versions.
    """
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()
