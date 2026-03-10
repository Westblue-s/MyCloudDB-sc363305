import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime

# ==========================================
# Database Connection & Helpers
# ==========================================
def get_connection():
    return mysql.connector.connect(
        host=st.secrets["sc363305-project-personal-finance-system-oncloud.l.aivencloud.com"],
        user=st.secrets["avnadmin"],
        password=st.secrets["AVNS_nLVmRdG1OMPt3_aYHP3"],
        database=st.secrets["defaultdb"],
        port=st.secrets["17738"]
    ) 

def generate_id(table, prefix, col):
    try:
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute(f"SELECT {col} FROM {table} ORDER BY {col} DESC LIMIT 1")
        res = cursor.fetchone(); conn.close()
        return f"{prefix}{int(res[0][len(prefix):]) + 1:03d}" if res else f"{prefix}001"
    except: return f"{prefix}001"

def load_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.set_page_config(page_title="Personal Finance Pro", layout="wide")
st.title("💎 Personal Finance System (Perfect Version)")

# โหลด Dropdown Data
df_u = load_data("SELECT UserID, FirstName FROM Users")
df_w = load_data("SELECT WalletID, WalletName FROM Wallets")
df_c = load_data("SELECT CategoryID, CategoryName, TransactionType FROM Categories")
df_g = load_data("SELECT GoalID, GoalName, UserID FROM SavingGoals")

dict_u = {f"{r['FirstName']} ({r['UserID']})": r['UserID'] for _, r in df_u.iterrows()}
dict_w = {f"{r['WalletName']}": r['WalletID'] for _, r in df_w.iterrows()}
dict_c = {f"{r['CategoryName']} [{r['TransactionType']}]": r['CategoryID'] for _, r in df_c.iterrows()}

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["👤 1. ผู้ใช้งาน", "💸 2. รับ-จ่าย", "🎯 3. เป้าหมาย & งบประมาณ", "📊 4. แดชบอร์ดอัจฉริยะ", "⚙️ 5. จัดการข้อมูล", "🔍 6. ค้นหา & กรองข้อมูล"])

# ==========================================
# แท็บ 1: ผู้ใช้งาน
# ==========================================
with tab1:
    st.header("👤 เพิ่มผู้ใช้งานใหม่")
    next_u = generate_id("Users", "USR", "UserID")
    with st.form("u_form"):
        c1, c2, c3 = st.columns(3)
        fn = c1.text_input("ชื่อจริง"); ln = c2.text_input("นามสกุล"); em = c3.text_input("อีเมล")
        if st.form_submit_button("บันทึกผู้ใช้"):
            conn = get_connection(); cursor = conn.cursor()
            cursor.execute("INSERT INTO Users (UserID, FirstName, LastName, Email) VALUES (%s,%s,%s,%s)", (next_u, fn, ln, em))
            conn.commit(); conn.close(); st.success("เพิ่มผู้ใช้สำเร็จ!"); st.rerun()

# ==========================================
# แท็บ 2: รับ-จ่าย (Transactions)
# ==========================================
with tab2:
    st.header("📝 บันทึกรายการ (Income / Expense)")
    next_tx = generate_id("Transactions", "SM", "TransactionID")
    with st.form("tx_form"):
        c1, c2 = st.columns(2)
        with c1:
            u_id = st.selectbox("ผู้ใช้งาน", options=dict_u.keys() if dict_u else ["-"])
            w_id = st.selectbox("ช่องทาง (เงินสด/ธนาคาร)", options=dict_w.keys())
            c_id = st.selectbox("หมวดหมู่", options=dict_c.keys())
        with c2:
            amt = st.number_input("จำนวนเงิน", min_value=1.0)
            date = st.date_input("วันที่")
            note = st.text_input("บันทึกช่วยจำ")
        if st.form_submit_button("บันทึกธุรกรรม"):
            if dict_u:
                conn = get_connection(); cursor = conn.cursor()
                cursor.execute("INSERT INTO Transactions VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())", (next_tx, dict_u[u_id], dict_w[w_id], dict_c[c_id], amt, date, note))
                conn.commit(); conn.close(); st.success("บันทึกเรียบร้อย!")

