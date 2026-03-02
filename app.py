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
        # แก้ไขจุดนี้: เปลี่ยนจาก json.loads เป็น dict() เพื่อรับค่าจาก Streamlit Secrets โดยตรง
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # ตรวจสอบว่าชื่อไฟล์ใน Google Sheets ของคุณชื่อ "Teloneer Sign Tracker" ตรงกันเป๊ะๆ
        sheet = client.open("Teloneer Sign Tracker").sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        # แสดง Error ที่ชัดเจนขึ้นหากยังติดปัญหา
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("ไม่มีข้อมูลในระบบ หรือกำลังรอการเชื่อมต่อ...")
else:
    # ส่วนการแสดงผลเดิมของคุณ
    total = len(df)
    # ตรวจสอบว่ามีคอลัมน์ชื่อ 'status' ใน Google Sheets หรือไม่
    status_col = "status" if "status" in df.columns else df.columns[0]
    
    pending = len(df[df[status_col] == "รอเซ็น"])
    completed = len(df[df[status_col] == "เซ็นแล้ว"])

    col1, col2, col3 = st.columns(3)
    col1.metric("📄 เอกสารทั้งหมด", total)
    col2.metric("⏳ รอเซ็น", pending)
    col3.metric("✅ เซ็นแล้ว", completed)

    st.divider()

    status_filter = st.selectbox("กรองสถานะ", ["ทั้งหมด", "รอเซ็น", "เซ็นแล้ว"])

    if status_filter != "ทั้งหมด":
        df_show = df[df[status_col] == status_filter].copy()
    else:
        df_show = df.copy()

    if "received_date" in df_show.columns:
        def calc_days(row):
            if row[status_col] == "รอเซ็น":
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
        current_status = row.get(status_col, "-")
        status_icon = "⏳" if current_status == "รอเซ็น" else "✅"
        
        with st.expander(f"{status_icon} {row.get('doc_name', 'ไม่มีชื่อเอกสาร')}"):
            c1, c2 = st.columns(2)
            c1.write(f"**ผู้ขอ:** {row.get('requester', '-')}")
            c1.write(f"**วันที่รับ:** {row.get('received_date', '-')}")
            c2.write(f"**สถานะ:** {current_status}")
            
            if current_status == "รอเซ็น":
                c2.write(f"**รอนานแล้ว:** {row.get('รอนานแล้ว', '-')}")
            else:
                c2.write(f"**วันที่เซ็น:** {row.get('completed_date', '-')}")
                
            if row.get("sign_link"):
                st.link_button("✍️ คลิกเซ็นเอกสาร", row["sign_link"])

    st.divider()

    st.subheader("📊 สรุปตามผู้ขอ")
    if "requester" in df.columns:
        summary = df.groupby("requester")[status_col].value_counts().unstack(fill_value=0)
        st.dataframe(summary, use_container_width=True)

st.caption("อัพเดทข้อมูลทุก 60 วินาที | Teloneer Company Limited")
