import enum


class SensitivityLevel(str, enum.Enum):
    STANDARD = "STANDARD"
    ELEVATED = "ELEVATED"
    RESTRICTED_PUBLIC = "RESTRICTED_PUBLIC"


class GeometryPrecision(str, enum.Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    ADMINISTRATIVE_CENTROID = "administrative_centroid"
    WITHHELD = "withheld"


class AssetStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    UNDER_CONSTRUCTION = "under_construction"
    PLANNED = "planned"
    DECOMMISSIONED = "decommissioned"
    UNKNOWN = "unknown"


class SalesReadinessState(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    NEEDS_ENRICHMENT = "NEEDS_ENRICHMENT"
    IDENTIFIED = "IDENTIFIED"
    QUALIFIED = "QUALIFIED"
    OUTREACH_READY = "OUTREACH_READY"
    WATCH = "WATCH"
    DISQUALIFIED = "DISQUALIFIED"


class VerificationState(str, enum.Enum):
    UNVERIFIED = "unverified"
    CORROBORATED = "corroborated"
    VERIFIED = "verified"
    DISPUTED = "disputed"


class OrganisationType(str, enum.Enum):
    OPERATOR = "operator"
    OWNER = "owner"
    PARENT = "parent"
    PUBLIC_AUTHORITY = "public_authority"
    SECURITY_PROVIDER = "security_provider"
    TECHNOLOGY_PROVIDER = "technology_provider"
    SUPPLIER = "supplier"
    OTHER = "other"


class OwnershipClass(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    STATE_OWNED = "state_owned"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class RelationshipPredicate(str, enum.Enum):
    OWNS = "OWNS"
    OPERATES = "OPERATES"
    CONTROLS = "CONTROLS"
    ULTIMATELY_OWNED_BY = "ULTIMATELY_OWNED_BY"
    PART_OF = "PART_OF"
    LOCATED_AT = "LOCATED_AT"
    LOCATED_IN = "LOCATED_IN"
    CONNECTS_TO = "CONNECTS_TO"
    REGULATED_BY = "REGULATED_BY"
    AUTHORISED_BY = "AUTHORISED_BY"
    MANAGED_BY = "MANAGED_BY"
    PROCURES_FROM = "PROCURES_FROM"
    CONTRACTED_WITH = "CONTRACTED_WITH"
    ANNOUNCED_PROJECT = "ANNOUNCED_PROJECT"
    INVESTING_IN = "INVESTING_IN"
    HAS_ROLE = "HAS_ROLE"
    WORKS_AT = "WORKS_AT"
    MENTIONED_IN = "MENTIONED_IN"
    AFFECTED_BY_EVENT = "AFFECTED_BY_EVENT"
    PARTICIPATES_IN_PROJECT = "PARTICIPATES_IN_PROJECT"
    ISSUED_TENDER = "ISSUED_TENDER"
    WON_TENDER = "WON_TENDER"
    RELATED_TO = "RELATED_TO"
    SOURCE_SUPPORTS_CLAIM = "SOURCE_SUPPORTS_CLAIM"


class SourceTier(int, enum.Enum):
    TIER_1_AUTHORITATIVE = 1
    TIER_2_STRUCTURED = 2
    TIER_3_OPEN_GEOSPATIAL = 3
    TIER_4_OPEN_WEB = 4
    TIER_5_DISCOVERY_ONLY = 5


class LicenceStatus(str, enum.Enum):
    DISCOVERY_ONLY = "discovery_only"
    ATTRIBUTION_REQUIRED = "attribution_required"
    CLEARED = "cleared"
    RESTRICTED = "restricted"


class SignalType(str, enum.Enum):
    EXPANSION = "expansion"
    NEW_FACILITY = "new_facility"
    ACQUISITION = "acquisition"
    LEADERSHIP_CHANGE = "leadership_change"
    SECURITY_LEADERSHIP_CHANGE = "security_leadership_change"
    PUBLIC_TENDER = "public_tender"
    CONTRACT_EXPIRY = "contract_expiry"
    AUTOMATION_PROGRAMME = "automation_programme"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    DRONE_PROGRAMME = "drone_programme"
    AUTONOMOUS_INSPECTION = "autonomous_inspection"
    RESILIENCE_INVESTMENT = "resilience_investment"
    EU_FUNDING = "eu_funding"
    CAPEX_ANNOUNCEMENT = "capex_announcement"
    REGULATORY_OBLIGATION = "regulatory_obligation"
    SECURITY_INCIDENT = "security_incident"
    OPERATIONAL_DISRUPTION = "operational_disruption"
    CAPACITY_EXPANSION = "capacity_expansion"
    VENDOR_REPLACEMENT = "vendor_replacement"
    SECURITY_HIRING = "security_hiring"
    NEW_CONTROL_CENTRE = "new_control_centre"
    NEW_SENSOR_DEPLOYMENT = "new_sensor_deployment"
    RESILIENCE_EXERCISE = "resilience_exercise"
    OTHER = "other"
