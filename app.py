import streamlit as st

# Initialize session state tracking variables if they don't exist
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "master_password" not in st.session_state:
    st.session_state.master_password = ""

# Define the logical application routing pages
login_page = st.Page("views/login.py", title="Authentication Portal", default=not st.session_state.authenticated)
dashboard_page = st.Page("views/dashboard.py", title="Administrative Vault", default=st.session_state.authenticated)

# Handle dynamic system routing
if st.session_state.authenticated:
    pg = st.navigation([dashboard_page])
else:
    pg = st.navigation([login_page])

pg.run()