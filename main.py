import streamlit as st
import pandas as pd
import plotly.express as px
from plotly import graph_objects as go
from scipy.stats import chi2_contingency

tab1, tab2 = st.tabs(["Funnel Analysis", "A/B Testing Analysis"])

user = pd.read_csv("user_table.csv")
homepage = pd.read_csv("home_page_table.csv")
search = pd.read_csv("search_page_table.csv")
payment = pd.read_csv("payment_page_table.csv")
confirmation = pd.read_csv("payment_confirmation_table.csv")

# drop_by_step = pd.DataFrame([['Homepage',homepage['user_id'].count()],['Search',search['user_id'].count()],
#                              ['Payment',payment['user_id'].count()],['Confirmation',confirmation['user_id'].count()]],columns =['Step','Count'])
# #print(drop_by_step)


def clean_df(df):
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

homepage = clean_df(homepage).rename(columns={'page': 'Homepage'})
search = clean_df(search).rename(columns={'page': 'Search'})
payment = clean_df(payment).rename(columns={'page': 'Payment'})
confirmation = clean_df(confirmation).rename(columns={'page': 'Confirmation'})

#Merge all the tables

flow = user.merge(homepage, how='outer', on ='user_id').merge(search, how='outer', on='user_id').merge(payment,how='outer', on='user_id').merge(confirmation, how='outer', on='user_id')


mergedfile = pd.DataFrame(flow)
mergedfile.to_csv('merged.csv', index=False)

# funnel = {
#     'Homepage': flow['Homepage'].notna().sum(),
#     'Search': flow['Search'].notna().sum(),
#     'Payment': flow['Payment'].notna().sum(),
#     'Confirmation':flow['Confirmation'].notna().sum()
# }

#print(funnel)

# Funnel by gender (counting non-null steps)
# funnel_by_gender = flow.groupby('sex').agg({
#     'Homepage': lambda x: x.notna().sum(),
#     'Search': lambda x: x.notna().sum(),
#     'Payment': lambda x: x.notna().sum(),
#     'Confirmation': lambda x: x.notna().sum()
# }).reset_index()
#
# funnel_by_device = flow.groupby('device').agg({
#     'Homepage': lambda x: x.notna().sum(),
#     'Search': lambda x: x.notna().sum(),
#     'Payment': lambda x: x.notna().sum(),
#     'Confirmation': lambda x: x.notna().sum()
# }).reset_index()

#print(funnel_by_device)

#################################################



st.set_page_config(layout="wide")

# Set funnel steps globally
funnel_steps = ["Homepage", "Search", "Payment", "Confirmation"]

with tab1:
    st.title("User Funnel Analysis")
    col1, col2 = st.columns([3, 1], gap="large")

    with col2:
        st.markdown("""
            <style>
            div[data-testid="column"]:nth-of-type(2) > div {
                position: sticky;
                top: 1rem;
                background-color: #f9f9f9;
                padding: 1rem;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                z-index: 999;
            }
            </style>
        """, unsafe_allow_html=True)

        st.subheader("Filters")
        gender_filter = st.multiselect(
            "Select Gender",
            options=flow['sex'].dropna().unique(),
            default=flow['sex'].dropna().unique()
        )
        device_filter = st.multiselect(
            "Select Device",
            options=flow['device'].dropna().unique(),
            default=flow['device'].dropna().unique()
        )
    with col1:
        filtered_flow = flow[
            (flow['sex'].isin(gender_filter)) &
            (flow['device'].isin(device_filter))
        ]

        # Calculate unique users at each step
        home_users = filtered_flow[filtered_flow['Homepage'] == 'home_page']['user_id'].nunique()
        payment_users = filtered_flow[filtered_flow['Payment'] == 'payment_page']['user_id'].nunique()
        confirmation_users = filtered_flow[filtered_flow['Confirmation'] == 'payment_confirmation_page']['user_id'].nunique()

        # Safeguard against division by zero
        conv_home_to_payment = (payment_users / home_users * 100) if home_users else 0
        conv_home_to_confirm = (confirmation_users / home_users * 100) if home_users else 0
        conv_payment_to_confirm = (confirmation_users / payment_users * 100) if payment_users else 0

        # Show metrics as cards
        st.markdown("### Conversion Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Home → Confirm", f"{conv_home_to_confirm:.2f}%")
        col2.metric("Home → Payment", f"{conv_home_to_payment:.2f}%")
        col3.metric("Payment → Confirm", f"{conv_payment_to_confirm:.2f}%")


        def plot_funnel(x_values, title):
            fig = go.Figure(go.Funnel(
                y = funnel_steps,
                x = x_values,
                textposition = "inside",
                textinfo = "value+percent initial",
                marker={"color": ["#0E76A8", "#1DA1F2", "#17BECF", "#2CA02C"]}
            ))
            fig.update_layout(title=title, margin=dict(l=60, r=60, t=50, b=40))
            st.plotly_chart(fig, use_container_width=True)

        # 🔹 Overall Funnel (Filtered)
        st.subheader("Overall Funnel")
        overall_counts = [filtered_flow[step].notna().sum() for step in funnel_steps]
        plot_funnel(overall_counts, "Overall Funnel")

        # 🔹 Funnel by Gender (One Chart with Both Male & Female)

        st.subheader("Funnel by Gender")

        gender_list = filtered_flow['sex'].dropna().unique()

        fig_gender = go.Figure()

        colors = {
            "Male": "#1f77b4",
            "Female": "#ff7f0e",
            # Add more if needed
        }

        for gender in gender_list:
            gender_df = filtered_flow[filtered_flow['sex'] == gender]
            counts = [gender_df[step].notna().sum() for step in funnel_steps]
            fig_gender.add_trace(go.Funnel(
                name=str(gender),
                y=funnel_steps,
                x=counts,
                textinfo="value+percent initial",
                marker={"color": colors.get(str(gender), "#636EFA")}  # default if color not found
            ))

        fig_gender.update_layout(title="Funnel by Gender (Side-by-side)", margin=dict(l=60, r=60, t=50, b=40))
        st.plotly_chart(fig_gender, use_container_width=True)


        # 🔹 Funnel by Device (One Chart with All Device Types)

        st.subheader("Funnel by Device")

        device_list = filtered_flow['device'].dropna().unique()

        fig_device = go.Figure()

        device_colors = {
            "Mobile": "#2ca02c",
            "Desktop": "#d62728",
            # Add more if needed
        }

        for device in device_list:
            device_df = filtered_flow[filtered_flow['device'] == device]
            counts = [device_df[step].notna().sum() for step in funnel_steps]
            fig_device.add_trace(go.Funnel(
                name=str(device),
                y=funnel_steps,
                x=counts,
                textinfo="value+percent initial",
                marker={"color": device_colors.get(str(device), "#9467bd")}
            ))

        st.plotly_chart(fig_device, use_container_width=True)
        fig_device.update_layout(title="Funnel by Device (Side-by-side)", margin=dict(l=60, r=60, t=50, b=40))


    st.set_page_config(layout="wide")

