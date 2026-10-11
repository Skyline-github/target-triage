"""雷达图配置（概览页与静态存档共用）。"""
from __future__ import annotations

from ..models import AssessmentReport


def radar_chart_config(report: AssessmentReport) -> dict:
    d = report.radar_data
    point_colors = {"green": "#2e6b5e", "yellow": "#d9b25f",
                    "red": "#c0504d", "unknown": "#9aa5a1"}
    return {
        "type": "radar",
        "data": {
            "labels": d["labels"],
            "datasets": [{
                "label": "五问状态",
                "data": d["values"],
                "backgroundColor": "rgba(46,107,94,.22)",
                "borderColor": "#2e6b5e",
                "borderWidth": 2,
                "pointBackgroundColor": [point_colors.get(s, "#9aa5a1")
                                         for s in d["statuses"]],
            }],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {"legend": {"display": False}},
            "scales": {"r": {
                "min": 0, "max": 3,
                "ticks": {"stepSize": 1, "backdropColor": "transparent"},
                "pointLabels": {"font": {"size": 11}},
                "grid": {"color": "#e3e9e6"},
                "angleLines": {"color": "#e3e9e6"},
            }},
        },
    }
