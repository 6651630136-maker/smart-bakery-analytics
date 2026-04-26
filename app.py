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

    # load file
        df = pd.read_excel("sales_raw_data.xlsx")

    # clean column
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(" ", "_")
        
    # map column
        if "Product_Name" in df.columns:
            df["Productname"] = df["Product_Name"]
        elif "ProductName" in df.columns:
            df["Productname"] = df["ProductName"]
        else:
            st.error("❌ ไม่เจอ Product column")
            st.stop()

        if "Sales_true" in df.columns:
            df["Sales"] = df["Sales_true"]

        if "Sales_pred" in df.columns:
            df["Prediction"] = df["Sales_pred"]

    # date
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
        df["Day"] = df["Date"].dt.day_name()
    # ---------- FILTER ----------

        st.sidebar.header("Filter")

        product_filter=st.sidebar.multiselect(
            "Product",
            df["Productname"].unique(),
            default=df["Productname"].unique()
        )

        weather_filter=st.sidebar.multiselect(
            "Weather",
            df["Weather"].dropna().unique(),
            default=df["Weather"].dropna().unique()
        )

        start=st.sidebar.date_input("Start Date",df["Date"].min())
        end=st.sidebar.date_input("End Date",df["Date"].max())

        data=df[
            (df["Productname"].isin(product_filter)) &
            (df["Weather"].isin(weather_filter)) &
            (df["Date"]>=pd.to_datetime(start)) &
            (df["Date"]<=pd.to_datetime(end))
        ]

        if len(data)==0:
            st.warning("No data available")
            st.stop()

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
            growth=((last-first)/first*100) if first!=0 else 0
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

    # ---------- WEATHER IMPACT ----------

    # ---------- WEATHER IMPACT (UPGRADE) ----------


        st.subheader("Weather Sales Analysis")

# ✅ CLEAN WEATHER (สำคัญมาก)
        data["Weather"] = data["Weather"].astype(str).str.strip()
        data["Weather"] = data["Weather"].replace("", "Unknown")
        data["Weather"] = data["Weather"].fillna("Unknown")

# ❗ กัน data ว่าง
        if data.empty:
            st.warning("No data available for Weather Analysis")
            st.stop()

# 🔥 group ยอดขายตามสภาพอากาศ
        weather_summary = data.groupby("Weather").agg({
            "Sales": ["sum", "mean", "count"]
        }).reset_index()

        weather_summary.columns = ["Weather", "Total Sales", "Avg Sales", "Days"]

# ❗ กัน groupby ว่าง
        if len(weather_summary) == 0:
            st.warning("No weather data to display")
            st.stop()

# ---------- KPI ----------
        w1, w2, w3 = st.columns(3)

        w1.metric("Total Weather Types", weather_summary.shape[0])

        best_weather = weather_summary.sort_values("Avg Sales", ascending=False).iloc[0]
        worst_weather = weather_summary.sort_values("Avg Sales").iloc[0]

        w2.metric("Best Weather (Avg)", best_weather["Weather"])
        w3.metric("Worst Weather (Avg)", worst_weather["Weather"])

# ---------- SORT ให้สวย ----------
        weather_summary = weather_summary.sort_values("Total Sales", ascending=False)

# ---------- BAR: TOTAL SALES ----------
        st.markdown("### Total Sales by Weather")

        fig_weather_total = px.bar(
            weather_summary,
            x="Weather",
            y="Total Sales",
            color="Weather"
        )

        st.plotly_chart(fig_weather_total, use_container_width=True)

# ---------- BAR: AVG SALES ----------
        st.markdown("### Average Sales per Day (Weather Impact)")

        fig_weather_avg = px.bar(
            weather_summary,
            x="Weather",
            y="Avg Sales",
            color="Weather"
        )

        st.plotly_chart(fig_weather_avg, use_container_width=True)

# ---------- TABLE ----------
        st.markdown("### Weather Data Table")
        st.dataframe(weather_summary)

