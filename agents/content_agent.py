"""Content planning agent for overseas B2B website pages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

CONTENT_AGENT_VERSION = "0.1"


PAGE_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "homepage": {
        "page_goal": "Explain SIRUI's verified manufacturer positioning and guide qualified B2B buyers to products, capabilities, and inquiry.",
        "sections": [
            ("Hero positioning", "State the primary product categories, manufacturer role, target buyer, and one inquiry action."),
            ("Product category overview", "Help buyers reach relevant paint brush and paint roller categories quickly."),
            ("OEM, ODM, and private label", "Summarize only verified customization scope and link to the service page."),
            ("Factory and quality evidence", "Show approved production and quality-control evidence without unsupported claims."),
            ("Buyer process", "Explain the approved path from requirements to sample, quotation, and order without promising terms."),
            ("Primary inquiry CTA", "Ask buyers for product category, quantity, market, packaging, and destination details."),
        ],
        "required_inputs": [
            "Approved company positioning and legal company name",
            "Verified primary product categories",
            "Verified OEM/ODM and private-label scope",
            "Approved factory and quality-control evidence",
        ],
        "cta": {
            "label": "Discuss Your Paint Tool Sourcing Project",
            "supporting_copy": "Share your product categories, target market, quantity, packaging, and destination for sales review.",
        },
    },
    "product_index": {
        "page_goal": "Help importers and distributors understand the verified product range and choose the next sourcing path.",
        "sections": [
            ("Category introduction", "Explain which verified product families are available and who the page serves."),
            ("Product category grid", "Use consistent category names, images, and links to detail pages."),
            ("Buyer selection guidance", "Explain selection factors using verified materials, sizes, applications, and formats."),
            ("OEM and packaging options", "Describe only verified private-label and packaging options."),
            ("Product-range inquiry CTA", "Invite buyers to share the range and market they are sourcing for."),
        ],
        "required_inputs": [
            "Approved product category taxonomy",
            "Verified category descriptions and images",
            "Verified selection attributes by category",
            "Approved OEM and packaging options",
        ],
        "cta": {
            "label": "Request a Product Range Discussion",
            "supporting_copy": "Tell us which paint tool categories, sizes, quantities, and market you are sourcing for.",
        },
    },
    "product_detail": {
        "page_goal": "Give a B2B buyer enough verified product information to assess fit and submit a qualified inquiry.",
        "sections": [
            ("Product summary", "State the verified product name, code, buyer application, and differentiating facts."),
            ("Specifications", "Present verified material, size, dimensions, components, and packaging in a scannable table."),
            ("Applications and selection", "Explain verified use cases and how buyers should select the correct option."),
            ("OEM and private label", "List only verified logo, color, handle, cover, label, packaging, or carton options."),
            ("Quality evidence", "Show approved inspection, production, or test evidence relevant to this product."),
            ("Related products", "Link to genuinely related products and the parent category."),
            ("Product inquiry CTA", "Collect specifications, quantity, customization, packaging, and destination details."),
        ],
        "required_inputs": [
            "Verified product name and product code",
            "Verified material, size, dimensions, components, and applications",
            "Verified customization and packaging options",
            "Approved product images and quality evidence",
        ],
        "cta": {
            "label": "Request Product Information or a Quote",
            "supporting_copy": "Send the required size, material, quantity, customization, packaging, and destination for sales review.",
        },
    },
    "about": {
        "page_goal": "Help overseas buyers verify the supplier using approved company, factory, process, and quality evidence.",
        "sections": [
            ("Company overview", "Use the approved legal identity, location, manufacturer role, and business focus."),
            ("Factory and production", "Explain only verified production processes, equipment, and supported categories."),
            ("Quality-control workflow", "Show verified inspection stages, records, and responsible functions."),
            ("OEM project support", "Explain the approved buyer collaboration process without promising commercial terms."),
            ("Evidence gallery", "Use dated, approved factory, process, team, and quality images with captions."),
            ("Supplier discussion CTA", "Invite buyers to request relevant verified documentation or discuss a sourcing project."),
        ],
        "required_inputs": [
            "Verified legal company identity and factory location",
            "Approved production-process and equipment information",
            "Approved quality-control workflow and evidence",
            "Approved factory, team, and production images",
        ],
        "cta": {
            "label": "Discuss Your Supplier Requirements",
            "supporting_copy": "Share the product range, quality documentation, market, and sourcing requirements you need reviewed.",
        },
    },
    "b2b_service": {
        "page_goal": "Explain the verified OEM, ODM, and private-label process and qualify B2B project inquiries.",
        "sections": [
            ("Service scope", "Define verified OEM, ODM, private-label, logo, color, component, and packaging support."),
            ("Project workflow", "Describe the approved steps from requirement review through sample, quotation, production, and shipment."),
            ("Customization matrix", "Separate verified options by product category and identify constraints requiring sales confirmation."),
            ("Information buyers should provide", "Request product, material, size, quantity, branding, packaging, destination, and timing needs."),
            ("FAQ", "Answer only approved questions; escalate MOQ, price, lead time, payment, and certification to sales."),
            ("OEM project CTA", "Invite a structured project inquiry without promising feasibility or terms."),
        ],
        "required_inputs": [
            "Verified OEM, ODM, and private-label scope by product category",
            "Approved project workflow and responsible teams",
            "Verified customization and packaging matrix",
            "Sales-approved FAQ answers",
        ],
        "cta": {
            "label": "Discuss an OEM or Private-Label Project",
            "supporting_copy": "Send your product, quantity, branding, packaging, destination, and target timing for feasibility review.",
        },
    },
    "contact": {
        "page_goal": "Collect enough information for sales to qualify and route an overseas B2B product inquiry.",
        "sections": [
            ("Inquiry introduction", "Explain who should use the form and what information helps the sales review."),
            ("Buyer and company fields", "Collect name, company, role, website, email, phone, and country."),
            ("Project requirement fields", "Collect product, material, size, quantity, branding, packaging, destination, timing, and sample needs."),
            ("Privacy and consent", "Add approved privacy wording and explain how submitted information will be handled."),
            ("Alternative contact route", "Show only verified sales contact channels and operating details."),
        ],
        "required_inputs": [
            "Approved sales contact details",
            "Approved inquiry form fields and routing owner",
            "Approved privacy and consent wording",
            "Approved response-time wording, if any",
        ],
        "cta": {
            "label": "Send Your Product Requirements",
            "supporting_copy": "Provide your company, product, quantity, customization, packaging, and destination details for review.",
        },
    },
}


COMMON_REQUIRED_INPUTS = [
    "Keyword demand and current ranking data: Needs verification",
    "All claims, specifications, certifications, pricing, MOQ, capacity, and lead-time statements require owner verification",
    "Image ownership and publication approval: Needs verification",
]


def _blueprint_for(page_type: str) -> dict[str, Any]:
    return PAGE_BLUEPRINTS.get(
        page_type,
        {
            "page_goal": "Explain the verified page topic and guide the intended buyer to a clear next action.",
            "sections": [
                ("Page introduction", "Explain the verified purpose and intended audience."),
                ("Supporting information", "Present approved evidence in a clear structure."),
                ("Next action", "Guide the buyer to the appropriate approved conversion route."),
            ],
            "required_inputs": ["Approved page purpose and factual source material"],
            "cta": {
                "label": "Contact SIRUI",
                "supporting_copy": "Share your company and product requirements for sales review.",
            },
        },
    )


def _content_brief(page_plan: dict[str, Any], index: int) -> dict[str, Any]:
    page_type = page_plan.get("page_type", "other")
    blueprint = _blueprint_for(page_type)
    current_metadata = page_plan.get("current_metadata", {})
    keyword_themes = page_plan.get("keyword_themes", {})
    sections = [
        {
            "section": title,
            "objective": objective,
            "evidence_status": "Needs verification",
        }
        for title, objective in blueprint["sections"]
    ]
    return {
        "content_brief_id": f"CONTENT-{index:03d}",
        "url": page_plan.get("url", ""),
        "page_type": page_type,
        "page_goal": blueprint["page_goal"],
        "target_markets": page_plan.get("target_markets", []),
        "target_audiences": page_plan.get("target_audiences", []),
        "search_intent": page_plan.get("search_intent", "Needs verification"),
        "current_metadata": current_metadata,
        "keyword_assignment": {
            "primary": keyword_themes.get("primary", []),
            "secondary": keyword_themes.get("secondary", []),
            "validation_status": keyword_themes.get(
                "validation_status", "needs_keyword_research"
            ),
            "usage_rule": "Use naturally after keyword validation; do not force repetition.",
        },
        "metadata_brief": {
            "title_draft": page_plan.get("metadata_guidance", {}).get(
                "title_pattern", "Needs verification"
            ),
            "meta_description_should_cover": page_plan.get(
                "metadata_guidance", {}
            ).get("meta_description_should_cover", []),
            "draft_status": "approval_required",
        },
        "recommended_sections": sections,
        "required_verified_inputs": blueprint["required_inputs"]
        + COMMON_REQUIRED_INPUTS,
        "cta_draft": {
            **blueprint["cta"],
            "status": "approval_required",
        },
        "editorial_checks": [
            "Use plain, buyer-focused English and avoid unsupported superlatives.",
            "Every factual or commercial claim has an approved source owner.",
            "Product terminology is consistent across title, H1, copy, form, and schema.",
            "The primary keyword is used naturally only after demand validation.",
            "The page has one clear primary conversion action and working destination.",
            "Headings, links, image alt text, mobile layout, and accessibility are reviewed.",
        ],
        "publication_gate": {
            "production_publish_allowed": False,
            "required_approvers": [
                "business fact owner",
                "SEO reviewer",
                "website owner",
            ],
            "status": "brief_only",
        },
    }


def build_content_plan(seo_plan: dict[str, Any]) -> dict[str, Any]:
    """Convert an SEO plan into page-level, approval-gated content briefs."""

    if not isinstance(seo_plan, dict):
        raise ValueError("seo_plan must be a dictionary.")
    page_plans = seo_plan.get("page_plans")
    if not isinstance(page_plans, list):
        raise ValueError("seo_plan must contain a page_plans list.")

    briefs = [
        _content_brief(page_plan, index)
        for index, page_plan in enumerate(page_plans, start=1)
    ]
    page_type_counts: dict[str, int] = {}
    for brief in briefs:
        page_type = brief["page_type"]
        page_type_counts[page_type] = page_type_counts.get(page_type, 0) + 1

    return {
        "content_agent_version": CONTENT_AGENT_VERSION,
        "source_seo_agent_version": seo_plan.get("seo_agent_version", "unknown"),
        "source_url": seo_plan.get("source_url", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "content_briefs": len(briefs),
            "briefs_by_page_type": page_type_counts,
            "production_pages_authorized": 0,
        },
        "content_policy": {
            "default_status": "brief_only",
            "production_publish_allowed": False,
            "human_approval_required": True,
            "unverified_value": "Needs verification",
        },
        "content_briefs": briefs,
        "global_definition_of_done": [
            "All factual and commercial statements are verified by a named owner.",
            "Keyword demand and page assignment are reviewed by SEO.",
            "The draft answers the target buyer's page-specific questions.",
            "The CTA destination, inquiry fields, privacy wording, and routing are tested.",
            "The approved content passes content, SEO, legal or privacy, and website review before publication.",
        ],
    }
