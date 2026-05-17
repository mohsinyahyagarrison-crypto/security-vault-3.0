import streamlit as st

st.set_page_config(page_title="CryptVault Login", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #0d1117; }
    h1, h2, p, label, span { color: #c9d1d9 !important; }
    div.stButton > button:first-child {
        background-color: #238636; color: white; border: none; width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #2ea043; border: none;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("ADMIN CONTROL ACCESS")
st.write("Provide authorization key details below to initialize local safe parameters.")

password_attempt = st.text_input("Master Password Profile Key", type="password")

if st.button("Authorize Session"):
    if password_attempt.strip() != "":
        st.session_state.authenticated = True
        st.session_state.master_password = password_attempt
        st.success("Authorization verified successfully. Access granted.")
        st.rerun()
    else:
        st.error("Key parameters cannot be left blank.")