import streamlit as st
import pandas as pd
import anthropic
import os

# ── Config ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DATA_PATH = os.path.expanduser("~/Desktop/Marbella Lane 工作细节 AI/运营助理/Operations daily work-Kelly.xlsx")

TASK_TYPES = {
    1: "Guest Request Handling", 2: "Owner Communication", 3: "Cleaning Quality Check",
    4: "Guest Complaint", 5: "Floating Task Check", 6: "Negative Review Analysis",
    7: "Procurement", 8: "Financial Reconciliation", 9: "Cleaning Scheduling",
    10: "Vendor Quote Request", 11: "Inbox Email Check", 12: "Enso Message Check",
    13: "Camera Status Check", 14: "Noiseaware Status Check", 15: "Reservation Issues",
    16: "Pet Issues", 17: "Claims / Compensation", 18: "Trash Issues",
    19: "Account Issues", 20: "Pest Control", 21: "Routine Maintenance", 22: "Update Records"
}

DEMO_TASKS = [
    {"date": "Apr 1", "property": "614", "task_type_name": "Camera Status Check", "status": "In Progress", "owner": "Rebecca", "issue": "Camera offline — likely network issue", "resolution": "Owner contacted to check router"},
    {"date": "Apr 1", "property": "1924B", "task_type_name": "Pest Control", "status": "Completed", "owner": "Doris", "issue": "Guest reported moths", "resolution": "Pest control inspection scheduled, Homeshield checked"},
    {"date": "Apr 2", "property": "66007", "task_type_name": "Guest Complaint", "status": "In Progress", "owner": "Kelly", "issue": "Guest complained about pool, requesting refund", "resolution": "Offered 20% max refund, issue resolved"},
    {"date": "Apr 2", "property": "62828", "task_type_name": "Routine Maintenance", "status": "Completed", "owner": "Philip", "issue": "Irrigation pipe burst, fallen tree trunk", "resolution": "Philip repaired leak and removed dead tree, photos uploaded"},
    {"date": "Apr 5", "property": "614", "task_type_name": "Camera Status Check", "status": "In Progress", "owner": "Rebecca", "issue": "Camera still offline after network fix", "resolution": "Waiting for owner follow-up"},
    {"date": "Apr 5", "property": "1924A", "task_type_name": "Trash Issues", "status": "Completed", "owner": "Miriam", "issue": "Bulk trash pickup needed — broken TV", "resolution": "Ontario Trash scheduled Apr 6, Miriam tasked to bring TV to curb Apr 5"},
    {"date": "Apr 5", "property": "795", "task_type_name": "Routine Maintenance", "status": "Completed", "owner": "Tony", "issue": "Underground pipe leak reported by city", "resolution": "Plumber Tony fixed, cost $1,500, owner approved"},
    {"date": "Apr 6", "property": "1022", "task_type_name": "Camera Status Check", "status": "In Progress", "owner": "Kelly", "issue": "Camera offline — guest checking out Apr 11", "resolution": "Scheduled inspection after guest checkout"},
    {"date": "Apr 6", "property": "3173", "task_type_name": "Camera Status Check", "status": "In Progress", "owner": "Doris", "issue": "Camera offline — solar panel issue", "resolution": "Doris to inspect after current guest checks out"},
    {"date": "Apr 7", "property": "65626", "task_type_name": "Guest Request Handling", "status": "Completed", "owner": "Edgardo", "issue": "Guest reported pool not heating", "resolution": "Edgardo explained spa vs pool heating system, pool tech visited same day"},
    {"date": "Apr 7", "property": "1924B", "task_type_name": "Pest Control", "status": "In Progress", "owner": "Owner", "issue": "Vendor quotes received for fumigation", "resolution": "Sent to owner to decide — fumigation vs spot treatment"},
    {"date": "Apr 8", "property": "614", "task_type_name": "Owner Communication", "status": "In Progress", "owner": "Owner", "issue": "Network signal issue affecting camera", "resolution": "Waiting for owner to contact ISP"},
    {"date": "Apr 9", "property": "360A", "task_type_name": "Negative Review Analysis", "status": "In Progress", "owner": "Evans", "issue": "Guest complained about ants and shower after checkout", "resolution": "Investigated — guest gave no prior notice during stay"},
    {"date": "Apr 10", "property": "62695", "task_type_name": "Pest Control", "status": "In Progress", "owner": "Edgardo", "issue": "Long-term tenant reported multiple issues including pests", "resolution": "Handyman and AC company scheduled, pest control quote rejected by owner"},
    {"date": "Apr 10", "property": "1161", "task_type_name": "Guest Complaint", "status": "Completed", "owner": "Doris", "issue": "Neighbor complained about guest party noise", "resolution": "Checked Noiseaware — noise was previous night, not tonight"},
    {"date": "Apr 11", "property": "942", "task_type_name": "Guest Request Handling", "status": "Completed", "owner": "Rubi", "issue": "Guest reported front door battery, fridge filter needs replacing", "resolution": "Rubi fixed cabinet door, batteries and filter purchased"},
    {"date": "Apr 12", "property": "1943", "task_type_name": "Routine Maintenance", "status": "In Progress", "owner": "Kelly", "issue": "Smart lock draining battery too fast", "resolution": "Emailed owner, monitoring next battery replacement cycle"},
    {"date": "Apr 12", "property": "884", "task_type_name": "Routine Maintenance", "status": "Completed", "owner": "Jacky", "issue": "Washing machine not working", "resolution": "Serial number obtained, vendor contacted, part ordered and installed"},
    {"date": "Apr 13", "property": "614", "task_type_name": "Camera Status Check", "status": "In Progress", "owner": "Rebecca", "issue": "Camera offline — 4th time this quarter", "resolution": "Escalated to owner, likely router replacement needed"},
    {"date": "Apr 14", "property": "319", "task_type_name": "Claims / Compensation", "status": "Completed", "owner": "Sweetcel", "issue": "Wardrobe door damaged by guest", "resolution": "Claimed $800 on Airbnb, platform approved $651, owner notified"},
]

