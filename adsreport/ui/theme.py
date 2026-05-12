"""Design tokens and Plotly theme configuration."""

from __future__ import annotations

from typing import Any

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


def get_tokens(_theme: str = "light") -> dict[str, str]:
    return LIGHT


def plotly_template(theme: str = "light") -> dict[str, Any]:
    t = get_tokens(theme)
    return {
        "layout": {
            "paper_bgcolor": t["surface"],
            "plot_bgcolor": t["surface"],
            "font": {"color": t["text_primary"], "family": t["font_family"]},
            "colorway": [
                t["accent"],
                t["success"],
                t["warning"],
                t["danger"],
                "#A78BFA",
                "#34D399",
                "#FB923C",
                "#60A5FA",
            ],
            "xaxis": {"gridcolor": t["border"], "linecolor": t["border"]},
            "yaxis": {"gridcolor": t["border"], "linecolor": t["border"]},
            "legend": {"bgcolor": t["surface_elevated"]},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        }
    }
