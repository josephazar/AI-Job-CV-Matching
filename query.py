import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import json  # Import JSON module for deserialization
from skill_matching import extract_job_information
from fuzzywuzzy import fuzz
from hard_requirements import filter_by_hard_requirements
import pandas as pd
import os
from dotenv import load_dotenv
import re
# Load environment variables from the .env file
load_dotenv()

# Azure Search service credentials
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = "resumes-index"

# Initialize the SearchClient
search_client = SearchClient(
    endpoint=search_endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(search_api_key)
)

def search_index(search_text, search_fields=None, top=10):
    try:
        results = search_client.search(search_text=search_text, search_fields=search_fields, top=top)
        return [result for result in results]
    except Exception as e:
        st.error(f"An error occurred while querying the index: {e}")
        return []
def match_skills(job_skills, skills2, threshold=50):
    matches = []
    matched_skills = set()  # Track already matched skills to avoid duplicates

    # Normalize and clean skills lists
    def clean_and_tokenize(skills):
        cleaned_skills = []
        for skill in skills:
            # Remove leading/trailing whitespace and convert to lowercase
            cleaned_skill = skill.lower().strip()
            cleaned_skills.append(cleaned_skill)
        return cleaned_skills

    # Preprocess job skills and skills to match against
    job_skills = clean_and_tokenize(job_skills)
    skills2 = clean_and_tokenize(skills2)

    # Debugging: Print the cleaned and tokenized skill lists
    print(f"Job Skills (cleaned): {job_skills}")
    print(f"Skills2 (cleaned): {skills2}")

    for skill in job_skills:
        for req_skill in skills2:
            # Use fuzzy matching for comparison
            score = fuzz.ratio(skill, req_skill)

            # Debugging: Print comparison details
            print(f"Comparing: '{skill}' vs '{req_skill}', Score: {score}")

            if score >= threshold and req_skill not in matched_skills:
                matches.append({"matched_skill": req_skill})
                matched_skills.add(req_skill)  # Add to the matched set

    # Debugging: Print final matches
    print(f"Matched Skills: {matches}")

    return matches



def filter_matching_results(query_results, extracted_skills, job_skills, threshold=70):
    matching_results = []
    
    # Debugging job_skills
    print(f"Job Skills: {job_skills}")
    
    for result in query_results:
        result_skills = []
        if "skills" in result:
            try:
                # Parse skills field if it's a JSON string
                result_skills = json.loads(result["skills"])
            except json.JSONDecodeError:
                continue  # Skip this result if skills parsing fails

        # Debugging result_skills
        print(f"Result Skills: {result_skills}")
        
        # Find matches for job skills in the current result's skills
        matches = match_skills(job_skills, result_skills, threshold=threshold)

        if matches:  # If there's at least one match, include this result
            result["matching_skills"] = matches
            matching_results.append(result)
    
    return matching_results


def fix_skill_format(extracted_skills):
    """
    Detects and fixes job skills extracted with individual letters separated by commas,
    merging them back into full words.
    """
    fixed_skills = []

    for skill in extracted_skills:
        # If the skill is just letters separated by commas, merge them
        if len(skill) > 1 and ',' in skill:
            # Merge the letters into a single word
            merged_skill = ''.join(skill.split(',')).replace(" ", "")
            fixed_skills.append(merged_skill)
        else:
            # If the skill is already a word (not separated by commas), add it as is
            fixed_skills.append(skill)

    # Remove duplicates and return
    print(list(set(fixed_skills)))
    return list(set(fixed_skills))



