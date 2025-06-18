import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

# Configure the page
st.set_page_config(
    page_title="NCAT Operations Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication function
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("dashboard_password", "ncat2024admin"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.markdown("### 🔐 NCAT Dashboard Access")
        st.markdown("This dashboard contains sensitive tribunal data. Please enter the access password.")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.info("💡 Contact the administrator for access credentials.")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.markdown("### 🔐 NCAT Dashboard Access")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😞 Password incorrect. Please try again.")
        return False
    else:
        # Password correct.
        return True

# Check authentication before showing the dashboard
if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Add logout button in sidebar
if st.sidebar.button("🚪 Logout"):
    st.session_state["password_correct"] = False
    st.rerun()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    .sidebar .sidebar-content {
        background-color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# Data definitions
@st.cache_data
def load_data():
    # Annual Tenancy Applications Data
    tenancy_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Total_Applications': [7173, 27954, 29780, 28849, 29167, 29905, 29798, 32654, 27720, 27873, 7496],
        'Data_Completeness': ['Q4 Only', 'Q2, Q3, Q4', 'Full Year', 'Full Year', 'Full Year', 'Full Year', 'Full Year', 'Full Year', 'Full Year', 'Full Year', 'Q1 Only']
    }
    
    # Tenancy Applications by Category (Updated with granular data from Table 2.2)
    category_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Termination_NonPayment': [2981, 11646, 15224, 14380, 13695, 10462, 9851, 10833, 10599, 9108, 2731],
        'Rental_Bonds': [1236, 4190, 4787, 4747, 4809, 5403, 5219, 5477, 5460, 6879, 1668],
        'General_Orders': [1276, 5325, 5618, 5344, 5806, 6388, 6407, 6871, 5571, 2623, 515],
        'Repairs': [101, 268, 351, 308, 320, 394, 464, 464, 479, 1128, 278],
        'Rent_Other_Payments': [375, 740, 768, 699, 717, 900, 947, 1153, 1373, 3796, 886],
        'Termination_Breach_s87': [None, 734, 845, 690, 660, 614, 700, 765, 744, None, None],
        'Termination_CoTenant_s102': [None, 60, 74, 88, 47, 74, 64, 54, 48, None, None],
        'Termination_Other': [1030, 2791, 3589, 3148, 3323, 4535, 5119, 5340, 5110, 4418, 1247]
    }
    
    # Lodgements by Party
    party_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Landlord': [5634, 20662, 23476, 22545, 22448, 20816, 23284, 23265, 21512, 18367, 5256],
        'Tenant': [1387, 5562, 6304, 6304, 6719, 7568, 6514, 7995, 6208, 7505, 1950],
        'Other': [152, 1730, None, None, None, 1521, None, 1394, None, 2001, 290]
    }
    
    # Geographic Distribution (Private Tenancy)
    geo_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [1226, 4049, 5993, 5887, 5994, 6140, 5972, 6607, 6574, 5599, 1820],
        'Newcastle': [1273, 3768, 5026, 4913, 4610, 4182, 4485, 4424, 4289, 3844, 1161],
        'Penrith': [1206, 3830, 5892, 5868, 6076, 5533, 4311, 4241, 4135, 3148, 869],
        'Sydney': [1902, 5845, 8429, 7953, 8064, 11122, 11080, 12768, 10885, 11483, 2963],
        'Tamworth': [633, 1825, 2217, 2182, 2060, 1643, 2080, 2017, 1845, 1661, 482],
        'Wollongong': [664, 1939, 2502, 2442, 2435, 1930, 2465, 2425, 2240, 2138, 538]
    }
    
    # Other NCAT Lists Data
    other_lists_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Tenancy': [7173, 27954, 29780, 28849, 29167, 29905, 29798, 32654, 27720, 27873, 7496],
        'Social_Housing': [3405, 10448, 12588, 12702, 12782, 9682, 11126, 13001, 12002, 12277, 3507],
        'General': [1334, 4204, 5103, 4632, 4550, 4895, 4492, 4948, 4961, 4855, 1165],
        'Home_Building': [693, 2300, 2860, 2870, 2943, 2874, 2980, 3806, 3807, 2983, 497],
        'Strata_Schemes': [384, 1125, 736, 1192, 1328, 1609, 1498, 1612, 1490, 1417, 298],
        'Motor_Vehicles': [365, 1218, 1636, 1504, 1531, 1585, 1704, 1735, 1738, 1605, 351]
    }
    
    # Total CCD Applications by Registry
    total_ccd_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [2182, 6751, 9938, 9845, 9820, 8463, 8146, 9481, 9564, 9315, 2721],
        'Newcastle': [2567, 6897, 9326, 9143, 8750, 7064, 7691, 8368, 8414, 7837, 2359],
        'Penrith': [2194, 6598, 10020, 10253, 10651, 8690, 7085, 7353, 6761, 5950, 2900],
        'Sydney': [3755, 11711, 15869, 15494, 15664, 21122, 21020, 22424, 19934, 20202, 4305],
        'Tamworth': [1345, 3600, 4607, 4613, 4570, 3890, 4707, 4710, 4606, 4501, 1247],
        'Wollongong': [1425, 4162, 5216, 5362, 5523, 4489, 4981, 5127, 5094, 4950, 1427]
    }
    
    # Social Housing by Registry
    social_housing_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [613, 1767, 2469, 2538, 2472, 1566, 1731, 1954, 2094, 2002, 562],
        'Newcastle': [766, 1805, 2475, 2168, 2272, 1545, 2030, 2382, 2264, 2089, 513],
        'Penrith': [503, 1409, 2209, 2279, 2441, 1875, 1580, 1612, 1436, 1159, 398],
        'Sydney': [570, 1640, 2612, 2397, 2433, 1955, 2800, 2962, 2922, 2847, 777],
        'Tamworth': [499, 1222, 1651, 1521, 1433, 1424, 1635, 1962, 2027, 1980, 670],
        'Wollongong': [454, 1240, 1647, 1715, 1772, 1317, 1350, 1883, 1838, 1900, 587]
    }
    
    # General List by Registry
    general_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [143, 478, 602, 578, 542, 550, 595, 602, 616, 662, 155],
        'Newcastle': [174, 566, 619, 640, 588, 566, 682, 706, 651, 658, 177],
        'Penrith': [228, 624, 861, 819, 783, 717, 628, 528, 470, 405, 110],
        'Sydney': [557, 1833, 2123, 1911, 1850, 2188, 1976, 2158, 2230, 2289, 570],
        'Tamworth': [92, 239, 261, 250, 228, 333, 332, 304, 256, 249, 59],
        'Wollongong': [140, 351, 401, 434, 428, 501, 485, 420, 399, 432, 94]
    }
    
    # Home Building by Registry
    home_building_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [81, 266, 359, 358, 401, 370, 384, 457, 467, 396, 61],
        'Newcastle': [94, 291, 381, 420, 428, 416, 457, 526, 546, 458, 90],
        'Penrith': [121, 421, 501, 483, 526, 462, 339, 387, 367, 288, 56],
        'Sydney': [273, 895, 1061, 1064, 1146, 1099, 1161, 1345, 1558, 1181, 205],
        'Tamworth': [50, 149, 178, 172, 167, 163, 181, 172, 185, 142, 33],
        'Wollongong': [74, 226, 269, 305, 275, 302, 334, 297, 334, 310, 52]
    }
    
    # Strata Schemes by Registry
    strata_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [35, 98, 67, 79, 95, 129, 123, 118, 131, 136, 34],
        'Newcastle': [34, 96, 94, 89, 105, 136, 136, 119, 118, 109, 18],
        'Penrith': [28, 58, 64, 56, 60, 74, 57, 47, 51, 48, 16],
        'Sydney': [245, 797, 630, 892, 981, 1131, 1086, 1108, 1039, 1051, 206],
        'Tamworth': [15, 37, 45, 45, 42, 55, 46, 46, 52, 49, 14],
        'Wollongong': [27, 73, 50, 50, 61, 63, 78, 75, 61, 53, 10]
    }
    
    # Motor Vehicles by Registry
    motor_vehicles_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [71, 263, 324, 321, 331, 298, 308, 309, 325, 335, 75],
        'Newcastle': [46, 170, 223, 215, 210, 206, 206, 234, 233, 225, 60],
        'Penrith': [78, 256, 331, 341, 367, 345, 345, 256, 221, 216, 31],
        'Sydney': [97, 360, 462, 453, 461, 471, 483, 524, 527, 489, 127],
        'Tamworth': [32, 83, 115, 116, 115, 109, 108, 100, 105, 104, 22],
        'Wollongong': [41, 100, 133, 138, 122, 106, 122, 118, 117, 121, 36]
    }
    
    # Commercial by Registry
    commercial_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [10, 51, 74, 72, 63, 67, 66, 72, 82, 86, 24],
        'Newcastle': [29, 70, 110, 115, 121, 101, 90, 104, 118, 129, 39],
        'Penrith': [27, 67, 85, 90, 86, 98, 72, 60, 63, 64, 10],
        'Sydney': [104, 331, 430, 420, 415, 430, 391, 394, 366, 372, 83],
        'Tamworth': [9, 49, 67, 72, 60, 49, 56, 55, 64, 60, 13],
        'Wollongong': [18, 58, 74, 77, 82, 85, 66, 70, 74, 81, 25]
    }
    
    # Residential Communities by Registry
    residential_communities_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [2, 5, 5, 10, 25, 14, 20, 17, 15, 15, 9],
        'Newcastle': [40, 94, 109, 164, 244, 104, 169, 129, 114, 91, 129],
        'Penrith': [1, 11, 8, 71, 95, 30, 19, 25, 16, 18, 3],
        'Sydney': [3, 18, 31, 24, 31, 20, 39, 40, 54, 65, 17],
        'Tamworth': [12, 41, 53, 96, 239, 101, 108, 88, 81, 53, 8],
        'Wollongong': [2, 59, 70, 57, 129, 61, 74, 127, 61, 43, 9]
    }
    
    # Retirement Villages by Registry
    retirement_villages_data = {
        'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        'Liverpool': [1, 1, 4, 3, 4, 6, 2, 2, 1, 1, 1],
        'Newcastle': [2, 18, 24, 27, 24, 26, 23, 18, 19, 20, 2],
        'Penrith': [0, 9, 3, 7, 5, 4, 3, 4, 2, 1, 0],
        'Sydney': [4, 12, 14, 13, 15, 19, 19, 22, 16, 15, 0],
        'Tamworth': [1, 3, 2, 1, 1, 4, 3, 4, 1, 5, 4],
        'Wollongong': [0, 7, 7, 5, 7, 4, 5, 5, 12, 5, 2]
    }
    
    # Party Category Data - Landlord vs Tenant breakdown by application type
    party_category_data = []
    
    # 2017 data
    party_category_data.extend([
        {'Year': 2017, 'Category': 'Rental Bonds', 'Landlord': 1527, 'Tenant': 3117, 'Total': 4787},
        {'Year': 2017, 'Category': 'General Orders', 'Landlord': 3411, 'Tenant': 1872, 'Total': 5618},
        {'Year': 2017, 'Category': 'Rent and other payments', 'Landlord': 380, 'Tenant': 355, 'Total': 768},
        {'Year': 2017, 'Category': 'Repairs', 'Landlord': 6, 'Tenant': 329, 'Total': 351},
        {'Year': 2017, 'Category': 'Termination - Breach (s.87)', 'Landlord': 845, 'Tenant': 0, 'Total': 845},
        {'Year': 2017, 'Category': 'Termination non-payment of rent', 'Landlord': 15224, 'Tenant': 0, 'Total': 15224},
        {'Year': 2017, 'Category': 'Termination by co-tenant (s102)', 'Landlord': 0, 'Tenant': 74, 'Total': 74},
        {'Year': 2017, 'Category': 'Termination - Other', 'Landlord': 2506, 'Tenant': 1023, 'Total': 3589}
    ])
    
    # 2018 data
    party_category_data.extend([
        {'Year': 2018, 'Category': 'Rental bonds', 'Landlord': 1496, 'Tenant': 3124, 'Total': 4747},
        {'Year': 2018, 'Category': 'General orders', 'Landlord': 3292, 'Tenant': 1746, 'Total': 5344},
        {'Year': 2018, 'Category': 'Rent and other payments', 'Landlord': 332, 'Tenant': 322, 'Total': 699},
        {'Year': 2018, 'Category': 'Repairs', 'Landlord': 0, 'Tenant': 284, 'Total': 308},
        {'Year': 2018, 'Category': 'Termination - breach (s.87)', 'Landlord': 690, 'Tenant': 0, 'Total': 690},
        {'Year': 2018, 'Category': 'Termination - non-payment of rent', 'Landlord': 14380, 'Tenant': 0, 'Total': 14380},
        {'Year': 2018, 'Category': 'Termination by co-tenant (s102)', 'Landlord': 0, 'Tenant': 88, 'Total': 88},
        {'Year': 2018, 'Category': 'Termination - other', 'Landlord': 2303, 'Tenant': 798, 'Total': 3148}
    ])
    
    # 2019 data
    party_category_data.extend([
        {'Year': 2019, 'Category': 'Rental bonds', 'Landlord': 1483, 'Tenant': 3194, 'Total': 4809},
        {'Year': 2019, 'Category': 'General orders', 'Landlord': 3615, 'Tenant': 1870, 'Total': 5806},
        {'Year': 2019, 'Category': 'Rent and other payments', 'Landlord': 304, 'Tenant': 367, 'Total': 717},
        {'Year': 2019, 'Category': 'Repairs', 'Landlord': 0, 'Tenant': 293, 'Total': 320},
        {'Year': 2019, 'Category': 'Termination - breach (s.87)', 'Landlord': 660, 'Tenant': 0, 'Total': 660},
        {'Year': 2019, 'Category': 'Termination - non-payment of rent', 'Landlord': 13695, 'Tenant': 0, 'Total': 13695},
        {'Year': 2019, 'Category': 'Termination by co-tenant (s102)', 'Landlord': 0, 'Tenant': 47, 'Total': 47},
        {'Year': 2019, 'Category': 'Termination - other', 'Landlord': 2274, 'Tenant': 993, 'Total': 3323}
    ])
    
    # 2020 data
    party_category_data.extend([
        {'Year': 2020, 'Category': 'Rental Bonds', 'Landlord': 1694, 'Tenant': 3504, 'Total': 5403},
        {'Year': 2020, 'Category': 'General Orders', 'Landlord': 3935, 'Tenant': 2095, 'Total': 6388},
        {'Year': 2020, 'Category': 'Rent and other payments', 'Landlord': 360, 'Tenant': 490, 'Total': 900},
        {'Year': 2020, 'Category': 'Repairs', 'Landlord': 0, 'Tenant': 366, 'Total': 394},
        {'Year': 2020, 'Category': 'Termination - Breach (s 87)', 'Landlord': 614, 'Tenant': 0, 'Total': 614},
        {'Year': 2020, 'Category': 'Termination non-payment of rent', 'Landlord': 10462, 'Tenant': 0, 'Total': 10462},
        {'Year': 2020, 'Category': 'Termination by a co-tenant (s 102)', 'Landlord': 0, 'Tenant': 74, 'Total': 74},
        {'Year': 2020, 'Category': 'Termination - Other', 'Landlord': 3067, 'Tenant': 1386, 'Total': 4535}
    ])
    
    # 2021 data
    party_category_data.extend([
        {'Year': 2021, 'Category': 'Rental Bonds', 'Landlord': 1664, 'Tenant': 3363, 'Total': 5219},
        {'Year': 2021, 'Category': 'General Orders', 'Landlord': 3988, 'Tenant': 2080, 'Total': 6407},
        {'Year': 2021, 'Category': 'Rent and other payments', 'Landlord': 416, 'Tenant': 479, 'Total': 947},
        {'Year': 2021, 'Category': 'Repairs', 'Landlord': 0, 'Tenant': 430, 'Total': 464},
        {'Year': 2021, 'Category': 'Termination - Breach (s 87)', 'Landlord': 700, 'Tenant': 0, 'Total': 700},
        {'Year': 2021, 'Category': 'Termination non-payment of rent', 'Landlord': 9851, 'Tenant': 0, 'Total': 9851},
        {'Year': 2021, 'Category': 'Termination by a co-tenant (s 102)', 'Landlord': 0, 'Tenant': 64, 'Total': 64},
        {'Year': 2021, 'Category': 'Termination - Other', 'Landlord': 3501, 'Tenant': 1530, 'Total': 5119}
    ])
    
    # 2022 data
    party_category_data.extend([
        {'Year': 2022, 'Category': 'Rental Bonds', 'Landlord': 1771, 'Tenant': 3456, 'Total': 5477},
        {'Year': 2022, 'Category': 'General Orders', 'Landlord': 4303, 'Tenant': 2193, 'Total': 6871},
        {'Year': 2022, 'Category': 'Rent and other payments', 'Landlord': 480, 'Tenant': 608, 'Total': 1153},
        {'Year': 2022, 'Category': 'Repairs', 'Landlord': 0, 'Tenant': 435, 'Total': 464},
        {'Year': 2022, 'Category': 'Termination - Breach (s 87)', 'Landlord': 765, 'Tenant': 0, 'Total': 765},
        {'Year': 2022, 'Category': 'Termination non-payment of rent', 'Landlord': 10833, 'Tenant': 0, 'Total': 10833},
        {'Year': 2022, 'Category': 'Termination by a co-tenant (s 102)', 'Landlord': 0, 'Tenant': 54, 'Total': 54},
        {'Year': 2022, 'Category': 'Termination - Other', 'Landlord': 3677, 'Tenant': 1559, 'Total': 5340}
    ])
    
    # 2023 data
    party_category_data.extend([
        {'Year': 2023, 'Category': 'Rental Bonds', 'Landlord': 1708, 'Tenant': 3555, 'Total': 5460},
        {'Year': 2023, 'Category': 'General Orders', 'Landlord': 3454, 'Tenant': 1831, 'Total': 5571},
        {'Year': 2023, 'Category': 'Rent and other payments', 'Landlord': 752, 'Tenant': 546, 'Total': 1373},
        {'Year': 2023, 'Category': 'Repairs', 'Landlord': 116, 'Tenant': 328, 'Total': 479},
        {'Year': 2023, 'Category': 'Termination - Breach (s 87)', 'Landlord': 744, 'Tenant': 0, 'Total': 744},
        {'Year': 2023, 'Category': 'Termination non-payment of rent', 'Landlord': 10599, 'Tenant': 0, 'Total': 10599},
        {'Year': 2023, 'Category': 'Termination by a co-tenant (s 102)', 'Landlord': 0, 'Tenant': 48, 'Total': 48},
        {'Year': 2023, 'Category': 'Termination - Other', 'Landlord': 3513, 'Tenant': 1455, 'Total': 5110}
    ])
    
    # 2024 data
    party_category_data.extend([
        {'Year': 2024, 'Category': 'Rental Bonds', 'Landlord': 2938, 'Tenant': 3745, 'Total': 6879},
        {'Year': 2024, 'Category': 'General Orders', 'Landlord': 1521, 'Tenant': 937, 'Total': 2623},
        {'Year': 2024, 'Category': 'Rent and other payments', 'Landlord': 2249, 'Tenant': 1379, 'Total': 3796},
        {'Year': 2024, 'Category': 'Repairs', 'Landlord': 416, 'Tenant': 668, 'Total': 1128},
        {'Year': 2024, 'Category': 'Termination non-payment of rent', 'Landlord': 8512, 'Tenant': 106, 'Total': 9108},
        {'Year': 2024, 'Category': 'Termination other', 'Landlord': 3714, 'Tenant': 534, 'Total': 4418}
    ])
    
    # Convert to DataFrames
    df_tenancy = pd.DataFrame(tenancy_data)
    df_categories = pd.DataFrame(category_data)
    df_parties = pd.DataFrame(party_data)
    df_geo = pd.DataFrame(geo_data)
    df_other_lists = pd.DataFrame(other_lists_data)
    df_total_ccd = pd.DataFrame(total_ccd_data)
    df_social_housing = pd.DataFrame(social_housing_data)
    df_general = pd.DataFrame(general_data)
    df_home_building = pd.DataFrame(home_building_data)
    df_strata = pd.DataFrame(strata_data)
    df_motor_vehicles = pd.DataFrame(motor_vehicles_data)
    df_commercial = pd.DataFrame(commercial_data)
    df_residential_communities = pd.DataFrame(residential_communities_data)
    df_retirement_villages = pd.DataFrame(retirement_villages_data)
    df_party_categories = pd.DataFrame(party_category_data)
    
    return (df_tenancy, df_categories, df_parties, df_geo, df_other_lists, df_total_ccd, 
            df_social_housing, df_general, df_home_building, df_strata, df_motor_vehicles, 
            df_commercial, df_residential_communities, df_retirement_villages, df_party_categories)

