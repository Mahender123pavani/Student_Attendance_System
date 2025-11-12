import streamlit as st
import pandas as pd
from datetime import date
from db import init_db, get_all_students, add_student, delete_student, update_student, mark_attendance, get_attendance_by_date, create_user, verify_user

# Initialize DB
init_db()

st.set_page_config(page_title="Student Attendance System", layout="wide")

# ---------- Login / Signup ----------
if "user" not in st.session_state:
    st.title("Login / Signup")
    tab = st.radio("Select", ["Login", "Sign Up"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if tab == "Sign Up":
        if st.button("Sign Up"):
            create_user(username, password)
            st.success("Account created! Please log in.")
    else:
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state["user"] = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password ❌")

else:
    st.sidebar.title(f"Welcome {st.session_state['user']} 👋")
    page = st.sidebar.selectbox("Select Page", ["Add Student", "Mark Attendance", "View Students", "View Attendance", "Attendance Analysis"])

    # ---------- Add Student ----------
    if page == "Add Student":
        st.subheader("Add Student")
        name = st.text_input("Name")
        roll_no = st.text_input("Roll Number")
        department = st.text_input("Department")
        year = st.number_input("Year", min_value=1, max_value=10)
        phone = st.text_input("Phone")
        address = st.text_input("Address")

        if st.button("Add Student"):
            add_student(roll_no, name, department, year, phone, address)
            st.success(f"Student {name} added successfully!")

    # ---------- Mark Attendance ----------
    elif page == "Mark Attendance":
        st.subheader("Mark Attendance 🕒")
        attendance_date = st.date_input("Select Date", value=date.today())
        students = get_all_students()

        if students:
            st.markdown("### Attendance Table")
            attendance_dict = {}

            # Table headers
            col0, col1, col2 = st.columns([1, 3, 2])
            col0.write("S.No")
            col1.write("Student Name")
            col2.write("Status")

            # Pre-fill existing attendance
            existing_attendance = {a['student_id']: a['status'] for a in get_attendance_by_date(attendance_date)}

            for i, student in enumerate(students, start=1):
                col0, col1, col2 = st.columns([1, 3, 2])
                col0.write(i)
                col1.write(f"{student['roll_no']} - {student['name']}")
                default_status = existing_attendance.get(student['id'], "Absent")
                status = col2.radio(
                    "",
                    ["Present", "Absent"],
                    horizontal=True,
                    index=0 if default_status=="Present" else 1,
                    key=f"att_{student['id']}"
                )
                attendance_dict[student['id']] = status

            if st.button("Save Attendance"):
                for student_id, status in attendance_dict.items():
                    mark_attendance(student_id, status, attendance_date)
                st.success(f"Attendance saved for {attendance_date}!")
        else:
            st.info("No students found. Please add students first.")

    # ---------- View Students ----------
    elif page == "View Students":
        st.subheader("All Students")
        search_query = st.text_input("Search by Name / Roll No / Department")
        students = pd.DataFrame(get_all_students())

        if not students.empty:
            if search_query:
                students = students[
                    students['name'].str.contains(search_query, case=False) |
                    students['roll_no'].str.contains(search_query, case=False) |
                    students['department'].str.contains(search_query, case=False)
                ]

            if not students.empty:
                for idx, row in students.iterrows():
                    st.markdown(f"{row['roll_no']} - {row['name']}")
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1,1,1,1,1,1,1,1])
                    with col1: name = st.text_input("Name", value=row['name'], key=f"name_{row['id']}")
                    with col2: roll_no = st.text_input("Roll No", value=row['roll_no'], key=f"roll_{row['id']}")
                    with col3: department = st.text_input("Department", value=row['department'], key=f"dept_{row['id']}")
                    with col4: year = st.number_input("Year", value=row['year'], min_value=1, max_value=10, key=f"year_{row['id']}")
                    with col5: phone = st.text_input("Phone", value=row['phone'], key=f"phone_{row['id']}")
                    with col6: address = st.text_input("Address", value=row['address'], key=f"address_{row['id']}")
                    with col7:
                        if st.button("Update", key=f"update_{row['id']}"):
                            update_student(row['id'], roll_no, name, department, year, phone, address)
                            st.success(f"{name} updated successfully!")
                            st.experimental_rerun()
                    with col8:
                        if st.button("Delete", key=f"delete_{row['id']}"):
                            delete_student(row['id'])
                            st.success(f"{name} deleted successfully!")
                            st.rerun()
            else:
                st.info("No students found for your search.")
        else:
            st.info("No students available.")

    # ---------- View Attendance ----------
    elif page == "View Attendance":
        st.subheader("Attendance Records")
        records = pd.DataFrame(get_attendance_by_date())
        if not records.empty:
            st.dataframe(records)
            st.download_button("Download CSV", records.to_csv(index=False), "attendance.csv", "text/csv")
        else:
            st.info("No attendance records found.")

    # ---------- Attendance Analysis ----------
    elif page == "Attendance Analysis":
        st.subheader("Attendance Analysis 📊")
        date_filter = st.date_input("Select Date (leave blank for all)")
        records = pd.DataFrame(get_attendance_by_date(date_filter if date_filter else None))

        if not records.empty:
            summary = records['status'].value_counts().reset_index()
            summary.columns = ['Status', 'Count']

            st.write("### Attendance Summary")
            st.dataframe(summary)
            st.download_button("Download Analysis CSV", summary.to_csv(index=False), "attendance_summary.csv", "text/csv")

            st.write("### Bar Chart")
            st.bar_chart(summary.set_index('Status'))

            st.write("### Pie Chart")
            st.pyplot(summary.plot.pie(y='Count', labels=summary['Status'], autopct='%1.1f%%', legend=False).get_figure())
        else:
            st.info("No attendance data found.")

    # ---------- Logout ----------
    st.sidebar.button("Logout", on_click=lambda: st.session_state.pop("user", None) or st.rerun())