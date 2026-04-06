import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

# --- 1. PAGE CONFIGURATION (Must be the first Streamlit command) ---
st.set_page_config(layout="wide", page_title="Process Engineering Calc Engine")

# --- 2. SHARED DATA & FUNCTIONS ---
@st.cache_data
def load_standard_hoppers():
    # Transcribed representative rows from standard sizes
    data = {
        'Nominal Live Vol (m3)': [1.25, 2.0, 2.9, 3.9, 5.0, 6.9, 8.6, 10.9, 13.8, 16.8, 20.0],
        'Flow Norm (m3/hr)': [75, 118, 175, 235, 300, 415, 515, 655, 830, 1010, 1200],
        'Flow Max (m3/hr)': [100, 157, 233, 313, 400, 553, 687, 873, 1107, 1347, 1600],
        'Diameter (mm)': [1300, 1500, 1700, 1900, 2100, 2300, 2500, 2700, 2900, 3100, 3250],
        'Dia Base (mm)': [433, 500, 567, 633, 700, 767, 833, 900, 967, 1033, 1083],
        'Cone Height (mm)': [751, 866, 981, 1097, 1212, 1328, 1443, 1559, 1674, 1790, 1876],
        'Cyl Height (mm)': [1199, 1384, 1569, 1753, 1938, 2122, 2307, 2491, 2676, 2860, 2999],
        'Height Cyl to Notch (mm)': [974, 1109, 1269, 1428, 1563, 1722, 1807, 1941, 2126, 2260, 2349],
        'Total Height (mm)': [1950, 2250, 2550, 2850, 3150, 3450, 3750, 4050, 4350, 4650, 4875],
        'Suction Dia (mm)': [150, 200, 250, 250, 250, 300, 350, 400, 450, 500, 600],
        'OF Box Outer Offset (mm)': [160, 160, 190, 210, 230, 230, 250, 280, 280, 305, 325],
        'OF Box Projection (mm)': [385, 385, 440, 485, 530, 530, 600, 655, 655, 705, 750],
        'OF Box Depth Below Notch (mm)': [200, 200, 250, 250, 300, 300, 350, 400, 450, 500, 500]
    }
    return pd.DataFrame(data)

def calculate_volumes(flow, res_time, fvf):
    base_vol = flow * (res_time / 60)
    live_vol = base_vol * fvf
    return base_vol, live_vol

