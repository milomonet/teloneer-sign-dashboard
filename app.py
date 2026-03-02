import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json

st.set_page_config(
    page_title="Teloneer Sign Tracker",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Teloneer Sign Tracker")
st.markdown("ติดตามสถานะเอกสารรอเซ็น")

@st.cache_data(ttl=60)
def load_data():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = json.loads(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Teloneer Sign Tracker").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("ไม่มีข้อมูลในระบบ")
else:
    total = len(df)
    pending = len(df[df["status"] == "รอเซ็น"])
    completed = len(df[df["status"] == "เซ็นแล้ว"])

    col1, col2, col3 = st.columns(3)
    col1.metric("📄 เอกสารทั้งหมด", total)
    col2.metric("⏳ รอเซ็น", pending)
    col3.metric("✅ เซ็นแล้ว", completed)

    st.divider()

    status_filter = st.selectbox("กรองสถานะ", ["ทั้งหมด", "รอเซ็น", "เซ็นแล้ว"])

    if status_filter != "ทั้งหมด":
        df_show = df[df["status"] == status_filter].copy()
    else:
        df_show = df.copy()

    if "received_date" in df_show.columns:
        def calc_days(row):
            if row["status"] == "รอเซ็น":
                try:
                    received = pd.to_datetime(row["received_date"], dayfirst=False)
                    delta = datetime.now() - received
                    return f"{delta.days} วัน"
                except:
                    return "-"
            return "-"
        df_show["รอนานแล้ว"] = df_show.apply(calc_days, axis=1)

    st.subheader(f"รายการเอกสาร ({len(df_show)} รายการ)")

    for _, row in df_show.iterrows():
        status_icon = "⏳" if row["status"] == "รอเซ็น" else "✅"
        with st.expander(f"{status_icon} {row.get('doc_name', '-')}"):
            c1, c2 = st.columns(2)
            c1.write(f"**ผู้ขอ:** {row.get('requester', '-')}")
            c1.write(f"**วันที่รับ:** {row.get('received_date', '-')}")
            c2.write(f"**สถานะ:** {row.get('status', '-')}")
            if row["status"] == "รอเซ็น":
                c2.write(f"**รอนานแล้ว:** {row.get('รอนานแล้ว', '-')}")
            else:
                c2.write(f"**วันที่เซ็น:** {row.get('completed_date', '-')}")
            if row.get("sign_link"):
                st.link_button("✍️ คลิกเซ็นเอกสาร", row["sign_link"])

    st.divider()

    st.subheader("📊 สรุปตามผู้ขอ")
    if "requester" in df.columns:
        summary = df.groupby("requester")["status"].value_counts().unstack(fill_value=0)
        st.dataframe(summary, use_container_width=True)

st.caption("อัพเดทข้อมูลทุก 60 วินาที | Teloneer Company Limited")
