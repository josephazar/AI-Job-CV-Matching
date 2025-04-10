import streamlit as st
from query import search_and_filter_candidates  # Import your existing wrapper function
from cv_analysis import cv_analysis_page  # Import your page function
from dotenv import load_dotenv
import os
load_dotenv()

# Sidebar Dropdown Navigation
def main():
    st.sidebar.title("Navigation")
    pages = {
        "Home": home_page,
        "CV Database": cv_analysis_page,  # Your CV analysis page
        "Candidate Filtering": search_and_filter_candidates,  # Candidate filtering system
    }

    # Dropdown to select the page
    selected_page = st.sidebar.selectbox("Go to", list(pages.keys()))

    # Render the selected page
    page_function = pages[selected_page]
    page_function()

# Home page
def home_page():
    st.title("Find best candidates for your job openings demo")

# Entry point for the app
if __name__ == "__main__":
    main()