# ── Load Data ────────────────────────────────────────────
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            xl = pd.ExcelFile(DATA_PATH)
            tasks = pd.read_excel(xl, sheet_name="Daily Tasks")
            tasks.columns = [
                "task_link", "date", "task_type", "property", "status", "owner",
                "issue", "action", "needs_vendor", "vendor_progress",
                "resolution", "issue_found", "issue_type", "is_recurring",
                "due_date", "completed_date", "followup"
            ]
            tasks = tasks[tasks["date"].notna()].copy()
            tasks["task_type_name"] = tasks["task_type"].apply(
                lambda x: TASK_TYPES.get(int(x), str(x)) if pd.notna(x) and str(x).replace('.0','').isdigit() else str(x) if pd.notna(x) else ""
            )
            cameras = pd.read_excel(xl, sheet_name="Camera & Noiseware")
            return tasks, cameras, True
        except Exception as e:
            st.warning(f"Could not load local data: {e}. Using demo data.")

    # Demo mode
    tasks = pd.DataFrame(DEMO_TASKS)
    cameras = pd.DataFrame([
        {"Property": 614, "Camera": "offline", "Noiseaware": "online", "Last Checked": "Apr 13", "Notes": "4th outage this quarter — likely router issue"},
        {"Property": 3173, "Camera": "offline", "Noiseaware": "online", "Last Checked": "Apr 6", "Notes": "Solar panel charging issue"},
        {"Property": 1022, "Camera": "offline", "Noiseaware": "online", "Last Checked": "Apr 7", "Notes": "Guest in until Apr 11, inspect after checkout"},
        {"Property": 1987, "Camera": "online", "Noiseaware": "offline", "Last Checked": "Apr 3", "Notes": "Rebecca to check on next visit"},
    ])
    return tasks, cameras, False

