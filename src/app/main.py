"""
Streamlit entry point.

Run locally:
    streamlit run src/app/main.py
"""

from __future__ import annotations

import html
from typing import Any, Callable

import streamlit as st
from pydantic import ValidationError

from config.settings import get_settings
from src.app.pipeline import run_recommendation


def _inject_css() -> None:
    """
    UI styling based on stitch_zomoto_ai_recommendations/DESIGN.md + code.html.

    Streamlit doesn't let us fully control markup of native inputs, but we can:
    - set global typography/colors
    - style inputs/buttons via CSS selectors
    - render result cards with small HTML blocks
    """
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

:root{
  --bg: #fff8f7;
  --surface: #ffffff;
  --surface-low: #fff0ef;
  --surface-med: #ffe9e8;
  --outline: #e4bebc;
  --text: #271717;
  --muted: #5b403f;
  --primary: #b7122a;
  --primary-container: #db313f;
  --secondary: #006492;
  --tertiary: #006762;
  --shadow1: 0 2px 8px rgba(0,0,0,0.05);
  --shadow2: 0 4px 12px rgba(0,0,0,0.08);
  --r-md: 12px;
  --r-lg: 16px;
}

html, body, [class*="stApp"]{
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* Remove Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Constrain width like the Stitch layout */
.block-container{
  padding-top: 1.25rem;
  padding-bottom: 2.5rem;
  max-width: 1200px;
}

/* Buttons */
div.stFormSubmitButton > button{
  border-radius: 14px !important;
  border: 1px solid transparent !important;
  padding: 0.85rem 1rem !important;
  font-weight: 700 !important;
  background: var(--primary) !important;
  color: #fff !important;
  box-shadow: var(--shadow2) !important;
}
div.stFormSubmitButton > button:hover{
  background: var(--primary-container) !important;
}

div.stButton > button {
  border-radius: 14px !important;
  border: 1px solid var(--outline) !important;
  padding: 0.85rem 1rem !important;
  font-weight: 700 !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  box-shadow: var(--shadow1) !important;
  transition: all 0.2s ease !important;
}
div.stButton > button:hover {
  background: var(--surface-low) !important;
  border-color: var(--primary) !important;
  color: var(--primary) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--shadow2) !important;
}

/* Cards */
.z-card{
  background: var(--surface);
  border: 1px solid rgba(228,190,188,0.65);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow1);
}
.z-card-pad{ padding: 1rem 1rem; }

.z-title{
  font-size: 34px;
  line-height: 42px;
  letter-spacing: -0.02em;
  font-weight: 700;
  margin: 0;
}
.z-subtitle{
  color: var(--muted);
  font-size: 14px;
  line-height: 20px;
  margin-top: 0.25rem;
}
.z-label{
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--muted);
}
.z-chip{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid rgba(228,190,188,0.85);
  border-radius: 9999px;
  color: var(--muted);
  background: #fff;
  font-size: 12px;
  font-weight: 700;
}
.z-chip-primary{
  border-color: rgba(183,18,42,0.35);
  color: var(--primary);
  background: rgba(183,18,42,0.06);
}
.z-banner{
  border-radius: var(--r-lg);
  border: 1px solid rgba(0,100,146,0.25);
  background: rgba(0,100,146,0.06);
  padding: 1rem 1rem;
}

/* Inputs */
div[data-baseweb="select"] > div{
  background: var(--surface-low) !important;
  border: none !important;
  border-radius: 12px !important;
}
div[data-baseweb="textarea"] textarea{
  background: var(--surface-low) !important;
  border: none !important;
  border-radius: 12px !important;
}

