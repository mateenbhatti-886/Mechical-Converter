import streamlit as st
import requests
import pandas as pd

# Page config
st.set_page_config(page_title="Mechanical Unit Converter", page_icon="🔧", layout="wide")

API_BASE_URL = "https://mechical-converter.onrender.com"

# Custom CSS
st.markdown("""
    <style>
    .header-text {
        font-size: 24px; font-weight: bold; text-align: center; padding: 10px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white; border-radius: 10px; margin-bottom: 20px;
    }
    .student-info {
        text-align: center; font-size: 18px; color: #2c3e50; padding: 15px;
        background: #ecf0f1; border-radius: 10px; margin-bottom: 30px;
        border-left: 5px solid #3498db;
    }
    .result-box {
        padding: 20px; background: #f8f9fa; border-radius: 10px;
        border: 2px solid #4CAF50; margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="header-text"><h1>🔧 MECHANICAL UNIT CONVERTER AND MATERIAL DENSITY CHECKER</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="student-info"><h2>MATEEN AHMAD BHATTI</h2><h3>24-ME-79</h3><p>Department of Mechanical Engineering</p></div>', unsafe_allow_html=True)

# API helper
def api_call(endpoint, method='GET', params=None, json_data=None):
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.post(url, json=json_data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}")
            return None
    except:
        st.error("❌ Cannot connect to backend. Run main.py first!")
        return None

def format_unit(unit):
    return unit.replace("_", " ").title()

# Sidebar
st.sidebar.title("📋 Navigation")
mode = st.sidebar.radio("Select Mode", ["🏠 Home", "🔄 Unit Converter", "📊 Material Density", "⚖️ Mass Calculator", "📐 Volume Calculator"])

# ==================== HOME ====================
if mode == "🏠 Home":
    st.header("Welcome!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("🔄 Unit Converter")
        st.write("Convert mechanical units")
    with col2:
        st.subheader("📊 Material Density")
        st.write("100+ materials database")
    with col3:
        st.subheader("⚖️ Calculations")
        st.write("Mass & Volume calculations")

# ==================== UNIT CONVERTER ====================
elif mode == "🔄 Unit Converter":
    st.header("🔄 Unit Converter")
    categories_data = api_call("categories")
    
    if categories_data:
        categories_dict = categories_data.get("categories", {})
        category = st.selectbox("Category:", list(categories_dict.keys()), format_func=format_unit)
        value = st.number_input("Value:", value=1.0)
        
        units = categories_dict.get(category, [])
        if units:
            col1, col2, col3 = st.columns([2, 1, 2])
            with col1:
                from_unit = st.selectbox("From:", units, format_func=format_unit)
            with col2:
                st.markdown("<h2 style='text-align:center'>➡️</h2>", unsafe_allow_html=True)
            with col3:
                to_unit = st.selectbox("To:", units, format_func=format_unit)
            
            if st.button("Convert", type="primary"):
                result = api_call("convert", params={"category": category, "value": value, "from_unit": from_unit, "to_unit": to_unit})
                if result:
                    st.success(f"**{value} {format_unit(from_unit)}** = **{result['result']:.6g} {format_unit(to_unit)}**")

# ==================== MATERIAL DENSITY ====================
elif mode == "📊 Material Density":
    st.header("📊 Material Density Checker")
    tab1, tab2 = st.tabs(["🔍 Search", "📂 Browse"])
    
    with tab1:
        search_query = st.text_input("Material name:", placeholder="e.g., steel")
        if st.button("Search", type="primary") and search_query:
            result = api_call("search-materials", params={"query": search_query})
            if result and result.get("results"):
                for mat in result["results"]:
                    st.write(f"**{mat['display_name']}** ({mat['category']}): {mat['density_kg_m3']} kg/m³")
            else:
                st.warning("Not found")
    
    with tab2:
        categories = api_call("materials/categories")
        if categories:
            cat = st.selectbox("Category:", categories.get("categories", []))
            if cat:
                data = api_call("materials", params={"category": cat})
                if data:
                    df_data = [{"Material": m.replace("_", " ").title(), "Density (kg/m³)": d} for m, d in data["materials"].items()]
                    st.dataframe(pd.DataFrame(df_data), use_container_width=True)

# ==================== MASS CALCULATOR ====================
elif mode == "⚖️ Mass Calculator":
    st.header("⚖️ Mass Calculator")
    material = st.text_input("Material:", placeholder="e.g., steel_mild")
    volume = st.number_input("Volume:", value=1.0)
    vol_unit = st.selectbox("Volume unit:", ["cubic_meter", "liter", "gallon_us", "cubic_foot"], format_func=format_unit)
    mass_unit = st.selectbox("Mass unit:", ["kilogram", "gram", "pound", "metric_ton"], format_func=format_unit)
    
    if st.button("Calculate", type="primary") and material:
        result = api_call("calculate-mass", method="POST", json_data={"material": material, "volume": volume, "volume_unit": vol_unit, "mass_unit": mass_unit})
        if result:
            st.success(f"Mass = **{result['mass']:.4f} {format_unit(mass_unit)}**")
            st.info(f"Density: {result['density_kg_m3']} kg/m³")

# ==================== VOLUME CALCULATOR ====================
elif mode == "📐 Volume Calculator":
    st.header("📐 Volume Calculator")
    material = st.text_input("Material:", placeholder="e.g., aluminum_6061")
    mass = st.number_input("Mass:", value=1.0)
    mass_unit = st.selectbox("Mass unit:", ["kilogram", "gram", "pound", "metric_ton"], format_func=format_unit)
    vol_unit = st.selectbox("Volume unit:", ["cubic_meter", "liter", "gallon_us", "cubic_foot"], format_func=format_unit)
    
    if st.button("Calculate", type="primary") and material:
        result = api_call("calculate-volume", params={"material": material, "mass": mass, "mass_unit": mass_unit, "volume_unit": vol_unit})
        if result:
            st.success(f"Volume = **{result['volume']:.4f} {format_unit(vol_unit)}**")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center'>© 2024 | Mateen Ahmad Bhatti (24-ME-79)</p>", unsafe_allow_html=True)