# ---------- INSIGHT ----------
        st.markdown(f"""
        <div style="
        background-color:#e3f2fd;
        padding:20px;
        border-radius:10px;
        color:#0d47a1;
        font-size:16px;
        line-height:1.8;
        ">

        <b>Best Selling Weather :</b> {best_weather['Weather']}<br>
        <b>Average Sales :</b> €{best_weather['Avg Sales']:.2f}<br><br>

        <b>Worst Selling Weather :</b> {worst_weather['Weather']}<br>
        <b>Average Sales :</b> €{worst_weather['Avg Sales']:.2f}<br><br>

        <b>Insight :</b><br>
        - Weather has direct impact on customer behavior<br>
        - Use promotion strategy during low-performance weather<br>
        - Increase stock during high-demand weather

        </div>
        """, unsafe_allow_html=True)

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
        ).fillna(0)

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

    # ---------- BUSINESS INSIGHT (FIXED UI) ----------

        st.subheader("Business Insight")

        weather_col = data["Weather"].astype(str)

        rain_sales = data[weather_col.str.contains("ฝน", na=False)]["Sales"].mean()
        clear_sales = data[weather_col.str.contains("แจ่ม|clear", na=False)]["Sales"].mean()

        rain_sales = 0 if pd.isna(rain_sales) else rain_sales
        clear_sales = 0 if pd.isna(clear_sales) else clear_sales

        if rain_sales < clear_sales:
            insight_weather = "Rain reduces sales"
        else:
            insight_weather = "Rain increases sales"

        st.markdown(f"""
        <div style="
        background-color:#d4edda;
        padding:20px;
        border-radius:10px;
        color:#155724;
        font-size:16px;
        line-height:1.8;
        ">

        <b>Best Selling Product :</b> {best_product['Productname']}<br>
        <b>Lowest Selling Product :</b> {worst_product['Productname']}<br><br>

        <b>Recommendation :</b><br>
        - Increase production of {best_product['Productname']}<br>
        - Create promotion for {worst_product['Productname']}<br>
        - {insight_weather}

        </div>
        """, unsafe_allow_html=True)