# Load data
(df_tenancy, df_categories, df_parties, df_geo, df_other_lists, df_total_ccd, 
 df_social_housing, df_general, df_home_building, df_strata, df_motor_vehicles, 
 df_commercial, df_residential_communities, df_retirement_villages, df_party_categories) = load_data()

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["🏠 Overview", "📈 Tenancy Trends", "🏢 Application Categories", "👥 Party Analysis", "📋 Detailed Party Breakdown", "🗺️ Geographic Distribution", "⚖️ NCAT Lists Comparison"]
)

# Main title
st.markdown('<h1 class="main-header">⚖️ NCAT Operations Dashboard</h1>', unsafe_allow_html=True)

if page == "🏠 Overview":
    st.header("Executive Summary")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_apps_2024 = df_tenancy[df_tenancy['Year'] == 2024]['Total_Applications'].iloc[0]
        st.metric("2024 Tenancy Applications", f"{total_apps_2024:,}")
    
    with col2:
        peak_year = df_tenancy.loc[df_tenancy['Total_Applications'].idxmax(), 'Year']
        peak_value = df_tenancy['Total_Applications'].max()
        st.metric("Peak Year", f"{peak_year} ({peak_value:,})")
    
    with col3:
        avg_apps = df_tenancy[df_tenancy['Year'].between(2017, 2024)]['Total_Applications'].mean()
        st.metric("Annual Average (2017-2024)", f"{avg_apps:,.0f}")
    
    with col4:
        growth_rate = ((total_apps_2024 - df_tenancy[df_tenancy['Year'] == 2017]['Total_Applications'].iloc[0]) / 
                      df_tenancy[df_tenancy['Year'] == 2017]['Total_Applications'].iloc[0]) * 100
        st.metric("Growth 2017-2024", f"{growth_rate:.1f}%")
    
    # Overview chart
    fig = px.line(df_tenancy[df_tenancy['Year'].between(2017, 2024)], 
                  x='Year', y='Total_Applications',
                  title='Total Tenancy Applications Over Time (2017-2024)',
                  markers=True)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Key insights
    st.subheader("Key Insights")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📊 Volume Trends:**
        - Tenancy applications peaked in 2022 with 32,654 cases
        - Consistent high volume averaging ~29,000 annually
        - Slight decline in 2023-2024 but still substantial
        """)
    
    with col2:
        st.info("""
        **🏢 Business Impact:**
        - Tenancy matters represent >50% of CCD workload
        - Core business function requiring dedicated resources
        - Sensitive to economic conditions (COVID-19 impact visible)
        """)

elif page == "📈 Tenancy Trends":
    st.header("Tenancy Application Trends")
    
    # Year filter
    year_range = st.slider("Select Year Range", 
                          min_value=2017, max_value=2024, 
                          value=(2017, 2024))
    
    filtered_df = df_tenancy[df_tenancy['Year'].between(year_range[0], year_range[1])]
    
    # Main trends chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=filtered_df['Year'], y=filtered_df['Total_Applications'],
                            mode='lines+markers', name='Total Applications',
                            line=dict(width=3), marker=dict(size=8)))
    
    fig.update_layout(
        title='Tenancy Applications Trend',
        xaxis_title='Year',
        yaxis_title='Number of Applications',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Annual change analysis
    st.subheader("Year-over-Year Changes")
    
    # Calculate percentage changes
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['YoY_Change'] = filtered_df_copy['Total_Applications'].pct_change() * 100
    filtered_df_copy['YoY_Absolute'] = filtered_df_copy['Total_Applications'].diff()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_change = px.bar(filtered_df_copy[1:], x='Year', y='YoY_Change',
                           title='Year-over-Year Percentage Change',
                           color='YoY_Change',
                           color_continuous_scale='RdBu_r')
        fig_change.update_layout(height=300)
        st.plotly_chart(fig_change, use_container_width=True)
    
    with col2:
        fig_abs = px.bar(filtered_df_copy[1:], x='Year', y='YoY_Absolute',
                        title='Year-over-Year Absolute Change',
                        color='YoY_Absolute',
                        color_continuous_scale='RdBu_r')
        fig_abs.update_layout(height=300)
        st.plotly_chart(fig_abs, use_container_width=True)

elif page == "🏢 Application Categories":
    st.header("Application Categories Analysis (Detailed Breakdown)")
    
    # Data preparation for categories
    df_cat_melted = df_categories.melt(id_vars=['Year'], 
                                      value_vars=['Termination_NonPayment', 'Rental_Bonds', 'General_Orders', 'Repairs', 
                                                'Rent_Other_Payments', 'Termination_Breach_s87', 'Termination_CoTenant_s102', 'Termination_Other'],
                                      var_name='Category', value_name='Applications')
    df_cat_melted = df_cat_melted.dropna()
    
    # Category names mapping
    category_mapping = {
        'Termination_NonPayment': 'Termination (Non-Payment)',
        'Rental_Bonds': 'Rental Bonds',
        'General_Orders': 'General Orders',
        'Repairs': 'Repairs',
        'Rent_Other_Payments': 'Rent & Other Payments',
        'Termination_Breach_s87': 'Termination (Breach s.87)',
        'Termination_CoTenant_s102': 'Termination (Co-Tenant s.102)',
        'Termination_Other': 'Termination (Other)'
    }
    df_cat_melted['Category'] = df_cat_melted['Category'].map(category_mapping)
    
    # Category selection
    col1, col2 = st.columns(2)
    
    with col1:
        # Year filter
        selected_years = st.multiselect("Select Years to Compare", 
                                       sorted(df_cat_melted['Year'].unique()),
                                       default=[2020, 2022, 2024])
    
    with col2:
        # Category grouping option
        view_mode = st.selectbox("View Mode:", 
                               ["📊 All Categories", "⚖️ Terminations Only", "🏠 Non-Terminations Only"])
    
    if selected_years:
        filtered_cat = df_cat_melted[df_cat_melted['Year'].isin(selected_years)]
        
        # Apply view mode filter
        if view_mode == "⚖️ Terminations Only":
            termination_cats = ['Termination (Non-Payment)', 'Termination (Breach s.87)', 
                              'Termination (Co-Tenant s.102)', 'Termination (Other)']
            filtered_cat = filtered_cat[filtered_cat['Category'].isin(termination_cats)]
        elif view_mode == "🏠 Non-Terminations Only":
            non_termination_cats = ['Rental Bonds', 'General Orders', 'Repairs', 'Rent & Other Payments']
            filtered_cat = filtered_cat[filtered_cat['Category'].isin(non_termination_cats)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Stacked bar chart
            fig_stacked = px.bar(filtered_cat, x='Year', y='Applications', color='Category',
                               title=f'Applications by Category - {view_mode} (Stacked)',
                               color_discrete_sequence=px.colors.qualitative.Set3)
            fig_stacked.update_layout(height=400)
            st.plotly_chart(fig_stacked, use_container_width=True)
        
        with col2:
            # Line chart for trends
            fig_lines = px.line(filtered_cat, x='Year', y='Applications', color='Category',
                               title=f'Category Trends - {view_mode}',
                               markers=True,
                               color_discrete_sequence=px.colors.qualitative.Set3)
            fig_lines.update_layout(height=400)
            st.plotly_chart(fig_lines, use_container_width=True)
        
        # Detailed analysis section
        st.subheader("Detailed Category Analysis")
        
        # Create tabs for different analyses
        tab1, tab2, tab3 = st.tabs(["📈 Trends Over Time", "🥧 Proportions", "📊 Year-over-Year Changes"])
        
        with tab1:
            # All categories trend (full years only)
            full_years_cat = df_cat_melted[df_cat_melted['Year'].between(2017, 2024)]
            
            fig_all_trends = px.line(full_years_cat, x='Year', y='Applications', color='Category',
                                   title='All Category Trends (2017-2024)',
                                   markers=True,
                                   color_discrete_sequence=px.colors.qualitative.Set3)
            fig_all_trends.update_layout(height=500)
            st.plotly_chart(fig_all_trends, use_container_width=True)
        
        with tab2:
            # Proportion analysis for selected years
            for year in selected_years:
                year_data = filtered_cat[filtered_cat['Year'] == year]
                if not year_data.empty:
                    total = year_data['Applications'].sum()
                    
                    fig_pie = px.pie(year_data, values='Applications', names='Category',
                                   title=f'{year} - Category Distribution ({view_mode})')
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab3:
            # Year-over-Year percentage changes
            yoy_data = []
            for category in filtered_cat['Category'].unique():
                cat_data = filtered_cat[filtered_cat['Category'] == category].sort_values('Year')
                cat_data['YoY_Change'] = cat_data['Applications'].pct_change() * 100
                yoy_data.append(cat_data)
            
            if yoy_data:
                yoy_combined = pd.concat(yoy_data, ignore_index=True)
                yoy_combined = yoy_combined.dropna(subset=['YoY_Change'])
                
                if not yoy_combined.empty:
                    fig_yoy = px.bar(yoy_combined, x='Year', y='YoY_Change', color='Category',
                                   title='Year-over-Year Percentage Change by Category',
                                   color_discrete_sequence=px.colors.qualitative.Set3)
                    fig_yoy.update_layout(height=400)
                    fig_yoy.add_hline(y=0, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_yoy, use_container_width=True)
    
    # Key insights based on the detailed data
    st.subheader("📊 Key Insights from Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **🔍 Termination Patterns:**
        - **Non-payment terminations** remain the dominant category
        - **Breach (s.87) terminations** show consistent but lower volumes
        - **Co-tenant terminations (s.102)** are relatively rare
        - COVID-19 impact clearly visible in 2020-2021 non-payment reductions
        """)
    
    with col2:
        st.info("""
        **🏠 Non-Termination Trends:**
        - **Rental bond disputes** showing significant increase in 2024
        - **Rent & other payments** applications growing substantially
        - **Repairs** applications increased dramatically in 2024
        - **General orders** declined notably in 2024
        """)
    
    # Summary statistics table
    st.subheader("Category Statistics Summary (2017-2024)")
    
    full_years_summary = df_cat_melted[df_cat_melted['Year'].between(2017, 2024)]
    summary_stats = full_years_summary.groupby('Category')['Applications'].agg(['mean', 'min', 'max', 'sum', 'std']).round(0)
    summary_stats.columns = ['Annual Average', 'Minimum', 'Maximum', 'Total (2017-2024)', 'Std Deviation']
    summary_stats = summary_stats.sort_values('Annual Average', ascending=False)
    
    # Format to prevent juttering
    summary_stats = summary_stats.astype(int)
    
    st.dataframe(summary_stats, use_container_width=True, height=400)