/* Radio as segmented (budget) */
div[role="radiogroup"]{
  background: var(--surface-low);
  padding: 6px;
  border-radius: 12px;
  border: 1px solid rgba(228,190,188,0.45);
}
div[role="radiogroup"] label{
  border-radius: 10px !important;
  padding: 8px 10px !important;
  margin: 0 4px !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _top_bar() -> None:
    st.markdown(
        """
<div class="z-card z-card-pad" style="display:flex; align-items:center; justify-content:space-between; gap:16px;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="width:40px; height:40px; border-radius:9999px; background:rgba(183,18,42,0.1); display:flex; align-items:center; justify-content:center; color:var(--primary);">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/>
        <path d="M7 2v20"/>
        <path d="M21 15V2v0a5 5 0 0 0-5 5v3c0 1.1.9 2 2 2h3Zm0 0v7"/>
      </svg>
    </div>
    <div>
      <div style="font-weight:800; font-size:18px; line-height:22px;">Zomoto</div>
      <div class="z-subtitle">AI-powered dining · Find restaurants that match your budget, taste, and vibe</div>
    </div>
  </div>
  <div class="z-chip z-chip-primary">POWERED BY AI</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_empty_state(set_example: Callable[..., None]) -> None:
    # From Stitch code.html (can be replaced with local assets later)
    hero_url = "https://lh3.googleusercontent.com/aida-public/AB6AXuD7gMwjFFF0YTMtW2SjEH5OGa2sS1y6NtrXmUF091OHb9f4O0nAJIPuhnu_qWB9EC2j1l83r-giUJTvqSQMhTTw5uMEWHNpdafI4ReDAfhXttYqmgSAbC-nYKCvU5ATwRWoylvMKhUQKsSbCzyjF40rqS48O7Lp1zs4n0SygqfCkZEQL2RX5zJpOul8OTjwFOAGDBtQFGjFaBYM_EEGfPHqYJF1UZMKD4VYflU7kcwnOeShRoE7zJKWP0hB5m6Z_L6lvo16Vot9mg"
    st.markdown(
        """
<div style="display:flex; flex-direction:column; align-items:center; text-align:center; gap:14px; padding: 12px 0;">
  <div style="max-width:520px;">
    <div style="border-radius:24px; overflow:hidden; box-shadow: var(--shadow2); border: 1px solid rgba(228,190,188,0.55);">
      <img src="{hero}" style="width:100%; display:block;"/>
    </div>
    <div style="margin-top:-18px; display:flex; justify-content:flex-end;">
      <div class="z-card z-card-pad" style="border-radius:18px; width:max-content;">
        <span class="z-chip z-chip-primary">★ Top Rated</span>
      </div>
    </div>
  </div>
  <div>
    <div style="font-size:28px; line-height:34px; letter-spacing:-0.01em; font-weight:800;">Tell us what you’re craving...</div>
    <div style="color:var(--muted); max-width:640px; margin-top:6px;">
      The more details you provide, the better our AI can tailor its culinary suggestions to your unique palate.
    </div>
  </div>
</div>
        """.format(hero=html.escape(hero_url)),
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.button(
            "Italian in Indiranagar",
            use_container_width=True,
            on_click=set_example,
            kwargs=dict(
                location="Indiranagar",
                budget="medium",
                cuisine="Italian",
                min_rating=4.0,
                additional="family-friendly",
                run_immediately=True,
            ),
        )
    with c2:
        st.button(
            "Romantic in Koramangala",
            use_container_width=True,
            on_click=set_example,
            kwargs=dict(
                location="Koramangala 5th Block",
                budget="high",
                cuisine="Italian",
                min_rating=4.0,
                additional="romantic, quiet ambience",
                run_immediately=True,
            ),
        )
    with c3:
        st.button(
            "Street Food in BTM",
            use_container_width=True,
            on_click=set_example,
            kwargs=dict(
                location="BTM",
                budget="low",
                cuisine=None,
                min_rating=4.0,
                additional="street food, quick service",
                run_immediately=True,
            ),
        )


def _render_reco_card(
    *,
    rank: int,
    name: str,
    cuisines: str,
    rating: str,
    cost: str,
    explanation: str,
) -> None:
    st.markdown(
        """
<div class="z-card z-card-pad" style="margin-bottom: 12px;">
  <div style="font-weight:800; font-size:18px; line-height:24px;">#{rank} — {name}</div>
  <div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:8px;">
    <span class="z-chip">{cuisines}</span>
    <span class="z-chip">{rating}</span>
    <span class="z-chip z-chip-primary">{cost}</span>
  </div>
  <div style="margin-top:10px; line-height: 1.55;">
    {explanation}
  </div>
</div>
        """.format(
            rank=rank,
            name=html.escape(name),
            cuisines=html.escape(cuisines),
            rating=html.escape(rating),
            cost=html.escape(cost),
            explanation=html.escape(explanation or "—"),
        ),
        unsafe_allow_html=True,
    )


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title="Zomoto — AI Recommendations", page_icon="🍽️", layout="wide")
    _inject_css()
    _top_bar()

    from src.data.repository import get_repository

    repo = get_repository()
    with st.spinner("Loading restaurant dataset..."):
        try:
            repo.ensure_loaded()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not load the dataset: {exc}")
            return



    if not settings.llm_configured():
        st.markdown(
            '<div class="z-banner"><div style="font-weight:800;">AI ranking unavailable</div>'
            '<div class="z-subtitle">Set <code>GROQ_API_KEY</code> to enable AI ranking. '
            "For now, results will be ranked by rating (fallback mode).</div></div>",
            unsafe_allow_html=True,
        )

    from src.models.preferences import UserPreferences
    from src.models.recommendation import EmptyFilterResult, RecommendationResult

    # Two-column layout: left form, right results (as in Stitch screenshot)
    left, right = st.columns([0.42, 0.58], gap="large")

    def set_example(
        *,
        location: str,
        budget: str,
        cuisine: str | None,
        min_rating: float,
        additional: str | None,
        run_immediately: bool = False,
    ) -> None:
        st.session_state["pref_location"] = location
        st.session_state["pref_budget"] = budget
        st.session_state["pref_cuisine"] = cuisine or ""
        st.session_state["pref_min_rating"] = float(min_rating)
        st.session_state["pref_additional"] = additional or ""
        if run_immediately:
            st.session_state["run_immediately"] = True
        st.rerun()

    # Session defaults for "chips"
    locations = repo.get_locations()
    if "pref_location" not in st.session_state:
        st.session_state["pref_location"] = "Indiranagar" if "Indiranagar" in locations else locations[0]
    if "pref_budget" not in st.session_state:
        st.session_state["pref_budget"] = "medium"
    if "pref_cuisine" not in st.session_state:
        st.session_state["pref_cuisine"] = ""
    if "pref_min_rating" not in st.session_state:
        st.session_state["pref_min_rating"] = float(settings.default_min_rating)
    if "pref_additional" not in st.session_state:
        st.session_state["pref_additional"] = ""

    submitted = False
    city = ""
    budget = "medium"
    cuisine = ""
    min_rating = float(settings.default_min_rating)
    extras = ""

    with left:
        st.markdown(
            """
<div style="margin-top:10px;">
  <div class="z-title">Refine Your Taste</div>
  <div class="z-subtitle">Let our AI curator find your next perfect meal.</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("prefs_form", clear_on_submit=False):
            st.markdown('<div class="z-label">CITY</div>', unsafe_allow_html=True)
            city = st.selectbox(
                "City",
                locations,
                index=locations.index(st.session_state["pref_location"])
                if st.session_state["pref_location"] in locations
                else 0,
                label_visibility="collapsed",
            )

            st.markdown('<div class="z-label" style="margin-top:10px;">BUDGET</div>', unsafe_allow_html=True)
            budget_label = st.radio(
                "Budget",
                ["Low", "Medium", "High"],
                horizontal=True,
                index=["low", "medium", "high"].index(st.session_state["pref_budget"]),
                label_visibility="collapsed",
            )
            budget = budget_label.lower()

            st.markdown('<div class="z-label" style="margin-top:10px;">CUISINE</div>', unsafe_allow_html=True)
            cuisine = st.selectbox(
                "Cuisine",
                [""] + repo.get_cuisines(),
                index=([""] + repo.get_cuisines()).index(st.session_state["pref_cuisine"])
                if st.session_state["pref_cuisine"] in ([""] + repo.get_cuisines())
                else 0,
                label_visibility="collapsed",
            )

            l, r = st.columns([0.7, 0.3])
            with l:
                st.markdown('<div class="z-label" style="margin-top:10px;">MINIMUM RATING</div>', unsafe_allow_html=True)
            with r:
                st.markdown(
                    f'<div style="margin-top:10px; text-align:right; font-weight:700; color: var(--primary);">{float(st.session_state["pref_min_rating"]):.1f}+</div>',
                    unsafe_allow_html=True,
                )

            min_rating = st.slider(
                "Minimum rating",
                0.0,
                5.0,
                float(st.session_state["pref_min_rating"]),
                0.5,
                label_visibility="collapsed",
            )

            st.markdown('<div class="z-label" style="margin-top:10px;">ADDITIONAL VIBES</div>', unsafe_allow_html=True)
            extras = st.text_area(
                "Additional preferences",
                value=st.session_state["pref_additional"],
                max_chars=settings.max_additional_preferences_length,
                placeholder="e.g., family-friendly, rooftop, pet-friendly, quiet for work...",
                label_visibility="collapsed",
                height=90,
            )

            submitted = st.form_submit_button("Get Recommendations")

        st.button(
            "Reset Preferences",
            use_container_width=True,
            on_click=set_example,
            kwargs=dict(
                location="Indiranagar" if "Indiranagar" in locations else locations[0],
                budget="medium",
                cuisine=None,
                min_rating=float(settings.default_min_rating),
                additional=None,
                run_immediately=False,
            ),
        )

    run_now = submitted or st.session_state.get("run_immediately", False)
    result: RecommendationResult | EmptyFilterResult | None = None
    if run_now:
        st.session_state["run_immediately"] = False
        st.session_state["pref_location"] = city
        st.session_state["pref_budget"] = budget
        st.session_state["pref_cuisine"] = cuisine
        st.session_state["pref_min_rating"] = float(min_rating)
        st.session_state["pref_additional"] = extras

        try:
            prefs = UserPreferences(
                location=city,
                budget=budget,  # type: ignore[arg-type]
                cuisine=cuisine or None,
                min_rating=min_rating,
                additional_preferences=extras or None,
            )
        except ValidationError as exc:
            with right:
                st.error(f"Invalid input: {exc}")
            return

        with right:
            with st.spinner("Finding the best matches..."):
                result = run_recommendation(prefs, settings=settings, repository=repo)

    with right:
        if result is None:
            _render_empty_state(set_example)
        elif isinstance(result, EmptyFilterResult):
            st.markdown(
                '<div class="z-card z-card-pad">'
                "<div style='font-weight:800; font-size:18px;'>No matches found</div>"
                f"<div class='z-subtitle' style='margin-top:6px;'>{html.escape(result.message)}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if result.suggestions:
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="z-label">TRY THIS</div>', unsafe_allow_html=True)
                for tip in result.suggestions:
                    st.markdown(
                        f'<div style="margin-top:8px;"><span class="z-chip">{html.escape(tip)}</span></div>',
                        unsafe_allow_html=True,
                    )
        else:
            assert isinstance(result, RecommendationResult)
            
            # Dynamically style the first element to have a top margin of 14px to align with the form
            banner_style = 'style="margin-top:14px;"' if result.used_fallback else ""
            summary_style = 'style="margin-top:14px;"' if (not result.used_fallback and result.summary) else ""
            title_margin = "14px 0 10px" if (not result.used_fallback and not result.summary) else "6px 0 10px"

            if result.used_fallback:
                st.markdown(
                    f'<div class="z-banner" {banner_style}>'
                    "<div style='font-weight:800;'>AI ranking unavailable right now</div>"
                    "<div class='z-subtitle'>Showing top picks by rating (fallback mode).</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

            if result.summary:
                st.markdown(
                    f'<div class="z-card z-card-pad" {summary_style}>'
                    "<div style='font-weight:800; font-size:18px;'>Summary</div>"
                    f"<div style='margin-top:6px; color: var(--muted);'>{html.escape(result.summary)}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            st.markdown(
                f'<div style="font-weight:800; font-size:18px; margin: {title_margin};">Top picks</div>',
                unsafe_allow_html=True,
            )
            for item in result.items:
                r = item.restaurant
                cuisines_txt = ", ".join(r.cuisines) if r.cuisines else "—"
                rating_txt = "Rating: —" if r.rating is None else f"Rating: {r.rating:.1f}/5"
                _render_reco_card(
                    rank=item.rank,
                    name=r.name,
                    cuisines=cuisines_txt,
                    rating=rating_txt,
                    cost=r.display_cost,
                    explanation=item.explanation or "",
                )


if __name__ == "__main__":
    main()