def search_and_filter_candidates():
    """Main wrapper function for the candidate filtering system."""
    st.title("Candidate Filtering System")
    job_desc = """
We are seeking a passionate and motivated Entry-Level Front-End Developer to join our growing team. As a Front-End Developer, you will work closely with senior developers, designers, and product managers to help build user-friendly, responsive, and dynamic websites and applications. This is a great opportunity for someone looking to kick-start their career in web development.

Responsibilities:
Assist in the development and maintenance of the front-end of websites and web applications.
Write clean, well-documented, and reusable code in HTML, CSS, and JavaScript.
Collaborate with UI/UX designers to implement and optimize design and user interfaces.
Ensure responsiveness and cross-browser compatibility of websites.
Troubleshoot and debug issues related to front-end performance.
Integrate APIs and third-party libraries to enhance functionality.
Optimize web applications for speed and performance.
Stay up-to-date with the latest web development trends, techniques, and best practices.
Qualifications:
Basic understanding of HTML, CSS, and JavaScript.
Familiarity with modern front-end frameworks (e.g., React, Vue.js, Angular) is a plus.
Experience with version control tools like Git.
Strong problem-solving skills and attention to detail.
Ability to work in a collaborative team environment.
Strong communication skills and a desire to learn.
Knowledge of web development tools such as code editors (e.g., VSCode), browser developer tools, etc.
A portfolio or examples of past work is a plus (e.g., personal projects, GitHub repositories).
Preferred Skills:
Experience with CSS preprocessors (SASS, LESS).
Knowledge of responsive design techniques.
Familiarity with front-end build tools like Webpack or Gulp.
Basic understanding of web accessibility principles.
Exposure to Agile development methodologies.
Education:
Bachelor’s degree in Computer Science, Web Development, or a related field, or equivalent practical experience.
"""
    st.markdown("#### Sample Job Description:")
    st.markdown(job_desc)
    # Job description input (search query)
    job_description = st.text_area("Enter the job description:", placeholder="Paste the job description here...")


    # Filter options for search fields
    with st.expander("Advanced Search Fields (Optional)"):
        skill_search = st.text_input("Search in skills:", placeholder="e.g., Python")
        education_search = st.text_input("Search in education:", placeholder="e.g., Computer Science")

    # Construct list of fields to search
    search_fields = []
    if skill_search:
        search_fields.append("skills")
    if education_search:
        search_fields.append("education")

    # Results limit
    top_n = st.slider("Number of results to return:", min_value=1, max_value=50, value=10)

    if st.button("Search"):
        if job_description.strip():  # Ensure the job description is not empty
            with st.spinner("Searching..."):
                # Perform the search using job description as the query
                results = search_index(
                    search_text=job_description,
                    search_fields=",".join(search_fields) if search_fields else None,
                    top=top_n,
                )
                st.session_state.results = results  # Store results in session state

            if st.session_state.results:
                st.subheader("Pre-Filtered Search Results")

                # Dynamically convert the results to a pandas DataFrame
                df = pd.json_normalize(st.session_state.results)
                df = reorder_and_clean_df(df)
                st.write(df)

                # Extracted skills from the combined query results (job description)
                extracted_skills = []
                for result in st.session_state.results:
                    if "skills" in result:
                        try:
                            skills = json.loads(result["skills"])  # Parse JSON string
                            extracted_skills.extend(skills)
                        except json.JSONDecodeError:
                            st.error(f"Failed to parse skills for result: {result}")

                # Fix extracted skills by merging letters into words
                extracted_skills = fix_skill_format(extracted_skills)

                # Remove duplicate skills
                extracted_skills = list(set(extracted_skills))

                # Display extracted skills
                if extracted_skills:
                    st.subheader("Extracted Skills from Results")
                else:
                    st.warning("No skills found in the query results.")

                # Extract job skills from the provided job description
                with st.spinner("Extracting job information..."):
                    try:
                        job_info = extract_job_information(job_description)
                    except Exception as e:
                        st.error(f"Error extracting job information: {e}")
                        job_info = None

                if job_info and "Skills" in job_info:
                    st.write(job_info)
                    job_skills = job_info["Skills"]
                    job_skills = fix_skill_format(job_skills)
                    st.write(f"Job skills: {', '.join(job_skills)}")

                    with st.spinner("Filtering results by matching skills..."):
                        filtered_results = filter_matching_results(
                            st.session_state.results, extracted_skills, job_skills
                        )
                        st.session_state.filtered_results = filtered_results

                    st.subheader("Filtered Matching Results (Based on Skills)")
                    if st.session_state.filtered_results:
                        df_filtered = pd.json_normalize(st.session_state.filtered_results)
                        df_filtered = reorder_and_clean_df(df_filtered)
                        st.write(df_filtered)
                    else:
                        st.warning("No matching results found based on skills.")
                else:
                    st.error("Failed to extract or match job skills.")
            else:
                st.warning("No results found for the given job description.")
        else:
            st.warning("Please enter a job description to search.")

    if "filtered_results" not in st.session_state:
        st.session_state.filtered_results = []

    if st.session_state.filtered_results:
        st.subheader("Filter by Hard Requirements")
        hard_requirements_input = st.text_area(
            "Enter hard requirements (comma-separated):",
            placeholder="e.g., 5 years of experience, Python, AWS certification"
        )

        if st.button("Apply Hard Requirements"):
            hard_requirements = [req.strip() for req in hard_requirements_input.split(",")]
            if hard_requirements:
                with st.spinner("Applying hard requirements..."):
                    final_results = filter_by_hard_requirements(
                        st.session_state.filtered_results, hard_requirements
                    )

                st.subheader("Final Results After Hard Requirements")
                if final_results:
                    df_final = pd.json_normalize(final_results)
                    df_final = reorder_and_clean_df(df_final)
                    st.dataframe(df_final)
                else:
                    st.warning("No results matched the hard requirements.")
            else:
                st.warning("Please enter hard requirements to filter the results.")

def reorder_and_clean_df(df):
    """Reorder the DataFrame to start with 'filename' column and drop empty columns."""
    if 'filename' in df.columns:
        cols = ['filename'] + [col for col in df.columns if col != 'filename']
        df = df[cols]
    # Convert any list or dict columns to readable strings
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, indent=2) if isinstance(x, (list, dict)) else x)
    df = df.dropna(axis=1, how='all')  # Drop columns with all NaN values
    return df