elif page == "👥 Party Analysis":
    st.header("Applications by Party Type")
    
    # Prepare party data
    df_party_clean = df_parties.dropna(subset=['Landlord', 'Tenant'])
    df_party_melted = df_party_clean.melt(id_vars=['Year'], 
                                         value_vars=['Landlord', 'Tenant'],
                                         var_name='Party', value_name='Applications')
    
    # Main chart
    fig = px.bar(df_party_melted, x='Year', y='Applications', color='Party',
                title='Applications by Party Type',
                barmode='group',
                color_discrete_map={'Landlord': '#ef4444', 'Tenant': '#3b82f6'})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Ratio analysis
    st.subheader("Landlord to Tenant Ratio")
    
    df_party_clean['LL_Tenant_Ratio'] = df_party_clean['Landlord'] / df_party_clean['Tenant']
    df_party_clean['Tenant_Percentage'] = (df_party_clean['Tenant'] / 
                                          (df_party_clean['Landlord'] + df_party_clean['Tenant']) * 100)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_ratio = px.line(df_party_clean, x='Year', y='LL_Tenant_Ratio',
                           title='Landlord to Tenant Ratio',
                           markers=True)
        fig_ratio.update_layout(height=300)
        st.plotly_chart(fig_ratio, use_container_width=True)
    
    with col2:
        fig_percent = px.line(df_party_clean, x='Year', y='Tenant_Percentage',
                             title='Tenant Applications (%)',
                             markers=True)
        fig_percent.update_layout(height=300)
        st.plotly_chart(fig_percent, use_container_width=True)
    
    # Summary statistics
    st.subheader("Summary Statistics (2017-2024)")
    
    full_years = df_party_clean[df_party_clean['Year'].between(2017, 2024)]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_ll = full_years['Landlord'].mean()
        st.metric("Average Landlord Applications", f"{avg_ll:,.0f}")
    
    with col2:
        avg_tenant = full_years['Tenant'].mean()
        st.metric("Average Tenant Applications", f"{avg_tenant:,.0f}")
    
    with col3:
        avg_ratio = full_years['LL_Tenant_Ratio'].mean()
        st.metric("Average LL:Tenant Ratio", f"{avg_ratio:.1f}:1")

