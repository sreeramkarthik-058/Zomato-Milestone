"""Custom CSS and styling utilities for the Streamlit app to provide a premium feel."""

import streamlit as st

def inject_custom_css():
    """Inject custom CSS to enhance the Streamlit UI."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');
        
        /* General background and font */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
            background-color: #f8f9fa !important;
            color: #1a1c1e !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* Override all typography classes */
        h1, h2, h3, h4, h5, h6, p, span, div, label, button, input, textarea, select, .stMarkdown, .stText {
            font-family: 'Montserrat', sans-serif !important;
            color: #1a1c1e !important;
        }
        
        /* Headline Large */
        .headline-large {
            font-size: 32px !important;
            font-weight: 700 !important;
            line-height: 40px !important;
            color: #1a1c1e !important;
            margin-bottom: 8px !important;
        }
        
        /* Headline Medium */
        .headline-medium {
            font-size: 24px !important;
            font-weight: 700 !important;
            line-height: 32px !important;
            color: #1a1c1e !important;
            margin-bottom: 16px !important;
        }
        
        /* Labels & Widget Text */
        [data-testid="stWidgetLabel"] p, label, .label-medium {
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 600 !important;
            font-size: 12px !important;
            line-height: 16px !important;
            text-transform: uppercase !important;
            color: #44474e !important; /* On-Surface Variant */
            letter-spacing: 0.5px !important;
        }
        
        /* Form Action Buttons (Crimson, ROUND_EIGHT) */
        div[data-testid="stFormSubmitButton"] button, button[kind="primary"] {
            background-color: #d31027 !important;
            color: #ffffff !important;
            border: 1px solid #d31027 !important;
            border-radius: 8px !important; /* ROUND_EIGHT */
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 700 !important;
            padding: 12px 24px !important;
            font-size: 14px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
            box-shadow: 0 2px 4px rgba(211, 16, 39, 0.15) !important;
            cursor: pointer !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover, button[kind="primary"]:hover {
            background-color: #b50e20 !important;
            border-color: #b50e20 !important;
            box-shadow: 0 4px 8px rgba(211, 16, 39, 0.25) !important;
        }
        div[data-testid="stFormSubmitButton"] button:active, button[kind="primary"]:active {
            transform: translateY(1px) !important;
        }
        
        /* Inputs styling */
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
            background-color: #ffffff !important;
            border: 1px solid #74777f !important; /* Outline */
            border-radius: 8px !important;
            color: #1a1c1e !important;
            font-family: 'Montserrat', sans-serif !important;
            font-size: 14px !important;
            padding: 10px 14px !important;
            transition: border-color 0.2s ease !important;
        }
        div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
            border-color: #d31027 !important;
            box-shadow: 0 0 0 1px #d31027 !important;
        }
        
        /* Selectbox styling */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid #74777f !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] * {
            color: #1a1c1e !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* Slider styling */
        div[data-testid="stSlider"] [role="slider"] {
            background-color: #d31027 !important;
        }
        div[data-testid="stSlider"] div[data-val] {
            color: #d31027 !important;
            font-weight: 600 !important;
        }
        
        /* Sidebar styling (Airy light background, clean separator) */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important; /* Surface Container */
            border-right: 1px solid #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #1a1c1e !important;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* Info and status boxes */
        div.stAlert {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
            padding: 16px !important;
        }
        div.stAlert p {
            color: #1a1c1e !important;
            font-size: 14px !important;
        }
        
        /* Custom UI Input Chips (Small buttons) */
        div.stButton > button {
            background-color: #ffffff !important;
            color: #1a1c1e !important;
            border: 1px solid #74777f !important; /* Outline */
            border-radius: 20px !important; /* Rounded pill */
            padding: 4px 14px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            font-family: 'Montserrat', sans-serif !important;
            transition: all 0.2s ease !important;
            cursor: pointer !important;
        }
        div.stButton > button:hover {
            border-color: #d31027 !important;
            color: #d31027 !important;
            background-color: rgba(211, 16, 39, 0.05) !important;
        }
        div.stButton > button:focus {
            outline: none !important;
            border-color: #d31027 !important;
        }
        
        /* Custom card styling */
        .restaurant-card {
            background-color: #ffffff; /* Surface Container */
            border-radius: 8px; /* ROUND_EIGHT */
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid #74777f; /* Outline */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
            transition: transform 0.2s, border-color 0.2s;
        }
        .restaurant-card:hover {
            transform: translateY(-2px);
            border-color: #d31027;
        }
        
        /* Typography inside cards */
        .restaurant-name {
            color: #1a1c1e !important;
            font-size: 20px;
            font-weight: 700;
            margin: 0;
            font-family: 'Montserrat', sans-serif !important;
        }
        .restaurant-meta {
            color: #44474e; /* On-Surface Variant */
            font-size: 13px;
            margin-bottom: 16px;
            font-family: 'Montserrat', sans-serif !important;
        }
        .rating-badge {
            background-color: #d31027; /* Crimson fill */
            color: #ffffff !important;
            padding: 4px 12px;
            border-radius: 16px; /* Pill shape */
            font-weight: 700;
            font-size: 13px;
            font-family: 'Montserrat', sans-serif !important;
            white-space: nowrap;
        }
        
        /* AI Rationale (Light tint, vertical Crimson accent bar) */
        .explanation-text {
            background-color: rgba(211, 16, 39, 0.05) !important; /* AI Rationale Tint */
            color: #1a1c1e !important;
            font-size: 14px;
            line-height: 1.6;
            border-left: 4px solid #d31027 !important; /* Crimson accent bar */
            padding: 16px;
            margin-top: 16px;
            border-radius: 0 8px 8px 0;
            font-family: 'Montserrat', sans-serif !important;
        }
        
        /* Hide default Streamlit visual headers & footer */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_restaurant_card(result):
    """Render a single restaurant recommendation card."""
    with st.container():
        st.markdown(
            f"""
            <div class="restaurant-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
                    <div class="restaurant-name">{result.rank}. {result.restaurant_name}</div>
                    <div class="rating-badge">★ {result.rating:.1f}</div>
                </div>
                <div class="restaurant-meta">
                    <span style="font-weight: 600; color: #1a1c1e;">CUISINE:</span> {result.cuisine} 
                    <span style="margin: 0 8px; color: #74777f;">|</span> 
                    <span style="font-weight: 600; color: #1a1c1e;">COST:</span> {result.estimated_cost}
                </div>
                <div class="explanation-text">
                    <div style="font-weight: 700; font-size: 11px; text-transform: uppercase; color: #d31027; margin-bottom: 6px; letter-spacing: 0.5px;">AI Rationale</div>
                    {result.explanation}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
