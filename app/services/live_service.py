import pandas as pd

from .data_loader import static_data
from .tfwm_client import tfwm_client


class ProductionLiveService:

    def refresh(self):
        return tfwm_client.refresh_all()

    def vehicles(self):
        return tfwm_client.vehicle_positions.copy()

    def trip_updates(self):
        return tfwm_client.trip_updates.copy()

    def find_route(self, route_code):
        df = self.vehicles()

        if df.empty:
            return df

        route_code = str(route_code).strip().upper()

        route_col = None

        for col in ["route_id", "route_code"]:
            if col in df.columns:
                route_col = col
                break

        if route_col is None:
            return pd.DataFrame()

        mask = (
            df[route_col]
            .astype(str)
            .str.upper()
            .eq(route_code)
        )

        return df.loc[mask].copy()

    def find_vehicle_by_trip(self, trip_id):
        df = self.vehicles()

        if df.empty or "trip_id" not in df.columns:
            return pd.DataFrame()

        return df[
            df["trip_id"].astype(str).eq(str(trip_id))
        ].copy()


live_service = ProductionLiveService()
