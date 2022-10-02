from __future__ import annotations
import typing


import pandas as pd
import requests
from requests.models import Response


API_BASE_URL: str = "https://www.nbrb.by/api/exrates"


class ParameterString:
    """Create a parameter string from passed kwargs."""

    def __init__(self, **kwargs) -> None:
        parameters: list[str] = [
            f"{param_name}={param_value}" for param_name, param_value in kwargs.items()
        ]
        self._param_string: str = "&".join(parameters)

    def __repr__(self) -> str:
        return self._param_string if self._param_string else "<ParameterString>"

    def add_parameters(self, **kwargs) -> str:
        new_params: list[str] = [
            f"{param_name}={param_value}" for param_name, param_value in kwargs.items()
        ]
        if self._param_string:
            self._param_string = f'{self._param_string}&{"&".join(new_params)}'
        else:
            self._param_string = "&".join(new_params)

        return self._param_string


class NBRBAPI:

    BASE_URL: str = API_BASE_URL

    # NOTE: does not contain data on BYN
    CURRENCY_MAP: dict[str, int] = {
        cur_dict["Cur_Abbreviation"]: cur_dict["Cur_ID"]
        for cur_dict in requests.get(f"{BASE_URL}/currencies").json()
    }

    def __init__(self) -> None:
        pass

    @classmethod
    def get(cls, slug: str) -> list[dict[str, str | int]] | dict[str, str | int]:
        """Make an arbitrary GET request."""

        return requests.get(f"{cls.BASE_URL}/{slug}").json()

    @classmethod
    def get_currency_list(cls) -> list[dict[str, str | int]]:
        """Get a list of all currencies."""
        return requests.get(f"{cls.BASE_URL}/currencies").json()

    @classmethod
    def get_currency_info(cls, currency: str = "USD") -> dict[str, str | int]:
        """Get info about a specific currency. Defaults to USD."""
        if currency not in cls.CURRENCY_MAP:
            raise ValueError(f"No data for {currency!r} is available.")

        return requests.get(
            f"{cls.BASE_URL}/currencies/{cls.CURRENCY_MAP[currency]}"
        ).json()

    @classmethod
    def get_byn_rate(
        cls,
        date: str | None = None,
        currency: str | None = None,
        monthly: bool = False,
    ) -> list[dict[str, str | int | float]] | dict[str, str | int | float]:
        """Get BYN exchange rate for specified day or currency.
        Date defaults to today.
        """

        params: ParameterString = ParameterString()
        url: str = f"{cls.BASE_URL}/rates"

        if currency and currency not in cls.CURRENCY_MAP:
            raise ValueError(f"No data for {currency!r} is available.")

        if currency:
            url += f"/{currency}"
            params.add_parameters(parammode=2)

        if date:
            params.add_parameters(date=date.replace("-0", "-"))

        params.add_parameters(periodicity=1 if monthly else 0)

        return requests.get(f"{url}?{params}").json()

    @classmethod
    def get_byn_rate_for_period(
        cls,
        currency: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, float]:
        """Get BYN exchange rate in relation to specified currency for a given period."""

        dates: pd.DatetimeIndex = pd.date_range(start_date, end_date)

        rates: dict[str, float] = {}

        for date in dates:
            date = date.to_pydatetime().date().isoformat()

            rate: float = NBRBAPI.get_byn_rate(currency=currency, date=date)[
                "Cur_OfficialRate"
            ]
            scale: int = NBRBAPI.get_byn_rate(currency=currency, date=date)["Cur_Scale"]
            rates[date] = rate / scale

        return rates
