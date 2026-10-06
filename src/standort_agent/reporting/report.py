from pathlib import Path

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
        profile=profile,
        rankings=rankings,
        top_results=rankings[:5],
        customer_explanation=explain_for_customer(profile, rankings[0]) if rankings else None,
    )

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        html,
        encoding="utf-8",
    )

    return output_path