elif page == "📋 Detailed Party Breakdown":
    st.header("Detailed Party Analysis by Application Category")
    
    # Data preparation - normalize category names
    df_party_cat_clean = df_party_categories.copy()
    
    # Normalize category names for consistency
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Rental bonds', 'Rental Bonds')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('General orders', 'General Orders')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Termination - breach', 'Termination - Breach')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Termination - non-payment of rent', 'Termination non-payment of rent')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Termination - other', 'Termination - Other')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Termination by co-tenant (s102)', 'Termination by co-tenant (s.102)')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Termination by a co-tenant (s 102)', 'Termination by co-tenant (s.102)')
    df_party_cat_clean['Category'] = df_party_cat_clean['Category'].str.replace('Termination - Breach (s 87)', 'Termination - Breach (s.87)')
    
    # Calculate percentages
    df_party_cat_clean['Landlord_Pct'] = (df_party_cat_clean['Landlord'] / df_party_cat_clean['Total'] * 100).round(1)
    df_party_cat_clean['Tenant_Pct'] = (df_party_cat_clean['Tenant'] / df_party_cat_clean['Total'] * 100).round(1)
    
    # Analysis controls
    col1, col2 = st.columns(2)
    
    with col1:
        # Year selection
        available_years = sorted(df_party_cat_clean['Year'].unique())
        selected_years = st.multiselect("Select Years to Analyze:", 
                                       available_years,
                                       default=[2020, 2022, 2024])
    
    with col2:
        # Category selection
        available_categories = sorted(df_party_cat_clean['Category'].unique())
        analysis_mode = st.selectbox("Analysis Focus:", 
                                   ["📊 All Categories", "⚖️ Terminations Only", "🏠 Non-Terminations Only", "🎯 Custom Selection"])
    
    # Filter data based on selections
    if selected_years:
        filtered_data = df_party_cat_clean[df_party_cat_clean['Year'].isin(selected_years)]
        
        # Apply category filter
        if analysis_mode == "⚖️ Terminations Only":
            termination_categories = [cat for cat in available_categories if 'Termination' in cat]
            filtered_data = filtered_data[filtered_data['Category'].isin(termination_categories)]
        elif analysis_mode == "🏠 Non-Terminations Only":
            non_termination_categories = [cat for cat in available_categories if 'Termination' not in cat]
            filtered_data = filtered_data[filtered_data['Category'].isin(non_termination_categories)]
        elif analysis_mode == "🎯 Custom Selection":
            selected_categories = st.multiselect("Select Specific Categories:", 
                                                available_categories,
                                                default=['Rental Bonds', 'Repairs', 'Termination non-payment of rent'])
            filtered_data = filtered_data[filtered_data['Category'].isin(selected_categories)]
        
        if not filtered_data.empty:
            # Main Analysis Tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Party Split Overview", "📈 Trends Over Time", "🔍 Category Deep Dive", "💡 Key Insights"])
            
            with tab1:
                st.subheader("Who Files What: Party Split by Application Type")
                
                # Create side-by-side comparison for latest year
                latest_year = max(selected_years)
                latest_data = filtered_data[filtered_data['Year'] == latest_year]
                
                if not latest_data.empty:
                    # Stacked bar chart showing landlord/tenant split
                    fig_split = px.bar(latest_data, x='Category', y=['Landlord', 'Tenant'],
                                     title=f'{latest_year} - Applications by Category and Party',
                                     color_discrete_map={'Landlord': '#ef4444', 'Tenant': '#3b82f6'},
                                     barmode='stack')
                    fig_split.update_layout(height=500, xaxis_tickangle=-45)
                    st.plotly_chart(fig_split, use_container_width=True)
                    
                    # Percentage breakdown table
                    st.subheader(f"Percentage Breakdown ({latest_year})")
                    
                    summary_table = latest_data[['Category', 'Landlord_Pct', 'Tenant_Pct', 'Total']].copy()
                    summary_table = summary_table.sort_values('Total', ascending=False)
                    summary_table.columns = ['Application Category', 'Landlord %', 'Tenant %', 'Total Applications']
                    
                    st.dataframe(summary_table, use_container_width=True, hide_index=True, height=400)
            
            with tab2:
                st.subheader("Party Patterns Over Time")
                
                # Multi-year comparison for selected categories
                if len(selected_years) > 1:
                    # Create line charts showing trends
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Landlord trends
                        fig_landlord = px.line(filtered_data, x='Year', y='Landlord', color='Category',
                                             title='Landlord Applications Trends',
                                             markers=True)
                        fig_landlord.update_layout(height=400)
                        st.plotly_chart(fig_landlord, use_container_width=True)
                    
                    with col2:
                        # Tenant trends
                        fig_tenant = px.line(filtered_data, x='Year', y='Tenant', color='Category',
                                           title='Tenant Applications Trends',
                                           markers=True)
                        fig_tenant.update_layout(height=400)
                        st.plotly_chart(fig_tenant, use_container_width=True)
                    
                    # Percentage trends
                    st.subheader("Percentage Share Trends")
                    
                    # Calculate and show how the landlord/tenant split changes over time
                    fig_pct_trends = px.line(filtered_data, x='Year', y='Landlord_Pct', color='Category',
                                           title='Landlord Share (%) Trends by Category',
                                           markers=True)
                    fig_pct_trends.update_layout(height=400)
                    fig_pct_trends.add_hline(y=50, line_dash="dash", line_color="red", 
                                           annotation_text="50% Split Line")
                    st.plotly_chart(fig_pct_trends, use_container_width=True)
            
            with tab3:
                st.subheader("Category Deep Dive")
                
                # Select specific category for detailed analysis
                focus_category = st.selectbox("Select Category for Detailed Analysis:", 
                                            filtered_data['Category'].unique())
                
                category_data = filtered_data[filtered_data['Category'] == focus_category]
                
                if not category_data.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Absolute numbers over time
                        fig_abs = px.bar(category_data, x='Year', y=['Landlord', 'Tenant'],
                                       title=f'{focus_category} - Absolute Numbers',
                                       color_discrete_map={'Landlord': '#ef4444', 'Tenant': '#3b82f6'},
                                       barmode='group')
                        fig_abs.update_layout(height=400)
                        st.plotly_chart(fig_abs, use_container_width=True)
                    
                    with col2:
                        # Percentage composition
                        fig_pct = px.bar(category_data, x='Year', y=['Landlord_Pct', 'Tenant_Pct'],
                                       title=f'{focus_category} - Percentage Split',
                                       color_discrete_map={'Landlord_Pct': '#ef4444', 'Tenant_Pct': '#3b82f6'},
                                       barmode='stack')
                        fig_pct.update_layout(height=400)
                        st.plotly_chart(fig_pct, use_container_width=True)
                    
                    # Statistics for this category
                    st.subheader(f"Statistics: {focus_category}")
                    
                    avg_landlord_pct = category_data['Landlord_Pct'].mean()
                    avg_tenant_pct = category_data['Tenant_Pct'].mean()
                    total_apps = category_data['Total'].sum()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Landlord Share", f"{avg_landlord_pct:.1f}%")
                    with col2:
                        st.metric("Average Tenant Share", f"{avg_tenant_pct:.1f}%")
                    with col3:
                        st.metric("Total Applications", f"{total_apps:,}")
            
            with tab4:
                st.subheader("💡 Key Insights from Party Analysis")
                
                # Generate insights based on the data
                insights_data = df_party_cat_clean[df_party_cat_clean['Year'] == 2024]  # Use latest year
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🏠 **Tenant-Dominated Categories:**")
                    tenant_dominated = insights_data[insights_data['Tenant_Pct'] > 70].sort_values('Tenant_Pct', ascending=False)
                    if not tenant_dominated.empty:
                        for _, row in tenant_dominated.iterrows():
                            st.write(f"• **{row['Category']}**: {row['Tenant_Pct']:.1f}% tenant-filed")
                    
                    st.markdown("#### 📊 **Mixed Categories:**")
                    mixed = insights_data[(insights_data['Tenant_Pct'] >= 30) & (insights_data['Tenant_Pct'] <= 70)].sort_values('Tenant_Pct', ascending=False)
                    if not mixed.empty:
                        for _, row in mixed.iterrows():
                            st.write(f"• **{row['Category']}**: {row['Landlord_Pct']:.1f}% LL / {row['Tenant_Pct']:.1f}% T")
                
                with col2:
                    st.markdown("#### 🏢 **Landlord-Dominated Categories:**")
                    landlord_dominated = insights_data[insights_data['Landlord_Pct'] > 70].sort_values('Landlord_Pct', ascending=False)
                    if not landlord_dominated.empty:
                        for _, row in landlord_dominated.iterrows():
                            st.write(f"• **{row['Category']}**: {row['Landlord_Pct']:.1f}% landlord-filed")
                
                # Key observations
                st.markdown("#### 🔍 **Key Observations:**")
                st.info("""
                **Pattern Analysis:**
                - **Repairs**: Almost exclusively tenant-initiated (seeking landlord compliance)
                - **Rental Bonds**: Predominantly tenant-filed (disputing bond return)
                - **Termination (Non-payment)**: Exclusively landlord-initiated (eviction proceedings)
                - **Termination (Co-tenant)**: Exclusively tenant-initiated (shared housing disputes)
                - **General Orders**: Mixed filing pattern (both parties seek various orders)
                - **Rent & Other Payments**: Shift in 2024 showing more landlord claims
                """)
                
                # 2024 changes
                if 2024 in selected_years:
                    st.markdown("#### 🚨 **2024 Notable Changes:**")
                    st.warning("""
                    **Significant Shifts in 2024:**
                    - **Termination non-payment**: First time showing tenant filings (106 cases)
                    - **Rent & Other Payments**: Dramatic increase in landlord claims (2,249 vs 752 in 2023)
                    - **Repairs**: Notable increase in landlord-initiated repair applications (416 vs 116 in 2023)
                    - These changes may reflect new legislation or reporting methods
                    """)
    
    else:
        st.warning("Please select at least one year to analyze.")

