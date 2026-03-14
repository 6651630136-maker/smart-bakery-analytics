import streamlit as st
import pandas as pd
import plotly.express as px
import json
import hashlib
import numpy as np
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor

st.set_page_config(page_title="Smart Bakery Platform", layout="wide")

# ---------------- SESSION ----------------

if "landing" not in st.session_state:
    st.session_state.landing = True

# ---------------- LANDING PAGE ----------------

if st.session_state.landing:

    st.markdown("""
    <style>

    .stApp{
        background-image:url("https://images.unsplash.com/photo-1509440159596-0249088772ff");
        background-size:cover;
        background-position:center;
    }

    .overlay{
        background:rgba(0,0,0,0.55);
        padding:80px;
        border-radius:20px;
        text-align:center;
        margin-top:80px;
    }

    .title{
        font-size:55px;
        font-weight:900;
        color:white;
        letter-spacing:3px;
        text-shadow:2px 2px 15px rgba(0,0,0,0.8);
    }

    .subtitle{
        font-size:22px;
        color:#eeeeee;
        margin-top:10px;
        margin-bottom:60px;
    }

    .stButton>button{
        font-size:26px;
        padding:20px 60px;
        border-radius:12px;
        background:linear-gradient(45deg,#ff4b4b,#ff7a7a);
        color:white;
        border:none;
        box-shadow:0px 8px 25px rgba(0,0,0,0.5);
    }

    </style>
    """, unsafe_allow_html=True)

    col1,col2,col3 = st.columns([1,2,1])

    with col2:

        st.markdown("""
        <div class="overlay">

        <div class="title">
        SMART BAKERY PLATFORM
        </div>

        <div class="subtitle">
        Powered Business Intelligence Platform
        </div>

        </div>
        """, unsafe_allow_html=True)

        colA, colB, colC = st.columns([1,2,1])

        with colB:
            if st.button("ENTER TO DASHBOARD", use_container_width=True):
                st.session_state.landing = False
                st.rerun()

    st.stop()

# ---------------- USER AUTH ----------------

USER_FILE="users.json"