def ask_claude(system_prompt, user_msg):
    key = ANTHROPIC_API_KEY or st.secrets.get("ANTHROPIC_API_KEY", "")
    if not key:
        return "⚠️ No API key configured. Please add ANTHROPIC_API_KEY to Streamlit secrets."
    client = anthropic.Anthropic(api_key=key)
    r = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}]
    )
    return r.content[0].text

def build_context(tasks_df):
    lines = []
    for _, row in tasks_df.iterrows():
        line = (f"[{row.get('date','')}] Property:{row.get('property','')} "
                f"Type:{row.get('task_type_name','')} Status:{row.get('status','')} "
                f"Owner:{row.get('owner','')} | Issue:{row.get('issue','')} | "
                f"Resolution:{row.get('resolution','')}")
        lines.append(line)
    return "\n".join(lines[:200])

def find_recurring_issues(tasks_df):
    property_issues = {}
    for _, row in tasks_df.iterrows():
        prop = str(row.get("property", "")).strip()
        issue = str(row.get("issue", "")).strip()
        if prop and issue and prop != "nan" and issue != "nan":
            if prop not in property_issues:
                property_issues[prop] = []
            property_issues[prop].append(issue)
    recurring = []
    for prop, issues in property_issues.items():
        if len(issues) >= 2:
            recurring.append({"property": prop, "count": len(issues), "issues": issues})
    return sorted(recurring, key=lambda x: x["count"], reverse=True)

# ── UI ───────────────────────────────────────────────────
st.set_page_config(page_title="StayVibe Brain", page_icon="🧠", layout="wide")

col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("## 🧠")
with col_title:
    st.markdown("# StayVibe Brain")
    st.caption("AI Operations Intelligence for Short-Term Rental Managers")

st.divider()

tasks, cameras, is_live = load_data()

if not is_live:
    st.info("🔍 **Demo Mode** — showing sample Marbella Lane operational data (20 records). Live version connects to 127+ real task records.")

# ── Metrics ──────────────────────────────────────────────
total = len(tasks)
active = len(tasks[tasks["status"].astype(str).str.contains("In Progress|处理中", na=False)])
done = len(tasks[tasks["status"].astype(str).str.contains("Completed|完成", na=False)])
properties = tasks["property"].nunique()

m1, m2, m3, m4 = st.columns(4)
m1.metric("📋 Total Tasks", total)
m2.metric("⏳ In Progress", active)
m3.metric("✅ Completed", done)
m4.metric("🏠 Properties Tracked", properties)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Ask Anything", "🚨 Recurring Issues", "📊 Overview", "✍️ Draft a Reply"])

# ── Tab 1 ────────────────────────────────────────────────
with tab1:
    st.subheader("Ask anything about your operations")
    st.caption("e.g. Which properties had camera issues? / What happened at property 614? / What's still unresolved?")

    query = st.text_input("Your question", placeholder="e.g. Which properties have had pest control problems?")

    if query:
        with st.spinner("Thinking..."):
            context = build_context(tasks)
            system = f"""You are StayVibe Brain, the AI operations assistant for Marbella Lane — a short-term rental management company with 200 properties across California, Hawaii, Seattle, Austin, and Mexico.
You have access to the following real operational task records:
{context}

Answer the question based on the data. Be specific — reference property numbers and dates when relevant. Keep your answer concise and actionable. Respond in English."""
            answer = ask_claude(system, query)
        st.markdown("**🧠 StayVibe Brain:**")
        st.info(answer)

    st.divider()
    st.subheader("Filter Tasks")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_filter = st.selectbox("Filter by status", ["All", "In Progress", "Completed"])
    with col_f2:
        prop_filter = st.text_input("Filter by property", placeholder="e.g. 614")

    filtered = tasks.copy()
    if status_filter != "All":
        filtered = filtered[filtered["status"].astype(str).str.contains(status_filter, na=False)]
    if prop_filter:
        filtered = filtered[filtered["property"].astype(str).str.contains(prop_filter, na=False)]

    display = filtered[["date", "property", "task_type_name", "status", "owner", "issue", "resolution"]].copy()
    display.columns = ["Date", "Property", "Task Type", "Status", "Owner", "Issue", "Resolution"]
    st.dataframe(display.head(50), use_container_width=True, hide_index=True)