def plot_hopper(hopper, shape, ll_lvl, hh_lvl):
    fig, ax = plt.subplots(figsize=(6, 8))
    
    D = hopper['Diameter (mm)'] / 1000
    Db = hopper['Dia Base (mm)'] / 1000
    Hc = hopper['Cone Height (mm)'] / 1000
    Hcyl = hopper['Cyl Height (mm)'] / 1000
    Htot = Hc + Hcyl
    Hnotch = Hc + (hopper['Height Cyl to Notch (mm)'] / 1000)
    OF_proj = hopper['OF Box Projection (mm)'] / 1000
    OF_depth = hopper['OF Box Depth Below Notch (mm)'] / 1000
    
    hopper_pts = [
        (-Db/2, 0), (Db/2, 0),
        (D/2, Hc), (D/2, Htot),
        (-D/2, Htot), (-D/2, Hc)
    ]
    poly = Polygon(hopper_pts, closed=True, fill=True, facecolor='#e0f2f1', edgecolor='black', linewidth=2)
    ax.add_patch(poly)
    
    box_pts = [
        (-D/2, Hnotch), 
        (-D/2 - OF_proj, Hnotch), 
        (-D/2 - OF_proj, Hnotch - OF_depth), 
        (-D/2, Hnotch - OF_depth)
    ]
    of_box = Polygon(box_pts, closed=True, fill=True, facecolor='#d1c4e9', edgecolor='black', linewidth=1.5)
    ax.add_patch(of_box)
    
    ax.axhline(y=ll_lvl, color='red', linestyle='--', label=f'LL Level ({ll_lvl:.2f}m)')
    ax.axhline(y=hh_lvl, color='blue', linestyle='-', linewidth=2, label=f'HH Level / Notch ({hh_lvl:.2f}m)')
    
    ax.set_xlim(-D - OF_proj, D)
    ax.set_ylim(-0.5, Htot + 0.5)
    ax.set_aspect('equal')
    ax.set_title(f"Hopper Sketch ({shape.capitalize()})")
    ax.set_ylabel("Height (m)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=8)
    
    return fig

# --- 3. PAGE MODULES ---

def page_home():
    """Landing page for the application."""
    st.title("⚙️ Process Engineering Calculation Engine")
    st.markdown("---")
    st.write("Welcome to the calculation engine. Please use the sidebar to navigate between available equipment sizing and MTO generation tools.")
    
    st.write("### Available Modules:")
    st.write("- **Pump Hopper Sizing:** Calculate live volumes, dimensions, and generate sketches for standard round and square hoppers based on flow requirements.")
    st.write("- **Heap Leach Sizing:** *(Under Development)*")

def page_hopper_sizing():
    """The Pump Hopper Sizing Application."""
    st.title("Pump Hopper Sizing & MTO Calculator")
    df_standards = load_standard_hoppers()

    with st.sidebar:
        st.header("1. Equipment Details")
        tag = st.text_input("Equipment Tag", "2130-HP-001")
        desc = st.text_input("Description", "TEST BOX")
        
        st.header("2. Process Conditions")
        shape = st.selectbox("Hopper Shape", ["Round", "Square"])
        fvf = st.number_input("Froth Volume Factor (FVF)", min_value=1.0, value=1.5, step=0.1)
        
        st.subheader("Minimum Case")
        min_flow = st.number_input("Min Feed Flow (m3/h)", value=190.0)
        min_res = st.number_input("Min Residence Time (sec)", value=45.0) / 60 
        
        st.subheader("Nominal Case")
        nom_flow = st.number_input("Nominal Feed Flow (m3/h)", value=190.0)
        nom_res = st.number_input("Nominal Residence Time (sec)", value=45.0) / 60
        
        st.subheader("Maximum Case")
        max_flow = st.number_input("Max Feed Flow (m3/h)", value=228.0)
        max_res = st.number_input("Max Residence Time (sec)", value=30.0) / 60

    # Calculations
    _, min_live = calculate_volumes(min_flow, min_res, fvf)
    _, nom_live = calculate_volumes(nom_flow, nom_res, fvf)
    _, max_live = calculate_volumes(max_flow, max_res, fvf)
    req_live_vol = max(min_live, nom_live, max_live)

    shape_factor = 1.0 if shape == "Round" else (math.pi / 4)
    lookup_vol = req_live_vol * shape_factor

    try:
        selected_hopper = df_standards[df_standards['Nominal Live Vol (m3)'] >= lookup_vol].iloc[0]
    except IndexError:
        st.error("Required volume exceeds standard tables. Please manually size or update the standard table.")
        st.stop()

    actual_live_vol = selected_hopper['Nominal Live Vol (m3)'] / shape_factor

    # Results UI
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader(f"MTO & Dimensions for: {tag}")
        st.markdown(f"**Description:** {desc}")
        
        st.write("### Calculated Volumes")
        metrics_df = pd.DataFrame({
            "Case": ["Min", "Nominal", "Max"],
            "Feed Flow (m3/h)": [min_flow, nom_flow, max_flow],
            "Res Time (min)": [min_res, nom_res, max_res],
            "Req. Live Vol (m3)": [round(min_live, 2), round(nom_live, 2), round(max_live, 2)]
        })
        st.dataframe(metrics_df, hide_index=True)
        
        st.success(f"**Design Live Volume Required:** {req_live_vol:.2f} m³")
        st.info(f"**Selected Standard Hopper Actual Live Capacity ({shape}):** {actual_live_vol:.2f} m³")

        st.write("### Geometry & MTO")
        dim_label = "Diameter" if shape == "Round" else "Width"
        
        mto_col1, mto_col2 = st.columns(2)
        mto_col1.metric(f"Overall {dim_label} (mm)", int(selected_hopper['Diameter (mm)']))
        mto_col1.metric("Total Height (mm)", int(selected_hopper['Total Height (mm)']))
        mto_col1.metric("Cone/Base Height (mm)", int(selected_hopper['Cone Height (mm)']))
        
        mto_col2.metric("Suction Nozzle Dia (mm)", int(selected_hopper['Suction Dia (mm)']))
        mto_col2.metric(f"Base {dim_label} (mm)", int(selected_hopper['Dia Base (mm)']))
        aspect_ratio = selected_hopper['Total Height (mm)'] / selected_hopper['Diameter (mm)']
        mto_col2.metric("Aspect Ratio", f"{aspect_ratio:.2f} : 1")

    with col2:
        st.write("### Operating Levels & Profile")
        cone_h_m = selected_hopper['Cone Height (mm)'] / 1000
        cyl_to_notch_m = selected_hopper['Height Cyl to Notch (mm)'] / 1000
        
        hh_lvl = cone_h_m + cyl_to_notch_m
        ll_lvl = cone_h_m 
        
        fig = plot_hopper(selected_hopper, shape, ll_lvl, hh_lvl)
        st.pyplot(fig)
        
        st.write(f"- **HH Level (Overflow Commence):** {hh_lvl*1000:.0f} mm (from base)")
        st.write(f"- **LL Level (Min Submergence):** {ll_lvl*1000:.0f} mm (from base)")
        st.write(f"- **Overflow Box Depth:** {int(selected_hopper['OF Box Depth Below Notch (mm)'])} mm")
        st.write(f"- **Overflow Box Projection:** {int(selected_hopper['OF Box Projection (mm)'])} mm")

def page_heap_leach():
    """Placeholder for the Heap Leach calculator."""
    st.title("Heap Leach Sizing Calculator")
    st.info("🚧 This calculation module is currently under development. Parameters for pad area, lift height, and irrigation rates will be added here.")
    # Add your future heap leach UI inputs and logic here.

# --- 4. MAIN APPLICATION ROUTING ---
def main():
    st.sidebar.title("Navigation")
    
    # Use a selectbox for clean navigation
    app_mode = st.sidebar.selectbox(
        "Choose a module:",
        ["Home", "Pump Hopper Sizing", "Heap Leach Sizing (WIP)"]
    )
    
    st.sidebar.markdown("---")

    # Route to the appropriate function based on selection
    if app_mode == "Home":
        page_home()
    elif app_mode == "Pump Hopper Sizing":
        page_hopper_sizing()
    elif app_mode == "Heap Leach Sizing (WIP)":
        page_heap_leach()

# Execution entry point
if __name__ == "__main__":
    main()