# ==========================================
# แท็บ 3: เป้าหมาย & งบประมาณ (Goals & Budgets)
# ==========================================
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.header("🎯 ตั้งเป้าหมายออมเงิน")
        with st.form("goal_form"):
            gu_id = st.selectbox("ผู้ใช้งาน", options=dict_u.keys() if dict_u else ["-"], key="g1")
            g_name = st.text_input("ชื่อเป้าหมาย")
            g_amt = st.number_input("ยอดที่ต้องการ", min_value=100.0)
            g_date = st.date_input("วันสิ้นสุด")
            if st.form_submit_button("สร้างเป้าหมาย"):
                next_g = generate_id("SavingGoals", "GOL", "GoalID")
                conn = get_connection(); cursor = conn.cursor()
                cursor.execute("INSERT INTO SavingGoals VALUES (%s,%s,%s,%s,%s,NOW(),NOW())", (next_g, dict_u[gu_id], g_name, g_amt, g_date))
                conn.commit(); conn.close(); st.success("สำเร็จ!"); st.rerun()
                
        st.subheader("💰 หยอดกระปุก (Contributions)")
        dict_g = {f"{r['GoalName']} ({r['GoalID']})": r['GoalID'] for _, r in df_g.iterrows()}
        with st.form("contribute_form"):
            cg_id = st.selectbox("เลือกเป้าหมาย", options=dict_g.keys() if dict_g else ["-"])
            cw_id = st.selectbox("หักเงินจากกระเป๋า", options=dict_w.keys())
            c_amt = st.number_input("ยอดเงินหยอดกระปุก", min_value=1.0)
            if st.form_submit_button("หยอดกระปุก"):
                if dict_g:
                    next_con = generate_id("GoalContributions", "CON", "ContributionID")
                    conn = get_connection(); cursor = conn.cursor()
                    cursor.execute("INSERT INTO GoalContributions VALUES (%s,%s,%s,%s,NOW(),NOW())", (next_con, dict_g[cg_id], dict_w[cw_id], c_amt))
                    conn.commit(); conn.close(); st.success("หยอดกระปุกสำเร็จ!")

    with c2:
        st.header("📊 ตั้งงบประมาณรายจ่าย")
        with st.form("budget_form"):
            bu_id = st.selectbox("ผู้ใช้งาน", options=dict_u.keys() if dict_u else ["-"], key="b1")
            bc_id = st.selectbox("หมวดหมู่ที่คุมงบ", options=[k for k in dict_c.keys() if "Expense" in k]) # เลือกเฉพาะรายจ่าย
            b_amt = st.number_input("งบประมาณที่ตั้งไว้", min_value=100.0)
            b_m = st.number_input("เดือน (1-12)", 1, 12, datetime.now().month)
            b_y = st.number_input("ปี", 2024, 2030, datetime.now().year)
            if st.form_submit_button("บันทึกงบ"):
                next_b = generate_id("Budgets", "BGT", "BudgetID")
                conn = get_connection(); cursor = conn.cursor()
                cursor.execute("INSERT INTO Budgets VALUES (%s,%s,%s,%s,%s,%s,NOW(),NOW())", (next_b, dict_u[bu_id], dict_c[bc_id], b_amt, b_m, b_y))
                conn.commit(); conn.close(); st.success("สำเร็จ!")

