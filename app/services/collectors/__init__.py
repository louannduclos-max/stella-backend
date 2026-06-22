from app.services.collectors.base import BaseCollector
from app.services.collectors.demography import DemographyCollector
from app.services.collectors.target_segments import TargetSegmentsCollector
from app.services.collectors.employment import EmploymentCollector
from app.services.collectors.income_housing import IncomeHousingCollector
from app.services.collectors.competition import CompetitionCollector
from app.services.collectors.regulation import RegulationCollector
from app.services.collectors.business_case import BusinessCaseCollector
from app.services.collectors.real_estate import RealEstateCollector, MicroZonesCollector
from app.services.collectors.tourism import TourismCollector
from app.services.collectors.pricing import PricingCollector
from app.services.collectors.mobility import MobilityCollector


ACTIVE_COLLECTORS: list[BaseCollector] = [
    DemographyCollector(),
    IncomeHousingCollector(),
    RealEstateCollector(),
    MicroZonesCollector(),
    TargetSegmentsCollector(),
    EmploymentCollector(),
    CompetitionCollector(),
    PricingCollector(),
    MobilityCollector(),
    TourismCollector(),
    RegulationCollector(),
    BusinessCaseCollector(),
]
