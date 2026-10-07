from pathlib import Path

import gradio as gr
from pydantic import ValidationError

from standort_agent.interpretation.rules import profile_input_errors

from standort_agent.graph.workflow import (
    location_graph,
)
from standort_agent.loader import (
    load_municipalities,
)
from standort_agent.models import (
    BusinessProfile,
)
from standort_agent.reporting.explanation import explain_for_customer
from standort_agent.reporting.report import (
    generate_html_report,
)


PROJECT_ROOT = (
    Path(__file__).resolve().parents[3]
)

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "municipalities.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "output"
    / "report.html"
)


DATASET = load_municipalities(
    DATA_PATH
)


def analyze_location(
    branche: str,
    flaeche_m2: float,
    zielgruppe: str,
    budget_miete_eur: float,
    region_praeferenz: str | list[str],
):
    """
    Convert Gradio input into a BusinessProfile, execute the
    LangGraph workflow, generate the HTML report and prepare
    UI output.
    """

    # 1. Build validated business profile

    values = dict(
        branche=branche, flaeche_m2=flaeche_m2, zielgruppe=zielgruppe,
        budget_miete_eur=budget_miete_eur, region_praeferenz=region_praeferenz,
    )
    errors = []
    try:
        profile = BusinessProfile(**values)
    except ValidationError as exc:
        labels = {
            "branche": "Business / Industry",
            "zielgruppe": "Target group",
            "region_praeferenz": "Preferred region",
            "flaeche_m2": "Required area (m²)",
            "budget_miete_eur": "Monthly rent budget (€)",
        }
        for error in exc.errors():
            field = error["loc"][0]
            errors.append(f"{labels.get(field, field)}: {error['msg']}.")
        # Report unrecognized text even when numeric fields are invalid.
        text_profile = values | {"flaeche_m2": 11, "budget_miete_eur": 200}
        try:
            errors.extend(profile_input_errors(BusinessProfile(**text_profile)))
        except ValidationError:
            pass
    else:
        errors = profile_input_errors(profile)
    if errors:
        return [], "## Please check your input\n\n" + "\n\n".join(errors), None


    # 2. Run LangGraph workflow

    result = location_graph.invoke(
        {
            "raw_profile": profile,
            "municipalities": (
                DATASET.municipalities
            ),
        }
    )


    # 3. Handle unsupported/out-of-scope requests

    if result.get("error"):

        error_message = f"""
## Unable to recommend locations

{result["error"]}

The current PoC specializes in **Austria**.

Try for example:

- Österreich
- Wien
- Graz
- Linz
- Steiermark
- Tirol
"""

        return (
            [],
            error_message,
            None,
        )


    # 4. Generate standalone HTML report

    if not result.get("top_results"):
        return [], "## No matching locations\n\nTry a different Austrian region.", None

    report_path = generate_html_report(
        profile=profile,
        rankings=result["rankings"],
        output_path=OUTPUT_PATH,
        customer_explanation=result.get("customer_explanation"),
        llm_status=result.get("llm_status"),
    )


    # 5. Build table shown in Gradio

    rows = []

    for evaluation in result[
        "top_results"
    ]:

        municipality = (
            evaluation.municipality
        )

        rows.append(
            [
                municipality.gemeinde,
                municipality.bundesland,
                round(
                    evaluation.total_score,
                    1,
                ),
                round(
                    evaluation.signals[
                        "demographics"
                    ].score,
                    1,
                ),
                round(
                    evaluation.signals[
                        "poi"
                    ].score,
                    1,
                ),
                round(
                    evaluation.signals[
                        "rent"
                    ].score,
                    1,
                ),
                round(
                    evaluation.signals[
                        "transit"
                    ].score,
                    1,
                ),
            ]
        )


    # 6. Build explanation for best location

    best = result[
        "top_results"
    ][0]

    summary = f"""
## Best match: {best.municipality.gemeinde}

**Overall score: {best.total_score:.1f}/100**

### Why it fits

**Demographics — {best.signals["demographics"].score:.1f}/100**

{best.signals["demographics"].reason}

**POI — {best.signals["poi"].score:.1f}/100**

{best.signals["poi"].reason}

**Rent — {best.signals["rent"].score:.1f}/100**

{best.signals["rent"].reason}

**Public transport — {best.signals["transit"].score:.1f}/100**

{best.signals["transit"].reason}
"""


    # 7. Return outputs to Gradio

    summary += "\n\n## What this means for your business\n\n" + (result.get("customer_explanation") or explain_for_customer(profile, best))
    if not result.get("llm_status", "").startswith("Groq LLM analysis:"):
        summary += "\n\n" + result.get("llm_status", "Offline mode")

    return (
        rows,
        summary,
        str(report_path),
    )