###############################################################
###############################################################
###############################################################
###############################################################

with tab2:
    st.title("A/B Testing Analysis")

    col1, col2 = st.columns([3, 1])

    # Right Column – Filters
    with col2:
        selected_device = st.multiselect("Device", options=flow['device'].unique(), default=flow['device'].unique())
        selected_sex = st.multiselect("Gender", options=flow['sex'].unique(), default=flow['sex'].unique())

    # Apply filters
    flow_ab = flow[
        (flow['device'].isin(selected_device)) &
        (flow['sex'].isin(selected_sex))
    ]

    with col1:

        # --- Pie Chart: Source of Confirmations (A vs B) ---
        confirmations_by_version = flow_ab[flow_ab['Confirmation'].notna()].groupby('version')['user_id'].nunique().reset_index()
        confirmations_by_version.columns = ['version', 'Confirmed Users']

        fig_pie = px.pie(
            confirmations_by_version,
            names='version',
            values='Confirmed Users',
            title='Distribution of Confirmations by Version (A vs B)',
            hole=0.4
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)


        # --- Overall A vs B Conversion Rate ---
        ab_overall_df = flow_ab[flow_ab['Payment'].notna()].copy()
        ab_overall_df['converted'] = ab_overall_df['Confirmation'].notna()

        ab_overall_summary = ab_overall_df.groupby('version')['converted'].agg(['mean', 'count']).reset_index()
        ab_overall_summary.rename(columns={'mean': 'Conversion Rate', 'count': 'Sample Size'}, inplace=True)

        fig_overall = px.bar(
            ab_overall_summary,
            x='version',
            y='Conversion Rate',
            color='version',
            title='Overall Conversion Rate: Payments → Confirmation (A vs B)',
            text=ab_overall_summary['Conversion Rate'].apply(lambda x: f"{x:.2%}")
        )
        fig_overall.update_traces(textposition='outside')
        fig_overall.update_layout(showlegend=False)
        st.plotly_chart(fig_overall, use_container_width=True)

        # --- Gender-wise Conversion ---
        ab_gender_df = flow_ab[flow_ab['Payment'].notna()].copy()
        ab_gender_df['converted'] = ab_gender_df['Confirmation'].notna()

        ab_gender_summary = ab_gender_df.groupby(['version', 'sex'])['converted'].agg(['mean', 'count']).reset_index()
        ab_gender_summary.rename(columns={'mean': 'Conversion Rate', 'count': 'Sample Size'}, inplace=True)

        fig_gender = px.bar(
            ab_gender_summary,
            x='sex',
            y='Conversion Rate',
            color='version',
            barmode='group',
            title='A/B Test: Payments → Confirmation by Gender'
        )
        st.plotly_chart(fig_gender, use_container_width=True)

        # --- Device-wise Conversion ---
        ab_device_df = flow_ab[flow_ab['Payment'].notna()].copy()
        ab_device_df['converted'] = ab_device_df['Confirmation'].notna()

        ab_device_summary = ab_device_df.groupby(['version', 'device'])['converted'].agg(['mean', 'count']).reset_index()
        ab_device_summary.rename(columns={'mean': 'Conversion Rate', 'count': 'Sample Size'}, inplace=True)

        fig_device = px.bar(
            ab_device_summary,
            x='device',
            y='Conversion Rate',
            color='version',
            barmode='group',
            title='A/B Test: Payments → Confirmation by Device'
        )
        st.plotly_chart(fig_device, use_container_width=True)


        # Step 1: Create a contingency table
        contingency_table = pd.crosstab(
            flow_ab['version'],
            flow_ab['Confirmation'].notna()
        )

        # Step 2: Perform the Chi-Square test
        chi2, p_val, dof, expected = chi2_contingency(contingency_table)

        # Step 3: Display the result
        st.write("### Chi-Square Test for Version vs Confirmation")
        st.write(f"Chi-square Statistic: {chi2:.4f}")
        st.write(f"P-value: {p_val:.4f}")
        if p_val < 0.05:
            st.success("Result: Statistically significant difference in confirmation rates between A and B (p < 0.05)")
        else:
            st.info("Result: No statistically significant difference in confirmation rates between A and B (p ≥ 0.05)")