# ==========================================
# แท็บ 4: แดชบอร์ดอัจฉริยะ (The Perfect Dashboard)
# ==========================================
with tab4:
    st.header("📈 แดชบอร์ดสรุปผลอัจฉริยะ")
    st.write("ระบบคำนวณข้อมูลทั้งหมดแบบ Real-time จากฐานข้อมูล ด้วย Multi-Table JOIN")

    # 1. ยอดเงินคงเหลือแบบไดนามิก (คำนวณจาก Transaction หักลบ Goal Contribution)
    st.subheader("💳 ยอดเงินคงเหลือ (Dynamic Balance)")
    query_bal = """
        SELECT 
            u.FirstName AS 'ผู้ใช้งาน',
            w.WalletName AS 'ช่องทาง',
            IFNULL(SUM(CASE WHEN c.TransactionType = 'Income' THEN t.Amount ELSE -t.Amount END), 0) - 
            IFNULL((SELECT SUM(gc.Amount) FROM GoalContributions gc WHERE gc.WalletID = w.WalletID AND gc.GoalID IN (SELECT GoalID FROM SavingGoals WHERE UserID = u.UserID)), 0) AS 'เงินคงเหลือ (บาท)'
        FROM Wallets w
        CROSS JOIN Users u
        LEFT JOIN Transactions t ON w.WalletID = t.WalletID AND u.UserID = t.UserID
        LEFT JOIN Categories c ON t.CategoryID = c.CategoryID
        GROUP BY u.UserID, w.WalletID;
    """
    df_bal = load_data(query_bal)
    st.dataframe(df_bal, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        # 2. ความคืบหน้าเป้าหมาย
        st.subheader("🎯 ความคืบหน้าการออม (Goal Progress)")
        query_progress = """
            SELECT 
                sg.GoalName AS 'เป้าหมาย',
                sg.TargetAmount AS 'ยอดที่ต้องการ',
                IFNULL(SUM(gc.Amount), 0) AS 'เก็บได้แล้ว',
                (sg.TargetAmount - IFNULL(SUM(gc.Amount), 0)) AS 'ขาดอีก'
            FROM SavingGoals sg
            LEFT JOIN GoalContributions gc ON sg.GoalID = gc.GoalID
            GROUP BY sg.GoalID;
        """
        st.dataframe(load_data(query_progress), use_container_width=True)

    with c2:
        # 3. ตรวจสอบงบประมาณ
        st.subheader("📊 งบประมาณ vs รายจ่ายจริง")
        query_bud = """
            SELECT 
                c.CategoryName AS 'หมวดหมู่',
                b.Amount AS 'งบที่ตั้งไว้',
                IFNULL(SUM(t.Amount), 0) AS 'ใช้จริง',
                (b.Amount - IFNULL(SUM(t.Amount), 0)) AS 'งบเหลือ'
            FROM Budgets b
            JOIN Categories c ON b.CategoryID = c.CategoryID
            LEFT JOIN Transactions t ON b.CategoryID = t.CategoryID AND b.UserID = t.UserID AND b.Month = MONTH(t.TransactionDate)
            GROUP BY b.BudgetID;
        """
        st.dataframe(load_data(query_bud), use_container_width=True)

# ==========================================
# แท็บ 5: จัดการข้อมูล (Update / Delete) - สมบูรณ์แบบครบ CRUD
# ==========================================
with tab5:
    st.header("⚙️ จัดการข้อมูล (แก้ไข / ลบ)")
    st.write("เลือกระบบที่ต้องการจัดการ เพื่อทำการ Update หรือ Delete ข้อมูล")
    
    manage_type = st.radio("เลือกตารางข้อมูล:", ["💸 รายการรับ-จ่าย (Transactions)", "👤 ผู้ใช้งาน (Users)"], horizontal=True)
    st.markdown("---")

    # ----------------------------------------
    # โหมดจัดการ Transactions
    # ----------------------------------------
    if manage_type == "💸 รายการรับ-จ่าย (Transactions)":
        df_tx = load_data("SELECT TransactionID, UserID, WalletID, CategoryID, Amount, TransactionDate, Note, updatedAt FROM Transactions ORDER BY updatedAt DESC")
        st.dataframe(df_tx, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✏️ แก้ไขรายการ (Update)")
            with st.form("edit_tx_form"):
                tx_list = df_tx['TransactionID'].tolist() if not df_tx.empty else ["-"]
                edit_tx_id = st.selectbox("เลือกรหัสรายการที่ต้องการแก้ไข", tx_list)
                
                # ให้แก้เฉพาะฟิลด์ที่มักจะพิมพ์ผิดบ่อยๆ (จำนวนเงิน กับ หมายเหตุ)
                new_amt = st.number_input("จำนวนเงินที่ถูกต้อง", min_value=1.0)
                new_note = st.text_input("บันทึกช่วยจำใหม่")
                
                if st.form_submit_button("อัปเดตข้อมูล"):
                    if edit_tx_id != "-":
                        conn = get_connection(); cursor = conn.cursor()
                        cursor.execute("UPDATE Transactions SET Amount = %s, Note = %s, updatedAt = NOW() WHERE TransactionID = %s", (new_amt, new_note, edit_tx_id))
                        conn.commit(); conn.close()
                        st.success(f"✅ อัปเดตรายการ {edit_tx_id} สำเร็จ!"); st.rerun()

        with c2:
            st.subheader("🗑️ ลบรายการ (Delete)")
            with st.form("del_tx_form"):
                del_tx_id = st.selectbox("เลือกรหัสรายการที่ต้องการลบ", tx_list, key="del_tx")
                st.warning("⚠️ ข้อมูลที่ถูกลบจะไม่สามารถกู้คืนได้")
                
                if st.form_submit_button("ลบข้อมูลทิ้ง"):
                    if del_tx_id != "-":
                        conn = get_connection(); cursor = conn.cursor()
                        cursor.execute("DELETE FROM Transactions WHERE TransactionID = %s", (del_tx_id,))
                        conn.commit(); conn.close()
                        st.error(f"🗑️ ลบรายการ {del_tx_id} สำเร็จ!"); st.rerun()

    # ----------------------------------------
    # โหมดจัดการ Users
    # ----------------------------------------
    elif manage_type == "👤 ผู้ใช้งาน (Users)":
        df_usr = load_data("SELECT UserID, FirstName, LastName, Email, updatedAt FROM Users")
        st.dataframe(df_usr, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✏️ แก้ไขข้อมูลผู้ใช้")
            with st.form("edit_user_form"):
                usr_list = df_usr['UserID'].tolist() if not df_usr.empty else ["-"]
                edit_u_id = st.selectbox("เลือกรหัสผู้ใช้", usr_list)
                
                new_fn = st.text_input("ชื่อจริงใหม่")
                new_ln = st.text_input("นามสกุลใหม่")
                new_em = st.text_input("อีเมลใหม่")
                
                if st.form_submit_button("อัปเดตผู้ใช้"):
                    if edit_u_id != "-":
                        conn = get_connection(); cursor = conn.cursor()
                        cursor.execute("UPDATE Users SET FirstName = %s, LastName = %s, Email = %s, updatedAt = NOW() WHERE UserID = %s", (new_fn, new_ln, new_em, edit_u_id))
                        conn.commit(); conn.close()
                        st.success(f"✅ อัปเดตข้อมูลผู้ใช้ {edit_u_id} สำเร็จ!"); st.rerun()

        with c2:
            st.subheader("🗑️ ลบผู้ใช้งาน")
            with st.form("del_user_form"):
                del_u_id = st.selectbox("เลือกรหัสผู้ใช้ที่ต้องการลบ", usr_list, key="del_usr")
                st.error("🚨 อันตราย! หากลบผู้ใช้ ระบบจะลบรายการรับ-จ่าย, เป้าหมาย, และงบประมาณ ของผู้ใช้นี้ทั้งหมด (Cascade Delete)")
                
                if st.form_submit_button("ยืนยันการลบผู้ใช้"):
                    if del_u_id != "-":
                        conn = get_connection(); cursor = conn.cursor()
                        cursor.execute("DELETE FROM Users WHERE UserID = %s", (del_u_id,))
                        conn.commit(); conn.close()
                        st.error(f"🗑️ ลบผู้ใช้ {del_u_id} และข้อมูลที่เกี่ยวข้องทั้งหมดสำเร็จ!"); st.rerun()

# ==========================================
# แท็บ 6: ค้นหา กรอง และจัดเรียงข้อมูล (Search, WHERE, ORDER BY)
# ==========================================
with tab6:
    st.header("🔍 ค้นหา กรอง และจัดเรียงข้อมูล (Advanced Search)")
    st.write("ระบบดึงข้อมูลจาก Transactions มาทำการกรอง (WHERE), ค้นหา (LIKE) และจัดเรียง (ORDER BY)")
    
    # ----------------------------------------
    # 1. ส่วนของ UI สำหรับรับค่าจากผู้ใช้
    # ----------------------------------------
    c1, c2, c3 = st.columns(3)
    with c1:
        # การค้นหา (Search / LIKE)
        search_note = st.text_input("🔍 ค้นหาจาก 'บันทึกช่วยจำ' (พิมพ์ข้อความบางส่วน)")
        
    with c2:
        # การกรองข้อมูล (Filter / WHERE)
        filter_cat = st.selectbox("📂 กรองตามหมวดหมู่", ["ทั้งหมด"] + list(dict_c.keys()))
        
    with c3:
        # การจัดเรียงข้อมูล (Sort / ORDER BY)
        sort_option = st.selectbox("↕️ จัดเรียงข้อมูล (Order By)", [
            "วันที่ (ใหม่ -> เก่า)", 
            "วันที่ (เก่า -> ใหม่)", 
            "จำนวนเงิน (มาก -> น้อย)", 
            "จำนวนเงิน (น้อย -> มาก)"
        ])

    st.markdown("---")

    # ----------------------------------------
    # 2. ส่วนของการสร้าง Dynamic SQL Query
    # ----------------------------------------
    # Query เริ่มต้น
    base_query = """
        SELECT 
            t.TransactionID AS 'รหัสรายการ', 
            u.FirstName AS 'ผู้ทำรายการ', 
            w.WalletName AS 'ช่องทาง', 
            c.CategoryName AS 'หมวดหมู่', 
            t.Amount AS 'จำนวนเงิน', 
            t.TransactionDate AS 'วันที่', 
            t.Note AS 'บันทึก'
        FROM Transactions t
        JOIN Users u ON t.UserID = u.UserID
        JOIN Wallets w ON t.WalletID = w.WalletID
        JOIN Categories c ON t.CategoryID = c.CategoryID
        WHERE 1=1 
    """
    params = []

    # เพิ่มเงื่อนไขการค้นหาด้วย LIKE
    if search_note:
        base_query += " AND t.Note LIKE %s"
        params.append(f"%{search_note}%")

    # เพิ่มเงื่อนไขการกรองด้วย WHERE
    if filter_cat != "ทั้งหมด":
        base_query += " AND t.CategoryID = %s"
        params.append(dict_c[filter_cat])

    # เพิ่มเงื่อนไขการจัดเรียงด้วย ORDER BY
    if sort_option == "วันที่ (ใหม่ -> เก่า)":
        base_query += " ORDER BY t.TransactionDate DESC"
    elif sort_option == "วันที่ (เก่า -> ใหม่)":
        base_query += " ORDER BY t.TransactionDate ASC"
    elif sort_option == "จำนวนเงิน (มาก -> น้อย)":
        base_query += " ORDER BY t.Amount DESC"
    elif sort_option == "จำนวนเงิน (น้อย -> มาก)":
        base_query += " ORDER BY t.Amount ASC"

    # ----------------------------------------
    # 3. ดึงข้อมูลและแสดงผล
    # ----------------------------------------
    conn = get_connection()
    # ใช้ pandas โยน params เข้าไปเพื่อป้องกัน SQL Injection
    df_search = pd.read_sql(base_query, conn, params=tuple(params) if params else None)
    
    st.write(f"พบข้อมูลทั้งหมด **{len(df_search)}** รายการ")
    st.dataframe(df_search, use_container_width=True)
    conn.close()
    