elif page == "🗺️ Geographic Distribution":
    st.header("Geographic Distribution by Registry")
    
    # Sub-page selector
    geo_page = st.selectbox("Select Analysis Type:", 
                           ["🏢 Total Applications by Office", "📊 Individual List Types by Office"])
    
    if geo_page == "🏢 Total Applications by Office":
        st.subheader("Total CCD Applications by Registry")
        
        # Year selector
        selected_year = st.selectbox("Select Year", 
                                    sorted(df_total_ccd['Year'].unique()),
                                    index=len(df_total_ccd['Year'].unique())-2)  # Default to 2024
        
        year_data = df_total_ccd[df_total_ccd['Year'] == selected_year]
        
        if not year_data.empty:
            # Prepare data for visualization
            registries = ['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong']
            values = [year_data[reg].iloc[0] for reg in registries]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart
                fig_bar = px.bar(x=registries, y=values,
                               title=f'{selected_year} - Total Applications by Registry',
                               color=values,
                               color_continuous_scale='viridis')
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Pie chart
                fig_pie = px.pie(values=values, names=registries,
                               title=f'{selected_year} - Registry Distribution')
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # Time series for all registries - Total CCD
        st.subheader("Total Application Trends by Registry Over Time")
        
        # Melt the total CCD data
        df_total_melted = df_total_ccd.melt(id_vars=['Year'], 
                                           value_vars=['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong'],
                                           var_name='Registry', value_name='Applications')
        
        # Filter for full years
        full_year_data = df_total_melted[df_total_melted['Year'].between(2017, 2024)]
        
        fig_trends = px.line(full_year_data, x='Year', y='Applications', color='Registry',
                            title='Total Application Trends by Registry (2017-2024)',
                            markers=True)
        fig_trends.update_layout(height=500)
        st.plotly_chart(fig_trends, use_container_width=True)
        
        # Registry comparison table - Total
        st.subheader("Registry Statistics - Total Applications (2017-2024)")
        
        registry_stats = full_year_data.groupby('Registry')['Applications'].agg(['mean', 'min', 'max', 'std']).round(0)
        registry_stats.columns = ['Average', 'Minimum', 'Maximum', 'Std Dev']
        registry_stats = registry_stats.sort_values('Average', ascending=False)
        
        # Format as integers to prevent juttering
        registry_stats = registry_stats.astype(int)
        
        st.dataframe(registry_stats, use_container_width=True, height=300)
    
    else:  # Individual List Types by Office
        st.subheader("Individual Application Types by Registry")
        
        # List type selector
        list_type = st.selectbox("Select Application Type:", 
                                ["Private Tenancy", "Social Housing", "General", "Home Building", 
                                 "Strata Schemes", "Motor Vehicles", "Commercial", 
                                 "Residential Communities", "Retirement Villages"])
        
        # Map selection to dataframe
        df_map = {
            "Private Tenancy": df_geo,
            "Social Housing": df_social_housing,
            "General": df_general,
            "Home Building": df_home_building,
            "Strata Schemes": df_strata,
            "Motor Vehicles": df_motor_vehicles,
            "Commercial": df_commercial,
            "Residential Communities": df_residential_communities,
            "Retirement Villages": df_retirement_villages
        }
        
        selected_df = df_map[list_type]
        
        # Year selector
        selected_year = st.selectbox("Select Year for Comparison", 
                                    sorted(selected_df['Year'].unique()),
                                    index=len(selected_df['Year'].unique())-2,
                                    key="individual_year")  # Default to 2024
        
        year_data = selected_df[selected_df['Year'] == selected_year]
        
        if not year_data.empty:
            # Prepare data for visualization
            registries = ['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong']
            values = [year_data[reg].iloc[0] for reg in registries]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart
                fig_bar = px.bar(x=registries, y=values,
                               title=f'{selected_year} - {list_type} Applications by Registry',
                               color=values,
                               color_continuous_scale='plasma')
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Pie chart
                fig_pie = px.pie(values=values, names=registries,
                               title=f'{selected_year} - {list_type} Distribution')
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # Time series for selected list type
        st.subheader(f"{list_type} Trends by Registry Over Time")
        
        # Melt the selected data
        df_selected_melted = selected_df.melt(id_vars=['Year'], 
                                             value_vars=['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong'],
                                             var_name='Registry', value_name='Applications')
        
        # Filter for full years
        full_year_data = df_selected_melted[df_selected_melted['Year'].between(2017, 2024)]
        
        fig_trends = px.line(full_year_data, x='Year', y='Applications', color='Registry',
                            title=f'{list_type} Application Trends by Registry (2017-2024)',
                            markers=True)
        fig_trends.update_layout(height=500)
        st.plotly_chart(fig_trends, use_container_width=True)
        
        # Comparative analysis across years
        st.subheader(f"{list_type} - Multi-Year Comparison")
        
        # Select multiple years for comparison
        comparison_years = st.multiselect("Select Years to Compare:", 
                                        sorted(selected_df['Year'].unique()),
                                        default=[2020, 2022, 2024])
        
        if len(comparison_years) > 1:
            comparison_data = selected_df[selected_df['Year'].isin(comparison_years)]
            
            # Create grouped bar chart
            df_comparison_melted = comparison_data.melt(id_vars=['Year'], 
                                                       value_vars=['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong'],
                                                       var_name='Registry', value_name='Applications')
            
            fig_comparison = px.bar(df_comparison_melted, x='Registry', y='Applications', color='Year',
                                   title=f'{list_type} Applications - Multi-Year Comparison',
                                   barmode='group')
            fig_comparison.update_layout(height=400)
            st.plotly_chart(fig_comparison, use_container_width=True)