# ================= UPLOAD PAGE =================
    # ================= UPLOAD PAGE (FULL DASHBOARD) =================

    if page == "Upload Excel":

        st.title("Upload Excel Sales Dashboard")

        file = st.file_uploader("Upload Excel", type=["xlsx"])

        if file:

        # ---------- LOAD ----------
            df = pd.read_excel(file)

        # ---------- CLEAN ----------
            df.columns = df.columns.str.strip()
            df.columns = df.columns.str.replace(" ", "_")

            df = df.rename(columns={
                "Product_Name": "Productname",
                "Sales_true": "Sales",
                "Sales_pred": "Prediction"
            })

            df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
            df["Weather"] = df["Weather"].astype(str).str.strip()

            df["Year"] = df["Date"].dt.year
            df["Month"] = df["Date"].dt.month
            df["Day"] = df["Date"].dt.day_name()

            st.success("Upload Successful")

        # ---------- FILTER ----------
            st.sidebar.header("Upload Filter")

            product_filter = st.sidebar.multiselect(
                "Product",
                df["Productname"].unique(),
                default=df["Productname"].unique()
            )

            weather_filter = st.sidebar.multiselect(
                "Weather",
                df["Weather"].dropna().unique(),
                default=df["Weather"].dropna().unique()
            )

            start = st.sidebar.date_input("Start Date", df["Date"].min())
            end = st.sidebar.date_input("End Date", df["Date"].max())

            data = df[
                (df["Productname"].isin(product_filter)) &
                (df["Weather"].isin(weather_filter)) &
                (df["Date"] >= pd.to_datetime(start)) &
                (df["Date"] <= pd.to_datetime(end))
            ]

            if len(data) == 0:
                st.warning("No data available")
                st.stop()

        # ---------- KPI ----------
            k1, k2, k3, k4 = st.columns(4)

            k1.metric("Total Sales", f"€{data['Sales'].sum():,.0f}")
            k2.metric("Records", len(data))
            k3.metric("Products", data["Productname"].nunique())
            k4.metric("Avg Sales", f"€{data['Sales'].mean():.2f}")

        # ---------- PRODUCT ----------
            product_sales = data.groupby("Productname")["Sales"].sum().reset_index()

            col1, col2 = st.columns(2)

            fig1 = px.pie(product_sales, names="Productname", values="Sales")
            col1.plotly_chart(fig1, use_container_width=True)

            fig2 = px.bar(product_sales, x="Productname", y="Sales", color="Productname")
            col2.plotly_chart(fig2, use_container_width=True)

        # ---------- WEATHER ----------
            st.subheader("Weather Impact")

            weather_sales = data.groupby("Weather")["Sales"].mean().reset_index()

            fig_weather = px.bar(
                weather_sales,
                x="Weather",
                y="Sales",
                color="Weather"
            )

            st.plotly_chart(fig_weather, use_container_width=True)

        # ---------- TREND ----------
            st.subheader("Sales Trend")

            trend = data.groupby("Date")["Sales"].sum().reset_index()

            fig3 = px.line(trend, x="Date", y="Sales")
            st.plotly_chart(fig3, use_container_width=True)

        # ---------- HEATMAP ----------
            st.subheader("Heatmap")

            heat = pd.pivot_table(
                data,
                values="Sales",
                index="Month",
                columns="Year",
                aggfunc="sum"
            ).fillna(0)

            fig6 = px.imshow(heat)
            st.plotly_chart(fig6, use_container_width=True)

        # ---------- TABLE ----------
            st.subheader("Data Table")

            st.dataframe(data)

            csv = data.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download Data",
                csv,
                "upload_data.csv",
                "text/csv"
            )

        # ---------- BUSINESS INSIGHT ----------
            st.subheader("Business Insight")

            best_product = product_sales.sort_values("Sales", ascending=False).iloc[0]
            worst_product = product_sales.sort_values("Sales").iloc[0]

            st.markdown(f"""
            <div style="
            background-color:#d4edda;
            padding:20px;
            border-radius:10px;
            color:#155724;
            font-size:16px;
            ">

            <b>Best Product :</b> {best_product['Productname']}<br>
            <b>Worst Product :</b> {worst_product['Productname']}<br><br>

            <b>Recommendation :</b><br>
            - Increase production of {best_product['Productname']}<br>
            - Promote {worst_product['Productname']}

            </div>
            """, unsafe_allow_html=True)
    