# ── Tab 2 ────────────────────────────────────────────────
with tab2:
    st.subheader("🚨 Recurring Issue Radar")
    st.caption("Properties with repeated problems — automatically detected from your task history")

    recurring = find_recurring_issues(tasks)

    if recurring:
        for item in recurring[:10]:
            prop = item["property"]
            count = item["count"]
            issues = item["issues"]
            color = "🔴" if count >= 4 else "🟡" if count >= 3 else "🔵"
            with st.expander(f"{color} Property **{prop}** — {count} recorded issues"):
                for i, issue in enumerate(issues, 1):
                    st.write(f"{i}. {issue}")
                if st.button(f"🧠 Analyze this property", key=f"analyze_{prop}"):
                    with st.spinner("Analyzing..."):
                        prop_tasks = tasks[tasks["property"].astype(str).str.contains(str(prop), na=False)]
                        context = build_context(prop_tasks)
                        system = "You are an expert STR operations analyst. Review the task history for this property and identify root causes. Give 2-3 specific, actionable recommendations. Be concise. Respond in English."
                        analysis = ask_claude(system, f"Property {prop} task history:\n{context}")
                    st.success(analysis)

    st.divider()
    st.subheader("📷 Camera & Noiseaware Status")
    if not cameras.empty:
        st.dataframe(cameras, use_container_width=True, hide_index=True)

# ── Tab 3 ────────────────────────────────────────────────
with tab3:
    st.subheader("📊 Operations Overview")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Task Type Breakdown**")
        st.bar_chart(tasks["task_type_name"].value_counts().head(10))
    with col_b:
        st.markdown("**Task Status Breakdown**")
        st.bar_chart(tasks["status"].value_counts())

    st.markdown("**Most Active Properties (Top 10)**")
    st.bar_chart(tasks["property"].value_counts().head(10))

    st.markdown("**Team Workload Distribution**")
    st.bar_chart(tasks["owner"].value_counts().head(10))

# ── Tab 4 ────────────────────────────────────────────────
with tab4:
    st.subheader("✍️ AI-Drafted Professional Replies")

    reply_type = st.selectbox("Reply type", [
        "Respond to a guest complaint",
        "Update owner on a maintenance issue",
        "Explain pricing strategy to owner",
        "Request a quote from a vendor",
        "Submit a claim to the platform",
        "Apologize and offer compensation to a guest"
    ])

    situation = st.text_area(
        "Describe the situation",
        placeholder="e.g. Guest at property 614 reported WiFi was down for 2 days and is asking for a refund...",
        height=120
    )

    tone = st.radio("Tone", ["Professional & Formal", "Warm & Friendly", "Brief & Direct"], horizontal=True)
    lang = st.radio("Language", ["English", "Chinese", "Bilingual (EN + CN)"], horizontal=True)

    if st.button("🧠 Generate Draft", type="primary") and situation:
        with st.spinner("Drafting..."):
            system = f"""You are the professional operations manager at Marbella Lane, a premium short-term rental management company with 200 properties across California, Hawaii, Seattle, Austin, and Mexico.
Draft a reply for: {reply_type}
Tone: {tone}
Language: {lang}
Requirements: Professional, empathetic, protect the company's interests while making the recipient feel valued. Do not over-promise. Keep it concise."""
            draft = ask_claude(system, f"Situation: {situation}\n\nPlease draft the reply.")
        st.markdown("**📝 Draft Reply:**")
        st.text_area("Copy and use directly", value=draft, height=250)

# ── Footer ───────────────────────────────────────────────
st.divider()
st.caption("🧠 StayVibe Brain v0.1 · Built by Yanan Sun · Marbella Lane · May 2026")