def load_users():
    try:
        with open(USER_FILE,"r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USER_FILE,"w") as f:
        json.dump(users,f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if "user" not in st.session_state:
    st.session_state.user=None

users=load_users()

# ---------------- LOGIN ----------------

if st.session_state.user is None:

    menu=["Sign In","Sign Up"]
    choice=st.sidebar.selectbox("Menu",menu)

    st.title("Smart Bakery Business Intelligence Platform")

    if choice=="Sign In":

        username=st.text_input("Username")
        password=st.text_input("Password",type="password")

        if st.button("Login"):

            if username in users and users[username]==hash_password(password):

                st.session_state.user=username
                st.success("Login Success")
                st.rerun()

            else:
                st.error("Invalid Username or Password")

    if choice=="Sign Up":

        new_user=st.text_input("Create Username")
        new_pass=st.text_input("Create Password",type="password")

        if st.button("Create Account"):

            users[new_user]=hash_password(new_pass)
            save_users(users)

            st.success("Account Created")

# ---------------- MAIN SYSTEM ----------------

else:

    st.sidebar.success(f"Welcome {st.session_state.user}")

        # --------- DASHBOARD BACKGROUND ---------

    st.markdown("""
    <style>

    .stApp{
        background-image: url("https://images.unsplash.com/photo-1509440159596-0249088772ff");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    [data-testid="stSidebar"]{
        background: rgba(0,0,0,0.65);
    }

    .block-container{
        background: rgba(255,255,255,0.93);
        padding: 2rem;
        border-radius: 15px;
    }

    </style>
    """, unsafe_allow_html=True)



    if st.sidebar.button("Sign Out"):
        st.session_state.user=None
        st.rerun()

    page=st.sidebar.selectbox(
    "Menu",
    ["Dashboard","Upload Excel","Sales Forecast"]
)

# ================= DASHBOARD =================

    if page=="Dashboard":

        st.title("Bakery Sales Intelligence Dashboard")

        df=pd.read_excel("sales_all_train_val_test2.xlsx")

        df["Date"]=pd.to_datetime(df["Date"])
        df["Year"]=df["Date"].dt.year
        df["Month"]=df["Date"].dt.month
        df["Day"]=df["Date"].dt.day_name()

        # ---------- FILTER ----------

        st.sidebar.header("Filter")

        product_filter=st.sidebar.multiselect(
            "Product",
            df["Productname"].unique(),
            default=df["Productname"].unique()
        )

        start=st.sidebar.date_input("Start Date",df["Date"].min())
        end=st.sidebar.date_input("End Date",df["Date"].max())

        data=df[
            (df["Productname"].isin(product_filter)) &
            (df["Date"]>=pd.to_datetime(start)) &
            (df["Date"]<=pd.to_datetime(end))
        ]

        # ---------- TREND ----------

        trend=data.groupby("Date")["Sales"].sum().reset_index()

        trend["t"]=np.arange(len(trend))

        X=trend[["t"]]
        y=trend["Sales"]

        model=LinearRegression()
        model.fit(X,y)

        trend["Prediction"]=model.predict(X)

        error=abs(trend["Sales"]-trend["Prediction"])

        accuracy=100-(error.sum()/trend["Sales"].sum()*100)

        # ---------- SALES GROWTH ----------

        if len(trend)>1:
            first=trend["Sales"].iloc[0]
            last=trend["Sales"].iloc[-1]
            if first != 0:
                growth=((last-first)/first)*100
            else:
                growth=0
        else:
            growth=0

        # ---------- KPI ----------

        k1,k2,k3,k4=st.columns(4)

        k1.metric("Total Sales",f"€{data['Sales'].sum():,.0f}")
        k2.metric("Forecast Accuracy",f"{accuracy:.2f}%")
        k3.metric("Sales Growth",f"{growth:.2f}%")
        k4.metric("Products",data["Productname"].nunique())

        # ---------- PRODUCT SALES ----------

        product_sales=data.groupby("Productname")["Sales"].sum().reset_index()

        col1,col2=st.columns(2)

        fig1=px.pie(product_sales,names="Productname",values="Sales")
        col1.plotly_chart(fig1,use_container_width=True)

        fig2=px.bar(product_sales,x="Productname",y="Sales",color="Productname")
        fig2.update_layout(yaxis_tickprefix="€")

        col2.plotly_chart(fig2,use_container_width=True)

        # ---------- PRODUCT CONTRIBUTION ----------

        st.subheader("Product Contribution %")

        product_sales["Contribution"]=product_sales["Sales"]/product_sales["Sales"].sum()*100

        fig_contribution=px.bar(
            product_sales,
            x="Productname",
            y="Contribution",
            color="Productname"
        )

        st.plotly_chart(fig_contribution,use_container_width=True)

        # ---------- ACTUAL VS PREDICTION ----------

        st.subheader("Actual vs Predicted Sales")

        fig3=px.line(trend,x="Date",y=["Sales","Prediction"])
        fig3.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig3,use_container_width=True)

        # ---------- FUTURE FORECAST ----------

        st.subheader("Future Sales Forecast")

        future_days=30

        future_t=np.arange(len(trend),len(trend)+future_days)

        future_pred=model.predict(future_t.reshape(-1,1))

        future_dates=pd.date_range(
            start=trend["Date"].max(),
            periods=future_days+1
        )[1:]

        future_df=pd.DataFrame({
            "Date":future_dates,
            "Forecast":future_pred
        })

        fig_future=px.line(future_df,x="Date",y="Forecast")
        fig_future.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig_future,use_container_width=True)

        # ---------- MONTHLY TREND ----------

        st.subheader("Monthly Sales Trend")

        month=data.groupby(data["Date"].dt.to_period("M"))["Sales"].sum().reset_index()

        month["Date"]=month["Date"].astype(str)

        fig4=px.line(month,x="Date",y="Sales")
        fig4.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig4,use_container_width=True)

        # ---------- SALES BY DAY ----------

        st.subheader("Sales by Day of Week")

        day=data.groupby("Day")["Sales"].sum().reset_index()

        fig5=px.bar(day,x="Day",y="Sales")
        fig5.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig5,use_container_width=True)

        # ---------- HEATMAP ----------

        st.subheader("Monthly Sales Heatmap")

        heat=pd.pivot_table(
            data,
            values="Sales",
            index="Month",
            columns="Year",
            aggfunc="sum"
        )
        heat=heat.fillna(0)

        fig6=px.imshow(heat)

        st.plotly_chart(fig6,use_container_width=True)

        # ---------- SALES DISTRIBUTION ----------

        st.subheader("Sales Distribution")

        fig_dist=px.histogram(data,x="Sales",nbins=30)
        fig_dist.update_layout(xaxis_tickprefix="€")

        st.plotly_chart(fig_dist,use_container_width=True)

        # ---------- PRODUCT TABLE ----------

        st.subheader("Product Sales Comparison")

        pivot=pd.pivot_table(
            data,
            values="Sales",
            index="Productname",
            columns="Year",
            aggfunc="sum"
        )

        st.dataframe(pivot,use_container_width=True)

        csv=pivot.to_csv().encode("utf-8")

        st.download_button(
            "Download Report",
            csv,
            "sales_report.csv",
            "text/csv"
        )

        # ---------- EXECUTIVE SUMMARY ----------

        st.subheader("Executive Summary")

        best_product=product_sales.sort_values("Sales",ascending=False).iloc[0]
        worst_product=product_sales.sort_values("Sales").iloc[0]

        best_day=data.groupby("Day")["Sales"].sum().idxmax()

        st.info(f"""
Total Revenue : €{data['Sales'].sum():,.0f}

Top Product : {best_product['Productname']}

Weak Product : {worst_product['Productname']}

Best Sales Day : {best_day}
""")

        # ---------- BUSINESS INSIGHT ----------

        st.subheader("Business Insight")

        st.success(f"""
Best Selling Product : {best_product['Productname']}

Lowest Selling Product : {worst_product['Productname']}

Recommendation :

Increase production of {best_product['Productname']}

Create promotion for {worst_product['Productname']}
""")

