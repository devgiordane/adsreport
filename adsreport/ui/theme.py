"""Design tokens and Plotly theme configuration."""

from __future__ import annotations

from typing import Any

# ── Dark theme tokens ─────────────────────────────────────────────────────────
DARK = {
    "bg": "#0B0D10",
    "surface": "#14171C",
    "surface_elevated": "#1B1F26",
    "border": "#232831",
    "text_primary": "#E6E8EB",
    "text_muted": "#8A93A0",
    "accent": "#4F8DFD",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "font_family": "Inter, system-ui, sans-serif",
    "radius_sm": "8px",
    "radius_md": "12px",
    "radius_lg": "16px",
}

# ── Light theme tokens ────────────────────────────────────────────────────────
LIGHT = {
    "bg": "#F8FAFC",
    "surface": "#FFFFFF",
    "surface_elevated": "#F1F5F9",
    "border": "#E2E8F0",
    "text_primary": "#0F172A",
    "text_muted": "#64748B",
    "accent": "#3B6FE0",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
    "font_family": "Inter, system-ui, sans-serif",
    "radius_sm": "8px",
    "radius_md": "12px",
    "radius_lg": "16px",
}


def get_tokens(theme: str = "dark") -> dict[str, str]:
    return DARK if theme == "dark" else LIGHT


def plotly_template(theme: str = "dark") -> dict[str, Any]:
    t = get_tokens(theme)
    return {
        "layout": {
            "paper_bgcolor": t["surface"],
            "plot_bgcolor": t["surface"],
            "font": {"color": t["text_primary"], "family": t["font_family"]},
            "colorway": [t["accent"], t["success"], t["warning"], t["danger"],
                         "#A78BFA", "#34D399", "#FB923C", "#60A5FA"],
            "xaxis": {"gridcolor": t["border"], "linecolor": t["border"]},
            "yaxis": {"gridcolor": t["border"], "linecolor": t["border"]},
            "legend": {"bgcolor": t["surface_elevated"]},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        }
    }