# ================= XGBOOST FORECAST =================
# ================= SALES FORECAST =================
# ================= XGBOOST FORECAST =================

    if page=="Sales Forecast":

        st.title("Sales Forecast (Machine Learning - XGBoost)")

    # ---------- LOAD DATA ----------
        sales_df = pd.read_excel("sales_raw_data.xlsx")

    # ---------- CLEAN ----------
        sales_df.columns = sales_df.columns.str.strip()
        sales_df.columns = sales_df.columns.str.replace(" ", "_")

    # ---------- MAP COLUMN ----------
        if "Product_Name" in sales_df.columns:
            sales_df["Productname"] = sales_df["Product_Name"]
        elif "ProductName" in sales_df.columns:
            sales_df["Productname"] = sales_df["ProductName"]
        elif "Productname" not in sales_df.columns:
            st.error("❌ ไม่เจอ Product column")
            st.write(sales_df.columns)
            st.stop()

        if "Sales_true" in sales_df.columns:
            sales_df["Sales"] = sales_df["Sales_true"]
        elif "Sales" not in sales_df.columns:
            st.error("❌ ไม่เจอ Sales column")
            st.stop()

        sales_df["Date"] = pd.to_datetime(sales_df["Date"], errors="coerce")

    # ---------- FILTER ----------
        st.sidebar.header("Forecast Filter")

        product_filter = st.sidebar.multiselect(
            "Product",
            sales_df["Productname"].dropna().unique(),
            default=sales_df["Productname"].dropna().unique()
        )

        start = st.sidebar.date_input("Start Date", sales_df["Date"].min())
        end = st.sidebar.date_input("End Date", sales_df["Date"].max())

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

    # ---------- ACTUAL ----------
        st.subheader("Actual Sales Trend")

        actual_trend = data.groupby("Date")["Sales"].sum().reset_index()
        fig1 = px.line(actual_trend, x="Date", y="Sales")
        fig1.update_layout(yaxis_tickprefix="€")
        st.plotly_chart(fig1,use_container_width=True)

    # =====================================================
    # 🤖 XGBOOST MODEL
    # =====================================================
        from xgboost import XGBRegressor
        import numpy as np

        st.subheader("Sales Forecast (2017-2019 Full Range)")

        forecast_list = []

        for product in product_filter:

            sub = data[data["Productname"] == product]
            daily = sub.groupby("Date")["Sales"].sum().reset_index()

            if len(daily) < 2:
                continue

        # ---------- FEATURE ----------
            daily["day"] = daily["Date"].dt.day
            daily["month"] = daily["Date"].dt.month
            daily["dow"] = daily["Date"].dt.dayofweek

            daily["lag1"] = daily["Sales"].shift(1)
            daily["lag7"] = daily["Sales"].shift(7)

            daily = daily.dropna()

            if len(daily) < 2:
                continue

            X = daily[["day","month","dow","lag1","lag7"]]
            y = daily["Sales"]

            model = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=5)
            model.fit(X,y)

        # ---------- FULL RANGE FORECAST ----------
            full_dates = pd.date_range(start="2017-01-01", end="2019-12-31")
            future = pd.DataFrame({"Date": full_dates})

            future["day"] = future["Date"].dt.day
            future["month"] = future["Date"].dt.month
            future["dow"] = future["Date"].dt.dayofweek

            last_sales = daily.set_index("Date")["Sales"].copy()

            preds = []

            for i in range(len(future)):

                current_date = future.iloc[i]["Date"]

                lag1 = last_sales.get(current_date - pd.Timedelta(days=1), last_sales.iloc[-1])
                lag7 = last_sales.get(current_date - pd.Timedelta(days=7), last_sales.iloc[-1])

                row = [[
                    future.iloc[i]["day"],
                    future.iloc[i]["month"],
                    future.iloc[i]["dow"],
                    lag1,
                    lag7
                ]]

                pred = model.predict(row)[0]

                preds.append(pred)
                last_sales.loc[current_date] = pred

            future["Sales_forecast"] = preds
            future["Productname"] = product

        # 🔥 สำคัญมาก (คุณลืมตรงนี้)
            forecast_list.append(future)

    # ---------- CHECK ----------
        if len(forecast_list) == 0:
            st.error("❌ Data not enough for forecasting")
            st.stop()

        forecast_data = pd.concat(forecast_list)

    # ---------- FORECAST GRAPH ----------
        fig2 = px.line(
            forecast_data,
            x="Date",
            y="Sales_forecast",
            color="Productname"
        )
        fig2.update_layout(yaxis_tickprefix="€")
        st.plotly_chart(fig2,use_container_width=True)

    # ---------- COMPARE ----------
        st.subheader("Actual vs Forecast")

        forecast_sum = forecast_data.groupby("Date")["Sales_forecast"].sum().reset_index()

        merged = pd.merge(
            actual_trend,
            forecast_sum,
            on="Date",
            how="outer"
        ).fillna(0)

        fig3 = px.line(merged, x="Date", y=["Sales","Sales_forecast"])
        fig3.update_layout(yaxis_tickprefix="€")
        st.plotly_chart(fig3,use_container_width=True)

    # ---------- TABLE ----------
        st.subheader("Forecast Data")
        st.dataframe(forecast_data)

        csv = forecast_data.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Forecast",
            csv,
            "forecast_xgboost.csv",
            "text/csv"
        )

    # ---------- INSIGHT ----------
        st.subheader("AI Insight")

        peak_row = forecast_data.sort_values("Sales_forecast", ascending=False).head(1)

        peak_date = pd.to_datetime(peak_row["Date"].values[0]).date()

        best_product = forecast_data.groupby("Productname")["Sales_forecast"].sum().idxmax()

        st.success(f"""
    🔥 Top product: {best_product}
    📈 Peak date: {peak_date}
    📦 Recommendation: Increase stock before peak
    """)

        st.caption("Model: XGBoost (lag1, lag7)")



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