# ================= UPLOAD PAGE =================

    # ================= UPLOAD PAGE =================

    if page=="Upload Excel":

        st.title("Upload Excel Sales Data")

        file = st.file_uploader("Upload Excel", type=["xlsx"])

        if file:

            df = pd.read_excel(file)

            df["Date"] = pd.to_datetime(df["Date"])

            st.success("Upload Successful")

            st.subheader("Preview Data")

            st.dataframe(df.head())

            # ---------------- FILTER ----------------

            st.sidebar.header("Upload Data Filter")

            product_filter = st.sidebar.multiselect(
                "Select Product",
                df["Productname"].unique(),
                default=df["Productname"].unique()
            )

            start_date = st.sidebar.date_input(
                "Start Date",
                df["Date"].min()
            )

            end_date = st.sidebar.date_input(
                "End Date",
                df["Date"].max()
            )

            data = df[
                (df["Productname"].isin(product_filter)) &
                (df["Date"] >= pd.to_datetime(start_date)) &
                (df["Date"] <= pd.to_datetime(end_date))
            ]

            # ---------------- KPI ----------------

            st.subheader("Sales Summary")

            k1,k2,k3 = st.columns(3)

            k1.metric("Total Sales",f"€{data['Sales'].sum():,.0f}")
            k2.metric("Products", data["Productname"].nunique())
            k3.metric("Records", len(data))

            # ---------------- SALES TREND ----------------

            st.subheader("Sales Trend")

            trend = data.groupby("Date")["Sales"].sum().reset_index()

            fig1 = px.line(
                trend,
                x="Date",
                y="Sales"
            )
            fig1.update_layout(yaxis_tickprefix="€")

            st.plotly_chart(fig1, use_container_width=True)

            # ---------------- PRODUCT SHARE ----------------

            st.subheader("Product Share")

            product_sales = data.groupby("Productname")["Sales"].sum().reset_index()

            col1,col2 = st.columns(2)

            fig2 = px.pie(
                product_sales,
                names="Productname",
                values="Sales"
            )

            col1.plotly_chart(fig2, use_container_width=True)

            fig3 = px.bar(
                product_sales,
                x="Productname",
                y="Sales",
                color="Productname"
            )

            col2.plotly_chart(fig3, use_container_width=True)

            # ---------------- SALES DISTRIBUTION ----------------

            st.subheader("Sales Distribution")

            fig4 = px.histogram(
                data,
                x="Sales",
                nbins=30
            )

            st.plotly_chart(fig4, use_container_width=True)

            # ---------------- DAILY SALES ----------------

            st.subheader("Daily Sales")


            daily = data.groupby(data["Date"].dt.day_name())["Sales"].sum().reset_index()

            daily.columns=["Day","Sales"]

            fig5 = px.bar(
                daily,
                x="Day",
                y="Sales"
            )

            st.plotly_chart(fig5, use_container_width=True)

            # ---------------- TABLE ----------------

            st.subheader("Sales Table")

            st.dataframe(data)

            csv = data.to_csv().encode("utf-8")

            st.download_button(
                "Download Data",
                csv,
                "upload_sales_data.csv",
                "text/csv"
            )

            # ================= XGBOOST FORECAST =================
