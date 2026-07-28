"""Product taxonomy: synonyms and HS code resolution for trade enrichment."""

from __future__ import annotations

from .storage import ResearchStore

TAXONOMY_NAME = "cacao-functional"
TAXONOMY_VERSION = "v1"
DEFAULT_TAXONOMY_ID = f"{TAXONOMY_NAME}-{TAXONOMY_VERSION}"

_SEED_SYNONYMS: list[tuple[str, str]] = [
    ("cocoa", "cocoa"),
    ("cacao", "cocoa"),
    ("cocoa powder", "cocoa"),
    ("high-flavanol cocoa", "cocoa"),
    ("arandano", "blueberry"),
    ("arándano", "blueberry"),
    ("blueberry", "blueberry"),
    ("blueberries", "blueberry"),
    ("quinoa", "quinoa"),
    ("quinua", "quinoa"),
    ("mango", "mango"),
    ("mangos", "mango"),
    ("mangoes", "mango"),
    ("palta", "avocado"),
    ("palta hass", "avocado"),
    ("avocado", "avocado"),
    ("aguacate", "avocado"),
    ("cafe", "coffee"),
    ("café", "coffee"),
    ("coffee", "coffee"),
    ("cafe tostado", "coffee"),
    ("uva", "grape"),
    ("uvas", "grape"),
    ("grape", "grape"),
    ("grapes", "grape"),
    ("pisco", "pisco"),
    ("aceite de oliva", "olive_oil"),
    ("olive oil", "olive_oil"),
    ("olive_oil", "olive_oil"),
    ("esparrago", "asparagus"),
    ("espárrago", "asparagus"),
    ("asparagus", "asparagus"),
    ("maca", "maca"),
    ("mandarina", "mandarin"),
    ("mandarinas", "mandarin"),
    ("mandarin", "mandarin"),
    ("mandarins", "mandarin"),
    ("tangerine", "mandarin"),
    ("kiwicha", "amaranth"),
    ("amaranto", "amaranth"),
    ("amaranth", "amaranth"),
    ("chia", "chia"),
    ("chía", "chia"),
    ("chia seeds", "chia"),
    ("camu camu", "camu_camu"),
    ("camu-camu", "camu_camu"),
    ("camucamu", "camu_camu"),
    ("alcachofa", "artichoke"),
    ("alcachofas", "artichoke"),
    ("alcaucil", "artichoke"),
    ("artichoke", "artichoke"),
    ("aji", "chili_pepper"),
    ("ají", "chili_pepper"),
    ("aji panca", "chili_pepper"),
    ("ají panca", "chili_pepper"),
    ("chili pepper", "chili_pepper"),
    ("dried chili", "chili_pepper"),
]

_SEED_HS_MAPPINGS: list[tuple[str, str, str]] = [
    ("cocoa", "180610", "Cocoa powder and preparations"),
    ("blueberry", "081040", "Fresh or frozen blueberries"),
    ("quinoa", "100850", "Quinoa"),
    ("mango", "080450", "Fresh or dried mangoes"),
    ("avocado", "080440", "Fresh or dried avocados"),
    ("coffee", "090121", "Roasted coffee, not decaffeinated"),
    ("grape", "080610", "Fresh grapes"),
    ("pisco", "220820", "Spirits from grape wine or marc"),
    ("olive_oil", "150910", "Virgin olive oil"),
    ("asparagus", "070920", "Fresh asparagus"),
    ("maca", "121190", "Plants and parts for pharmacy or perfumery"),
    ("mandarin", "080520", "Fresh or dried mandarins, clementines, and tangerines"),
    ("amaranth", "100890", "Kiwicha (amaranth grain), other cereals n.e.s."),
    ("chia", "120799", "Chia seeds, other oil seeds n.e.s."),
    ("camu_camu", "081190", "Camu camu pulp, frozen"),
    ("artichoke", "070991", "Fresh or chilled globe artichokes"),
    ("chili_pepper", "090421", "Dried chili peppers (ají panca), neither crushed nor ground"),
]


def _normalize(query: str) -> str:
    return " ".join(query.casefold().split())


def parse_taxonomy_version(taxonomy_version: str) -> tuple[str, str]:
    if taxonomy_version == DEFAULT_TAXONOMY_ID:
        return TAXONOMY_NAME, TAXONOMY_VERSION
    if "-" in taxonomy_version:
        name, version = taxonomy_version.rsplit("-", 1)
        return name, version
    return taxonomy_version, TAXONOMY_VERSION


def ensure_default_taxonomy(store: ResearchStore) -> str:
    existing = store.get_taxonomy(TAXONOMY_NAME, TAXONOMY_VERSION)
    if existing:
        return existing["id"]
    taxonomy = store.create_taxonomy(name=TAXONOMY_NAME, version=TAXONOMY_VERSION)
    taxonomy_id = taxonomy["id"]
    for term, normalized in _SEED_SYNONYMS:
        store.add_synonym(taxonomy_id=taxonomy_id, term=term, normalized=normalized)
    for product_term, hs_code, description in _SEED_HS_MAPPINGS:
        store.add_hs_mapping(
            taxonomy_id=taxonomy_id,
            product_term=product_term,
            hs_code=hs_code,
            description=description,
        )
    return taxonomy_id


def resolve_hs_code(store: ResearchStore, *, taxonomy_version: str, query_normalized: str) -> str | None:
    name, version = parse_taxonomy_version(taxonomy_version)
    taxonomy = store.get_taxonomy(name, version)
    if taxonomy is None:
        taxonomy_id = ensure_default_taxonomy(store)
    else:
        taxonomy_id = taxonomy["id"]
    normalized_query = _normalize(query_normalized)
    for mapping in store.get_hs_mappings(taxonomy_id):
        term = _normalize(mapping["product_term"])
        if term in normalized_query or normalized_query in term:
            return mapping["hs_code"]
    canonical_terms: set[str] = set()
    for synonym in store.get_synonyms(taxonomy_id):
        if synonym["term"] in normalized_query or synonym["normalized"] in normalized_query:
            canonical_terms.add(synonym["normalized"])
    for mapping in store.get_hs_mappings(taxonomy_id):
        if _normalize(mapping["product_term"]) in canonical_terms:
            return mapping["hs_code"]
    return None


def expand_query_with_synonyms(store: ResearchStore, *, taxonomy_version: str, query_normalized: str) -> str:
    name, version = parse_taxonomy_version(taxonomy_version)
    taxonomy = store.get_taxonomy(name, version)
    if taxonomy is None:
        ensure_default_taxonomy(store)
        taxonomy = store.get_taxonomy(name, version)
    if taxonomy is None:
        return query_normalized
    extras: list[str] = []
    for synonym in store.get_synonyms(taxonomy["id"]):
        if synonym["normalized"] in query_normalized or synonym["term"] in query_normalized:
            extras.append(synonym["term"])
    if not extras:
        return query_normalized
    return _normalize(f"{query_normalized} {' '.join(extras)}")
