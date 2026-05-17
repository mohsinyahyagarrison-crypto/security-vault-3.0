import streamlit as st
import sqlite3
import base64
import os
import pandas as pd
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

st.set_page_config(page_title="CryptVault Management Panel", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0d1117; }
    h1, h2, h3, p, label, span { color: #c9d1d9 !important; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    div.stButton > button:first-child {
        background-color: #238636; color: white; border: none;
    }
    div.stButton > button:first-child:hover {
        background-color: #2ea043; border: none;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Cryptographic Key Derivation Engine
# ---------------------------------------------------------
SALT_FILE = "vault.salt"


def get_or_create_salt():
    if not os.path.exists(SALT_FILE):
        salt = os.urandom(16)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
        return salt
    with open(SALT_FILE, "rb") as f:
        return f.read()


def derive_secure_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


# Guard rails: Force exit back to login if direct routing is attempted without authentication
if not st.session_state.get("authenticated", False):
    st.warning("Session parameters invalid. Redirecting to access terminal.")
    st.session_state.authenticated = False
    st.rerun()

# Setup database parameters
salt = get_or_create_salt()
conn = sqlite3.connect('vault.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        label TEXT NOT NULL, 
        encrypted_content BLOB NOT NULL
    )
''')
conn.commit()

# Derive master session token using state variable passed securely across screens
derived_key = derive_secure_key(st.session_state.master_password, salt)
cipher = Fernet(derived_key)

# ---------------------------------------------------------
# UI Layout Navigation Shell
# ---------------------------------------------------------
st.title("ADMIN CYBER-VAULT")
st.caption("CryptVault Secure Database & Asset Control panel")

# Sidebar navigation options and session management
menu = ["View Vault", "Add Secret", "Delete Secret", "Backup & Maintenance"]
choice = st.sidebar.selectbox("Navigation Options", menu)

if st.sidebar.button("Terminate Session (Logout)"):
    st.session_state.authenticated = False
    st.session_state.master_password = ""
    st.rerun()

# ---------------------------------------------------------
# Navigation Operations Logic
# ---------------------------------------------------------
if choice == "View Vault":
    st.subheader("Current Encrypted Assets")
    data = pd.read_sql_query("SELECT * FROM secrets", conn)

    if not data.empty:
        decrypted_list = []
        for _, row in data.iterrows():
            try:
                decrypted_val = cipher.decrypt(row['encrypted_content']).decode()
                decrypted_list.append({"ID": row['id'], "Asset Label": row['label'], "Secret Content": decrypted_val})
            except Exception:
                decrypted_list.append({"ID": row['id'], "Asset Label": row['label'],
                                       "Secret Content": "DECRYPTION FAILURE (Invalid Key)"})

        st.dataframe(pd.DataFrame(decrypted_list), use_container_width=True)
    else:
        st.info("The vault database is currently empty.")

elif choice == "Add Secret":
    st.subheader("Store New Secure Asset")
    asset_label = st.text_input("Asset Label / Application Name", placeholder="e.g., GitHub OAuth Token")
    asset_value = st.text_input("Secret Value", type="password", placeholder="Enter sensitive string")

    if st.button("Encrypt & Commit to DB"):
        if asset_label and asset_value:
            encrypted_text = cipher.encrypt(asset_value.encode())
            c.execute('INSERT INTO secrets (label, encrypted_content) VALUES (?,?)', (asset_label, encrypted_text))
            conn.commit()
            st.success(f"Successfully encrypted and locked configuration for '{asset_label}'.")
        else:
            st.error("Fields cannot be left blank.")

elif choice == "Delete Secret":
    st.subheader("Revoke & Delete Asset")
    data = pd.read_sql_query("SELECT id, label FROM secrets", conn)

    if not data.empty:
        st.dataframe(data, use_container_width=True)
        delete_id = st.number_input("Target Record ID to Wipe", min_value=1, step=1)

        if st.button("Permanently Purge Record"):
            c.execute('DELETE FROM secrets WHERE id=?', (delete_id,))
            conn.commit()
            st.warning(f"Record ID {delete_id} dropped from physical database tables.")
            st.rerun()
    else:
        st.info("No records available to delete.")

elif choice == "Backup & Maintenance":
    st.subheader("Core Data Archival")

    with open("vault.db", "rb") as db_file:
        st.download_button(
            label="Download Encrypted vault.db File",
            data=db_file,
            file_name="vault_backup.db",
            mime="application/octet-stream"
        )

    with open(SALT_FILE, "rb") as salt_file:
        st.download_button(
            label="Download Cryptographic vault.salt File",
            data=salt_file,
            file_name="vault.salt",
            mime="application/octet-stream"
        )
    st.caption(
        "Warning Note: To restore backups on a different machine, you need BOTH the vault database file and the specific .salt file generated during creation.")