from standort_agent.models import BusinessProfile, MunicipalityEvaluation


def explain_for_customer(
    profile: BusinessProfile,
    evaluation: MunicipalityEvaluation,
) -> str:
    """Translate measured signals into plain language without new claims."""
    name = evaluation.municipality.gemeinde
    introduction = (
        f"{name} is worth a closer look for your business."
        if evaluation.total_score >= 60
        else f"{name} ranks first among the locations compared, but the results suggest a cautious approach."
    )
    demographics = evaluation.signals["demographics"].score
    if demographics >= 70:
        audience = "Its mix of residents and population size compares well with other locations for your chosen customer age groups."
    elif demographics >= 40:
        audience = "Its mix of residents and population size offers a moderate match for your chosen customer age groups."
    else:
        audience = "Its mix of residents and population size is a weaker match for your chosen customer age groups, so check local demand carefully."

    poi = evaluation.signals["poi"].score
    if poi >= 70:
        surroundings = "The area has relatively dense nearby amenities and businesses, which may help you reach customers already visiting the area."
    elif poi >= 40:
        surroundings = "Nearby amenities and businesses offer some surrounding activity, though busier alternatives exist in the dataset."
    else:
        surroundings = "Nearby amenities and businesses are relatively sparse, so you may need to invest more in attracting customers to the location."

    transit = evaluation.signals["transit"].score
    access = (
        "Strong public transport connections can make it easier for customers to visit without a car."
        if transit >= 70 else
        "Public transport access is moderate; check whether the available routes suit your customers."
        if transit >= 40 else
        "Limited public transport access could make visits harder for customers who do not drive."
    )
    monthly_rent = evaluation.municipality.mietindex_eur_m2 * profile.flaeche_m2
    difference = monthly_rent - profile.budget_miete_eur
    if difference > 0:
        rent = (
            f"For your {profile.flaeche_m2:,.0f} m² space, estimated rent is €{monthly_rent:,.0f} per month—"
            f"€{difference:,.0f} above your budget. This is a trade-off to resolve before proceeding."
        )
    elif difference < 0:
        rent = (
            f"Estimated rent for your {profile.flaeche_m2:,.0f} m² space is €{monthly_rent:,.0f} per month, "
            f"leaving €{abs(difference):,.0f} within your rent budget."
        )
    else:
        rent = f"Estimated rent is €{monthly_rent:,.0f} per month, exactly matching your rent budget with no rent headroom."

    conclusion = (
        "Use this comparison to choose where to investigate next. Check actual premises, rental quotes "
        "and customer demand locally: these estimates use simplified, synthetic data and do not predict sales."
    )
    return "\n\n".join([introduction, audience, surroundings, access, rent, conclusion])