elif page == "⚖️ NCAT Lists Comparison":
    st.header("NCAT Lists Comparison")
    
    # Sub-page selector
    comparison_page = st.selectbox("Select Analysis Type:", 
                                  ["📊 Overall List Performance", "🗺️ List Types by Registry"])
    
    if comparison_page == "📊 Overall List Performance":
        st.subheader("Overall Application Volume by List Type")
        
        # Prepare other lists data
        df_lists_melted = df_other_lists.melt(id_vars=['Year'], 
                                             value_vars=['Tenancy', 'Social_Housing', 'General', 'Home_Building', 'Strata_Schemes', 'Motor_Vehicles'],
                                             var_name='List_Type', value_name='Applications')
        
        # List name mapping
        list_mapping = {
            'Tenancy': 'Tenancy',
            'Social_Housing': 'Social Housing',
            'General': 'General',
            'Home_Building': 'Home Building',
            'Strata_Schemes': 'Strata Schemes',
            'Motor_Vehicles': 'Motor Vehicles'
        }
        df_lists_melted['List_Type'] = df_lists_melted['List_Type'].map(list_mapping)
        
        # Year filter
        year_filter = st.slider("Select Year Range", 
                               min_value=2017, max_value=2024, 
                               value=(2017, 2024))
        
        filtered_lists = df_lists_melted[df_lists_melted['Year'].between(year_filter[0], year_filter[1])]
        
        # Stacked area chart
        fig_area = px.area(filtered_lists, x='Year', y='Applications', color='List_Type',
                          title='NCAT List Applications Over Time',
                          color_discrete_sequence=px.colors.qualitative.Set3)
        fig_area.update_layout(height=500)
        st.plotly_chart(fig_area, use_container_width=True)
        
        # Market share analysis
        st.subheader("Market Share Analysis")
        
        # Calculate proportions
        total_by_year = filtered_lists.groupby('Year')['Applications'].sum().reset_index()
        total_by_year.columns = ['Year', 'Total']
        
        filtered_lists_with_total = filtered_lists.merge(total_by_year, on='Year')
        filtered_lists_with_total['Percentage'] = (filtered_lists_with_total['Applications'] / 
                                                  filtered_lists_with_total['Total'] * 100)
        
        # Line chart for percentages
        fig_percent = px.line(filtered_lists_with_total, x='Year', y='Percentage', color='List_Type',
                             title='Market Share (%) by List Type',
                             markers=True)
        fig_percent.update_layout(height=400)
        st.plotly_chart(fig_percent, use_container_width=True)
        
        # Summary statistics
        st.subheader("List Performance Summary (2017-2024)")
        
        full_years_lists = filtered_lists[filtered_lists['Year'].between(2017, 2024)]
        summary_stats = full_years_lists.groupby('List_Type')['Applications'].agg(['mean', 'sum', 'std']).round(0)
        summary_stats.columns = ['Annual Average', 'Total (2017-2024)', 'Std Deviation']
        summary_stats['Market Share %'] = (summary_stats['Total (2017-2024)'] / summary_stats['Total (2017-2024)'].sum() * 100).round(1)
        summary_stats = summary_stats.sort_values('Annual Average', ascending=False)
        
        # Format to prevent juttering
        summary_stats[['Annual Average', 'Total (2017-2024)', 'Std Deviation']] = summary_stats[['Annual Average', 'Total (2017-2024)', 'Std Deviation']].astype(int)
        
        st.dataframe(summary_stats, use_container_width=True, height=300)
        
        # Key insights
        st.info("""
        **🔍 Key Insights:**
        - **Tenancy** consistently dominates with ~55% market share
        - **Social Housing** is the second largest category
        - **Home Building** and **General** lists show steady demand
        - **Motor Vehicles** and **Strata Schemes** represent smaller but consistent workloads
        """)
    
    else:  # List Types by Registry
        st.subheader("Application Types by Registry Analysis")
        
        # Create a comprehensive comparison
        col1, col2 = st.columns(2)
        
        with col1:
            # Select year for analysis
            selected_year = st.selectbox("Select Year for Registry Analysis", 
                                        sorted(df_total_ccd['Year'].unique()),
                                        index=len(df_total_ccd['Year'].unique())-2)
        
        with col2:
            # Select specific list types to compare
            available_lists = ["Private Tenancy", "Social Housing", "General", "Home Building", 
                              "Strata Schemes", "Motor Vehicles", "Commercial", 
                              "Residential Communities", "Retirement Villages"]
            selected_lists = st.multiselect("Select List Types to Compare:", 
                                           available_lists,
                                           default=["Private Tenancy", "Social Housing"])
        
        if selected_lists:
            # Prepare data for selected lists and year
            registry_comparison_data = []
            
            for list_type in selected_lists:
                if list_type == "Private Tenancy":
                    df_source = df_geo
                elif list_type == "Social Housing":
                    df_source = df_social_housing
                elif list_type == "General":
                    df_source = df_general
                elif list_type == "Home Building":
                    df_source = df_home_building
                elif list_type == "Strata Schemes":
                    df_source = df_strata
                elif list_type == "Motor Vehicles":
                    df_source = df_motor_vehicles
                elif list_type == "Commercial":
                    df_source = df_commercial
                elif list_type == "Residential Communities":
                    df_source = df_residential_communities
                elif list_type == "Retirement Villages":
                    df_source = df_retirement_villages
                
                year_data = df_source[df_source['Year'] == selected_year]
                if not year_data.empty:
                    for registry in ['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong']:
                        registry_comparison_data.append({
                            'List_Type': list_type,
                            'Registry': registry,
                            'Applications': year_data[registry].iloc[0]
                        })
            
            if registry_comparison_data:
                df_comparison = pd.DataFrame(registry_comparison_data)
                
                # Grouped bar chart
                fig_grouped = px.bar(df_comparison, x='Registry', y='Applications', color='List_Type',
                                   title=f'{selected_year} - Application Types by Registry',
                                   barmode='group',
                                   color_discrete_sequence=px.colors.qualitative.Set2)
                fig_grouped.update_layout(height=500)
                st.plotly_chart(fig_grouped, use_container_width=True)
                
                # Stacked percentage chart
                fig_stacked = px.bar(df_comparison, x='Registry', y='Applications', color='List_Type',
                                   title=f'{selected_year} - List Type Distribution by Registry (%)',
                                   text='Applications',
                                   color_discrete_sequence=px.colors.qualitative.Set2)
                fig_stacked.update_traces(texttemplate='%{text}', textposition='inside')
                fig_stacked.update_layout(height=400, barnorm='percent')
                st.plotly_chart(fig_stacked, use_container_width=True)
        
        # Registry specialization analysis
        st.subheader("Registry Specialization Analysis")
        
        # Calculate which registries handle the most of each type
        specialization_data = []
        list_dataframes = {
            "Private Tenancy": df_geo,
            "Social Housing": df_social_housing,
            "General": df_general,
            "Home Building": df_home_building,
            "Strata Schemes": df_strata,
            "Motor Vehicles": df_motor_vehicles,
            "Commercial": df_commercial,
            "Residential Communities": df_residential_communities,
            "Retirement Villages": df_retirement_villages
        }
        
        for list_type, df_source in list_dataframes.items():
            # Use 2024 data for analysis
            year_2024 = df_source[df_source['Year'] == 2024]
            if not year_2024.empty:
                registries = ['Liverpool', 'Newcastle', 'Penrith', 'Sydney', 'Tamworth', 'Wollongong']
                values = [year_2024[reg].iloc[0] for reg in registries]
                total = sum(values)
                
                for registry, value in zip(registries, values):
                    percentage = (value / total * 100) if total > 0 else 0
                    specialization_data.append({
                        'List_Type': list_type,
                        'Registry': registry,
                        'Applications': value,
                        'Percentage_of_Type': percentage
                    })
        
        if specialization_data:
            df_specialization = pd.DataFrame(specialization_data)
            
            # Heatmap showing percentage distribution
            pivot_data = df_specialization.pivot(index='Registry', columns='List_Type', values='Percentage_of_Type')
            
            fig_heatmap = px.imshow(pivot_data.values,
                                   x=pivot_data.columns,
                                   y=pivot_data.index,
                                   color_continuous_scale='viridis',
                                   title='Registry Specialization Heatmap (% of each list type handled by registry)',
                                   text_auto='.1f')
            fig_heatmap.update_layout(height=400)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Top performers table
            st.subheader("Registry Performance Leaders (2024)")
            
            # Find the top registry for each list type
            top_performers = df_specialization.loc[df_specialization.groupby('List_Type')['Applications'].idxmax()]
            top_performers = top_performers[['List_Type', 'Registry', 'Applications', 'Percentage_of_Type']].sort_values('Applications', ascending=False)
            top_performers['Percentage_of_Type'] = top_performers['Percentage_of_Type'].round(1)
            top_performers['Applications'] = top_performers['Applications'].astype(int)
            
            st.dataframe(top_performers, use_container_width=True, hide_index=True, height=300)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b;'>
    <p>NCAT Operations Dashboard | Data Period: 2015-2025 | 
    <em>Built with Streamlit</em></p>
</div>
""", unsafe_allow_html=True)