def analyze_with_error_popup(*inputs):
    """Clear obsolete outputs before showing any validation or scope error."""
    result = analyze_location(*inputs)
    yield result
    if result[2] is None:
        message = result[1].replace("## ", "").replace("**", "")
        raise gr.Error(message)


# GRADIO USER INTERFACE


with gr.Blocks(
    title="Standort Agent"
) as demo:

    gr.Markdown(
        """
# Standort Agent

### Explainable location recommendations for Austria

Enter a business profile and the system will compare
candidate municipalities using demographics, surrounding
activity, rent affordability and public transport.
"""
    )


    # Business input

    with gr.Row():

        branche = gr.Dropdown(
            label="Business / Industry",
            choices=[
                ("Retail / Shops", "retail"),
                ("Gastronomy / Café", "cafe"),
                ("Fitness / Wellness", "fitness"),
                ("Logistics", "logistics"),
            ],
            value="retail",
            allow_custom_value=False,
            info="Choose the industry that best matches your business.",
        )

        flaeche_m2 = gr.Textbox(
            label="Required area (m²)",
            value="200",
            info="Positive number up to 100,000 m². Use 200 or 200.5; no letters or scientific notation.",
        )


    with gr.Row():

        zielgruppe = gr.Dropdown(
            label="Target group",
            choices=[
                ("Young professionals (25–40)", "young_professionals"),
                ("Students and families", "students_families"),
                ("Health-conscious adults aged 30+", "adults_30_plus"),
            ],
            value="young_professionals",
            allow_custom_value=False,
            info="Choose the customer group you want to reach.",
        )

        budget_miete_eur = gr.Textbox(
            label="Monthly rent budget (€)",
            value="4000",
            info="Monthly budget from €200 to €10,000,000. Use 4000 or 4000.5; no letters or scientific notation.",
        )


    gr.Markdown(
        "**Want more choices?** A subscription will give you access to more "
        "industry and target-group options. Subscription features are planned "
        "and are not available in this demo yet."
    )

    region_praeferenz = gr.Dropdown(
        label="Preferred regions",
        choices=[
            ("All Austria", "Österreich"),
            *[(location, location) for location in sorted(
                {item.bundesland for item in DATASET.municipalities}
                | {item.gemeinde.split("(", 1)[0].strip() for item in DATASET.municipalities}
            )],
        ],
        value=["Wien"],
        multiselect=True,
        allow_custom_value=False,
        info="Select one or more cities or federal states. Results match any selection. Select All Austria on its own. Salzburg includes the entire federal state.",
    )


    analyze_button = gr.Button(
        "Analyze Locations",
        variant="primary",
    )


    # Ranking output

    gr.Markdown(
        "## Recommended Locations"
    )


    ranking_table = gr.Dataframe(
        headers=[
            "Municipality",
            "Federal State",
            "Overall Score",
            "Demographics",
            "POI",
            "Rent",
            "Transit",
        ],
        datatype=[
            "str",
            "str",
            "number",
            "number",
            "number",
            "number",
            "number",
        ],
        interactive=False,
    )


    # Explanation

    summary_output = gr.Markdown()


    # HTML report

    report_file = gr.File(
        label="Standalone HTML Report",
        interactive=False,
    )


    # Button action

    analyze_button.click(
        fn=analyze_with_error_popup,
        inputs=[
            branche,
            flaeche_m2,
            zielgruppe,
            budget_miete_eur,
            region_praeferenz,
        ],
        outputs=[
            ranking_table,
            summary_output,
            report_file,
        ],
    )


if __name__ == "__main__":
    demo.launch()