# ================= SALES FORECAST =================

    if page=="Sales Forecast":

        st.title("Sales Forecast (Machine Learning)")

        # ---------- LOAD DATA ----------

        sales_df = pd.read_excel("sales_all_train_val_test2.xlsx")
        forecast_df = pd.read_excel("forecast_output.xlsx")

        sales_df["Date"] = pd.to_datetime(sales_df["Date"])
        forecast_df["Date"] = pd.to_datetime(forecast_df["Date"])

        # ---------- FILTER ----------

        st.sidebar.header("Forecast Filter")

        product_filter = st.sidebar.multiselect(
            "Product",
            sales_df["Productname"].unique(),
            default=sales_df["Productname"].unique()
        )

        start = st.sidebar.date_input(
            "Start Date",
            sales_df["Date"].min()
        )

        end = st.sidebar.date_input(
            "End Date",
            sales_df["Date"].max()
        )

        data = sales_df[
            (sales_df["Productname"].isin(product_filter)) &
            (sales_df["Date"] >= pd.to_datetime(start)) &
            (sales_df["Date"] <= pd.to_datetime(end))
        ]

        if len(data) == 0:
            st.warning("No data available")
            st.stop()

        # ---------- KPI ----------

        k1,k2,k3 = st.columns(3)

        k1.metric("Total Sales",f"€{data['Sales'].sum():,.0f}")
        k2.metric("Products",data["Productname"].nunique())
        k3.metric("Records",len(data))

        # ---------- ACTUAL SALES TREND ----------

        st.subheader("Actual Sales Trend")

        actual_trend = data.groupby("Date")["Sales"].sum().reset_index()

        fig1 = px.line(
            actual_trend,
            x="Date",
            y="Sales"
        )

        fig1.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig1,use_container_width=True)

        # ---------- FORECAST DATA ----------

        st.subheader("Sales Forecast (ML Model Output)")

        forecast_data = forecast_df[
            forecast_df["Productname"].isin(product_filter)
        ]

        fig2 = px.line(
            forecast_data,
            x="Date",
            y="Sales_forecast"
        )

        fig2.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig2,use_container_width=True)

        # ---------- ACTUAL VS FORECAST ----------

        st.subheader("Actual vs Forecast Comparison")

        actual = actual_trend.copy()
        forecast = forecast_data.groupby("Date")["Sales_forecast"].sum().reset_index()

        merged = pd.merge(
            actual,
            forecast,
            on="Date",
            how="outer"
        ).fillna(0)

        fig3 = px.line(
            merged,
            x="Date",
            y=["Sales","Sales_forecast"]
        )

        fig3.update_layout(yaxis_tickprefix="€")

        st.plotly_chart(fig3,use_container_width=True)

        # ---------- FORECAST TABLE ----------

        st.subheader("Forecast Data Table")

        st.dataframe(forecast_data)

        csv = forecast_data.to_csv().encode("utf-8")

        st.download_button(
            "Download Forecast",
            csv,
            "forecast_output.csv",
            "text/csv"
        )

st.markdown("""
<style>
.footer{
position:fixed;
left:0;
bottom:0;
width:100%;
background-color:rgba(0,0,0,0.8);
color:white;
text-align:center;
padding:10px;
font-size:14px;
}
</style>

<div class="footer">
© 2026 Smart Bakery BI Platform | Powered by Data Analytics & Machine Learning
</div>
""", unsafe_allow_html=True)
