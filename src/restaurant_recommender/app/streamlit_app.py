"""Main Streamlit application for Epicurean Pulse: AI-Powered Restaurant Recommendations."""

import os
from pathlib import Path
import streamlit as st
import pandas as pd

from restaurant_recommender.orchestrator import RecommendationOrchestrator
from restaurant_recommender.models import UserPreferences, Budget, RecommendationStatus
from restaurant_recommender.app.style_utils import inject_custom_css, render_restaurant_card

# Page configuration
st.set_page_config(
    page_title="Epicurean Pulse — Gastronomy Concierge",
    page_icon="🍴",
    layout="wide",
)

def main():
    # Inject design system custom CSS styles
    inject_custom_css()
    
    # Initialize session state for quick chips bidirectional sync
    if "location_input" not in st.session_state:
        st.session_state.location_input = ""
    if "cuisine_input" not in st.session_state:
        st.session_state.cuisine_input = ""
    
    # App Header Visual Banner
    assets_dir = Path(__file__).parent / "assets"
    banner_path = assets_dir / "banner.png"
    if banner_path.exists():
        st.image(str(banner_path), use_column_width=True)
    else:
        st.markdown('<div class="headline-large">🍴 EPICUREAN PULSE</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 16px; color: #44474e; margin-bottom: 24px;">An AI-native gastronomy concierge.</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border: none; border-top: 1px solid #74777f; margin: 24px 0;' />", unsafe_allow_html=True)

    # Initializing Orchestrator
    try:
        orchestrator = RecommendationOrchestrator()
    except Exception as e:
        st.error(f"Failed to initialize the recommendation engine: {e}")
        st.info("Check your .env file and ensure LLM_API_KEY is set.")
        return

    # Sidebar: Configuration & Status (matches Epicurean Pulse color palette and metadata)
    with st.sidebar:
        st.markdown("<div style='font-size: 20px; font-weight: 700; color: #1a1c1e; margin-bottom: 16px;'>⚙️ CONFIGURATION</div>", unsafe_allow_html=True)
        from restaurant_recommender.config import get_settings
        settings = get_settings()
        
        st.info(f"**Model:** {settings.llm_model}")
        st.info(f"**Provider:** {settings.llm_provider}")
        
        if not settings.llm_api_key:
            st.warning("⚠️ LLM_API_KEY is missing in .env")
        else:
            st.success("✅ API Key configured")
            
        st.markdown("<hr style='border: none; border-top: 1px solid #74777f; margin: 16px 0;' />", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 14px; font-weight: 600; color: #1a1c1e; margin-bottom: 8px;'>ABOUT</div>", unsafe_allow_html=True)
        st.write("This gastronomy concierge uses the Zomato dataset and Groq LLMs to recommend highly tailored dining spots backed by reasoning.")

    # Main Area: User Input & Recommendations
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.markdown("<div class='headline-medium'>🔍 Your Preferences</div>", unsafe_allow_html=True)
        
        # Location Input with key for bidirectional state binding
        location = st.text_input(
            "Location (City or Neighborhood)", 
            key="location_input",
            placeholder="e.g. Bangalore, Indiranagar"
        )
        
        # Location quick-select chips (ROUND_PILL, changes style when selected)
        st.markdown("<div style='font-size: 11px; font-weight: 600; color: #74777f; margin-top: -8px; margin-bottom: 8px;'>POPULAR CITIES:</div>", unsafe_allow_html=True)
        popular_locs = ["Bangalore", "Delhi", "Mumbai", "Pune"]
        loc_cols = st.columns(len(popular_locs))
        for idx, loc in enumerate(popular_locs):
            with loc_cols[idx]:
                # If current state matches loc, prefix with a checkmark
                label = f"✓ {loc}" if location.strip().lower() == loc.lower() else loc
                if st.button(label, key=f"loc_chip_{loc}"):
                    st.session_state.location_input = loc
                    st.rerun()
        
        st.write("") # spacing

        # Cuisine Input with key for bidirectional state binding
        cuisine = st.text_input(
            "Cuisine preference", 
            key="cuisine_input",
            placeholder="e.g. North Indian, Italian, Chinese"
        )
        
        # Cuisine quick-select chips (ROUND_PILL, changes style when selected)
        st.markdown("<div style='font-size: 11px; font-weight: 600; color: #74777f; margin-top: -8px; margin-bottom: 8px;'>POPULAR CUISINES:</div>", unsafe_allow_html=True)
        popular_cuisines = ["North Indian", "Chinese", "Italian", "South Indian", "Biryani"]
        cuis_cols = st.columns(len(popular_cuisines))
        for idx, cuis in enumerate(popular_cuisines):
            with cuis_cols[idx]:
                label = f"✓ {cuis}" if cuisine.strip().lower() == cuis.lower() else cuis
                if st.button(label, key=f"cuis_chip_{cuis}"):
                    st.session_state.cuisine_input = cuis
                    st.rerun()

        st.write("") # spacing

        # Budget selectbox
        budget_val = st.selectbox(
            "Budget Band",
            options=[b.value.capitalize() for b in Budget],
            index=1 # Default to Medium
        )
        budget = Budget(budget_val.lower())
        
        # Minimum rating slider
        min_rating = st.slider("Minimum Rating", 0.0, 5.0, 4.0, 0.1)
        
        # Free-text additional preferences
        additional = st.text_area(
            "Additional Preferences (Optional)",
            placeholder="e.g. Roof-top seating, family friendly, quiet music...",
            max_chars=2000
        )
        
        st.write("") # spacing
        
        # Action Submit Button (styled in style_utils.py as Crimson, ROUND_EIGHT)
        submit = st.button("Get Recommendations", type="primary", use_container_width=True)

    with col2:
        if submit:
            if not location.strip() or not cuisine.strip():
                st.error("Please provide both location and cuisine preferences.")
            else:
                try:
                    prefs = UserPreferences(
                        location=location.strip(),
                        budget=budget,
                        cuisine=cuisine.strip(),
                        min_rating=min_rating,
                        additional_preferences=additional.strip() if additional.strip() else None
                    )
                    
                    with st.spinner("🧑‍🍳 Our AI is curating your personalized selection..."):
                        response = orchestrator.recommend(prefs)
                    
                    if response.status == RecommendationStatus.SUCCESS:
                        st.markdown(f"<div class='headline-medium'>🎯 Top {len(response.recommendations)} Recommendations</div>", unsafe_allow_html=True)
                        if response.summary:
                            st.info(response.summary)
                        
                        for rec in response.recommendations:
                            render_restaurant_card(rec)
                            
                    elif response.status == RecommendationStatus.NO_MATCHES:
                        st.warning(f"🍱 {response.message}")
                        st.info("Try widening your filters (e.g., lowering the minimum rating or changing the budget).")
                    else:
                        st.error(f"❌ {response.message}")
                        
                except Exception as e:
                    st.error(f"Validation error: {e}")
        else:
            st.markdown(
                """
                <div style="background-color: #ffffff; padding: 48px; border-radius: 8px; text-align: center; border: 1px dashed #74777f;">
                    <h3 style="color: #44474e; font-weight: 600; margin-bottom: 12px;">Waiting for your preferences...</h3>
                    <p style="color: #74777f; font-size: 14px; margin: 0;">Specify your dining criteria on the left to reveal recommendations.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()
