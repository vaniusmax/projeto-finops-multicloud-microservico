from __future__ import annotations

from finops_api.repositories.dims_repo import DimsRepository
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.schemas.filters import AvailableRange, CloudScopes, FilterOption, FiltersResponse


class FiltersService:
    def __init__(self, dims_repo: DimsRepository, fact_repo: FactCostRepository) -> None:
        self.dims_repo = dims_repo
        self.fact_repo = fact_repo

    def get_filters(self, cloud: str) -> FiltersResponse:
        scopes_by_cloud = self.dims_repo.list_scopes_by_cloud()
        min_date, max_date = self.fact_repo.available_range(cloud)
        services = self.dims_repo.top_services(None if cloud == "all" else cloud, limit=10)
        regions = self.dims_repo.top_regions(None if cloud == "all" else cloud, limit=10)

        cloud_scopes = [
            CloudScopes(
                cloud=cloud_key,
                scopes=[FilterOption(key=item.key, name=item.name) for item in items],
            )
            for cloud_key, items in scopes_by_cloud.items()
            if cloud == "all" or cloud_key == cloud
        ]

        return FiltersResponse(
            clouds=["all", "aws", "azure", "oci"],
            scopes_by_cloud=cloud_scopes,
            services_top=[FilterOption(key=item.key, name=item.name) for item in services],
            regions_top=[FilterOption(key=item.key, name=item.name) for item in regions],
            available_range=AvailableRange(min_date=min_date, max_date=max_date),
        )
