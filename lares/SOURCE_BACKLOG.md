# Lares — Source Backlog (country × sector)

Per spec §48/§49. This is the backlog of source *candidates* to research and
turn into adapters — distinct from `SOURCES.md`, which documents adapters
that are actually implemented (TED, GLEIF, Overpass, ENTSO-E-pending-token).

Status legend: `implemented` (see SOURCES.md) · `candidate` (known category
of source exists, specific URL/licence not yet researched and reviewed) ·
`unresearched` (not yet looked at).

A "Country Expansion Agent" (spec §49) — tooling that researches a new
country's national open-data portal, transport ministry, energy regulator,
TSO, gas TSO, port register, airport authority, procurement portal, company
registry, water regulator, digital-infrastructure authority, and GIS portal
— is not yet built. This table is what it would populate; for now it's
filled in by category, not yet by verified URL, to avoid asserting
unreviewed licence terms as fact (see DATA_GOVERNANCE.md's licence gate).

## Pan-European (cross-country)

| Source | Categories | Status |
|---|---|---|
| TED (Tenders Electronic Daily) | Procurement, all countries | implemented |
| GLEIF | Corporate ownership, all countries | implemented |
| OpenStreetMap / Geofabrik | Geospatial origination, all categories | implemented (Overpass discovery only; Geofabrik bulk extract adapter is `candidate`) |
| ENTSO-E Transparency Platform | Electricity transmission | candidate — adapter written, disabled pending `ENTSOE_API_TOKEN` |
| European Commission TEN-T / TENtec | Ports, airports, rail freight, corridors | candidate |
| European Commission TEN-E / PCI-PMI transparency | Energy projects | candidate |
| ENTSO-G / GIE | Gas transmission, LNG, storage | candidate — licence for the intended commercial reuse needs checking first |
| CEF Digital / EU digital-connectivity programmes | Digital infrastructure, submarine cables | candidate |
| OpenCorporates | Corporate registry cross-reference | candidate — commercial licence terms need checking before bulk use |

## Italy (QA market — partially covered by seed data)

| Sector | Candidate source | Status |
|---|---|---|
| Energy (TSO) | terna.it (operator disclosures) | candidate; QA seed has Terna as an organisation, no live adapter |
| Maritime | assoporti.it (national port authority association), individual AdSP sites (e.g. portsofgenoa.com) | candidate; QA seed has Genoa |
| Rail | rfi.it | candidate; QA seed has RFI as an organisation |
| Procurement | ANAC (Autorità Nazionale Anticorruzione) national portal, in addition to TED | unresearched |
| Corporate registry | Registro Imprese (InfoCamere) | unresearched |
| Open data / GIS | dati.gov.it | unresearched |

## Netherlands

| Sector | Candidate source | Status |
|---|---|---|
| Maritime | portofrotterdam.com | candidate; QA seed has Rotterdam |
| Aviation | schiphol.nl | candidate; QA seed has Schiphol |
| Digital | ams-ix.net | candidate; QA seed has AMS-IX |
| Energy (TSO) | tennet.eu | unresearched |
| Corporate registry | KVK (Kamer van Koophandel) open data | unresearched |
| Open data | data.overheid.nl | unresearched |

## Germany

| Sector | Candidate source | Status |
|---|---|---|
| Energy (TSOs) | 50hertz.com, amprion.net, tennet.eu, transnetbw.de | candidate; QA seed has 50Hertz |
| Aviation | fraport.com, and other Land-level airport operators | candidate; QA seed has Fraport |
| Digital | de-cix.net (Frankfurt IXP), individual data-centre operator disclosures | unresearched |
| Procurement | national e-Vergabe portal, in addition to TED | unresearched |
| Corporate registry | Bundesanzeiger / Handelsregister | unresearched |

## France

| Sector | Candidate source | Status |
|---|---|---|
| Energy (TSO) | rte-france.com | candidate; QA seed has RTE |
| Maritime | Grands Ports Maritimes sites (e.g. Marseille-Fos, Le Havre) | unresearched |
| Rail | sncf-reseau.com | unresearched |
| Procurement | BOAMP (Bulletin officiel des annonces de marchés publics), in addition to TED | unresearched |
| Corporate registry | INPI / data.inpi.fr | unresearched |

## Greece

| Sector | Candidate source | Status |
|---|---|---|
| Maritime | olp.gr (Piraeus) and other regional port authorities | candidate; QA seed has Piraeus |
| Energy (TSO) | admie.gr (IPTO) | unresearched |

## Not yet researched at all (priority order for next pass)

Spain, Poland, Belgium, Sweden, Norway, Switzerland, Portugal, Austria,
Denmark, Finland, Ireland, remaining EU-27 members, UK, Iceland — then
Western Balkans, Ukraine, Moldova, Turkey per spec §5's expansion order.
For each: national open-data portal, transport ministry, energy regulator,
TSO, gas TSO, port register, airport authority, national procurement
portal (beyond TED), corporate registry, water regulator,
digital-infrastructure authority, infrastructure GIS portal — per the
Country Expansion Agent checklist (spec §49).
