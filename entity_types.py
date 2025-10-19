"""
Entity Types for Graphiti Knowledge Graph

These entity types guide the LLM during entity extraction, improving:
1. Entity classification accuracy
2. Semantic relationship extraction (WORKS_AT, FOUNDED, etc. instead of generic MENTIONS)
3. Entity deduplication (better context for matching)

Easily extensible - add new types as needed for domain-specific entities.
"""

from pydantic import BaseModel, Field


class Person(BaseModel):
    """
    An individual human being.

    Examples: employees, founders, executives, board members, consultants,
    clients, partners, stakeholders, contractors.

    Use full names when available (e.g., "John Smith" not "John").
    Include titles only if part of the name (e.g., "Dr. Jane Doe").
    """
    pass


class Organization(BaseModel):
    """
    A company, business entity, or institution.

    Examples: corporations, LLCs, partnerships, non-profits, government agencies,
    departments, divisions, subsidiaries, clients, vendors, partners.

    Use official legal names when available.
    Include entity type suffixes (Inc., LLC, Ltd.) if mentioned.
    """
    pass


class Project(BaseModel):
    """
    A defined initiative, product, or program of work.

    Examples: product names, internal projects, initiatives, programs,
    campaigns, research efforts, development efforts, strategic plans.

    Use official project names/codenames.
    Distinguish between products (customer-facing) and internal projects.
    """
    pass


class Location(BaseModel):
    """
    A geographic place or address.

    Examples: countries, states, cities, addresses, office locations,
    headquarters, jurisdictions, regions, facilities.

    Use most specific location mentioned (e.g., "San Francisco, CA" not just "California").
    Include full addresses when available.
    """
    pass


class LegalTerm(BaseModel):
    """
    Legal concepts, contract types, or compliance terms.

    Examples: contracts, agreements, clauses, legal obligations,
    compliance requirements, regulations, laws, legal entities,
    NDAs, SOWs, MSAs, terms of service.

    Use specific legal terminology when available.
    Include contract types (e.g., "Non-Disclosure Agreement" not just "agreement").
    """
    pass


class FinancialMetric(BaseModel):
    """
    Financial data, metrics, or monetary values.

    Examples: revenue figures, valuations, investments, budgets,
    costs, expenses, profits, losses, financial ratios, KPIs,
    funding amounts, pricing.

    Include currency and amounts when mentioned.
    Distinguish between different types of financial metrics.
    """
    pass


class Technology(BaseModel):
    """
    Software, platforms, tools, or technical systems.

    Examples: programming languages, frameworks, libraries,
    platforms, tools, databases, APIs, cloud services,
    software products, hardware, infrastructure.

    Use official product/technology names.
    Include versions if mentioned and relevant.
    """
    pass


class Event(BaseModel):
    """
    A specific occurrence or time-bound happening.

    Examples: meetings, launches, releases, announcements,
    milestones, deadlines, conferences, presentations,
    fiscal periods (Q1 2024), project phases.

    Include dates/timeframes when mentioned.
    Be specific about event type and context.
    """
    pass


class Document(BaseModel):
    """
    Written or digital documentation.

    Examples: reports, presentations, proposals, specifications,
    policies, procedures, manuals, guides, forms, records,
    certificates, licenses.

    Use official document titles when available.
    Include document types (e.g., "Annual Report 2024").
    """
    pass


class Concept(BaseModel):
    """
    Abstract ideas, methodologies, or domain concepts.

    Examples: business strategies, methodologies (Agile, Scrum),
    theoretical concepts, principles, approaches, models,
    frameworks (not software), business models.

    Use for important abstract concepts that don't fit other categories.
    Avoid over-extraction - focus on significant concepts.
    """
    pass


# Entity types dictionary for Graphiti
# Maps type names to Pydantic model classes
entity_types = {
    "Person": Person,
    "Organization": Organization,
    "Project": Project,
    "Location": Location,
    "LegalTerm": LegalTerm,
    "FinancialMetric": FinancialMetric,
    "Technology": Technology,
    "Event": Event,
    "Document": Document,
    "Concept": Concept,
}


# Example usage:
# await graphiti.add_episode(
#     name="document.pdf",
#     episode_body=content,
#     source=EpisodeType.text,
#     source_description="My document",
#     reference_time=datetime.now(timezone.utc),
#     entity_types=entity_types,  # <-- Pass this
# )
