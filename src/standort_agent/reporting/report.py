from pathlib import Path
from standort_agent.reporting.names import format_location_text

from standort_agent.interpretation.rules import profile_for_display, interpret_profile
from standort_agent.scoring.weighting import get_weights

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
)

from standort_agent.reporting.explanation import explain_for_customer

from standort_agent.models import (
    BusinessProfile,
    MunicipalityEvaluation,
)


TEMPLATE_DIR = (
    Path(__file__).parent
    / "templates"
)


def generate_html_report(
    profile: BusinessProfile,
    rankings: list[MunicipalityEvaluation],
    output_path: str | Path,
    customer_explanation: str | None = None,
    llm_status: str | None = None,
) -> Path:
    """
    Generate a standalone HTML report from already-calculated
    ranking results.
    """

    environment = Environment(
        loader=FileSystemLoader(
            TEMPLATE_DIR
        ),
        autoescape=select_autoescape(
            ["html", "xml"]
        ),
    )

    template = environment.get_template(
        "report.html.j2"
    )

    html = template.render(
        profile=profile_for_display(profile),
        rankings=rankings,
        top_results=rankings,
        weights=get_weights(interpret_profile(profile)),
        signals=[('demographics', 'Customer fit', '#3558a7'), ('poi', 'Surrounding activity', '#8b86cc'), ('rent', 'Rent affordability', '#d5983e'), ('transit', 'Public transport', '#65a9d3')],
        rent_max=max([profile.budget_miete_eur] + [r.municipality.mietindex_eur_m2 * profile.flaeche_m2 for r in rankings]) * 1.15,
        customer_explanation=customer_explanation or (explain_for_customer(profile, rankings[0]) if rankings else None),
        llm_status=llm_status,
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        format_location_text(html),
        encoding="utf-8",
    )

    return output_path