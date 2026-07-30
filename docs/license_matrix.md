# License Matrix

| Source | License | Commercial Use | Attribution | Notes |
|---|---|---|---|---|
| OpenAlex | OpenAlex data snapshot | Allowed | Required | Attribution required |
| Crossref | Crossref REST API metadata | Allowed | Required | Etiquette rate limits |
| PubMed / NCBI E-utilities | Public domain | Allowed | Not required | No copyright |
| Semantic Scholar | Open Data | Allowed | Required | Attribution required |
| EPO OPS | Free tier with registration | Allowed | Required | Rate limits apply |
| GDELT | Open for non-commercial use | Restricted | Required | Check terms for commercial |
| UN Comtrade | Open data | Allowed | Required | Attribution required |
| **WTO ePing / Timeseries** | WTO open data | Allowed | Required | Free API key at apiportal.wto.org |
| **WITS / UNCTAD TRAINS** | World Bank / UNCTAD open data | Allowed | Required | No API key |
| **FAOSTAT** | CC BY-NC-SA 3.0 IGO | **Restricted (NC)** | Required | Confirm commercial use for CLI Market |
| **USDA FAS** | US public domain | Allowed | Optional | Free API key |
| **RASFF Window** | CC BY 4.0 | Allowed | Required | Attribute "European Commission – RASFF" |
| **Eurostat Comext** | Eurostat open data | Allowed | Required | Attribute "Eurostat" |
| **USPTO ODP** | US public domain | Allowed | Optional | Free API key (USPTO.gov account) |
| **World Bank Indicators** | CC BY 4.0 | Allowed | Required | No API key |
| **Google Trends (alpha)** | Google API terms | TBD | TBD | Alpha — terms under evaluation |
| **ClinicalTrials.gov** | NIH public domain | Allowed | Optional | No API key |
| **arXiv** | Metadata CC0; papers vary | Allowed (metadata) | Optional | Do not redistribute full PDFs |
| **IMF Data** | IMF open data | Allowed | Required | No API key |
| **OECD SDMX** | OECD terms of use | Allowed | Required | Free API key registration |
| **Codex Alimentarius** | FAO/WHO open texts | Allowed | Required | No API; local index |
| **CFIA Canada** | Open Government Licence – Canada | Allowed | Required | Bulk/scrape; no REST API |
| **RappelConso** | Licence Ouverte (France) | Allowed | Required | OpenData France API |

## Action Items
- [ ] Confirm GDELT commercial use terms
- [ ] Confirm FAOSTAT CC BY-NC-SA compatibility with CLI Market commercial product
- [ ] Confirm Google Trends alpha commercial terms when available
- [ ] Add license headers to generated reports
- [ ] Store license per `source_request` in DB

## Planned connectors

See `docs/connectors/README.md` for full technical specifications.
