import requests
import pandas as pd
from typing import List, Dict, Optional


class TwseOpenApi:
    def __init__(
        self,
        base_url: str = "https://openapi.twse.com.tw/v1/",
        return_raw: bool = False,
    ) -> None:
        """
        Initialize the TwseOpenApi object with a base_url.

        Parameters
        ----------
        base_url : str, optional
            The base URL for the TWSE OpenAPI (default is "https://openapi.twse.com.tw/v1/").
        """
        self.base_url: str = base_url
        self.return_raw: bool = return_raw

    @staticmethod
    def parse_taiwanese_date(taiwan_date: str) -> Optional[pd.Timestamp]:
        """
        Parse a Taiwanese year date string (e.g., '1131227') into a Gregorian date.

        Parameters
        ----------
        taiwan_date : str
            A string representing a date in Taiwanese year format (e.g., '1131227').

        Returns
        -------
        Optional[pd.Timestamp]
            The parsed Gregorian date as a Pandas Timestamp, or None if parsing fails.
        """
        if not isinstance(taiwan_date, str) or len(taiwan_date) != 7:
            return None
        try:
            # Split the Taiwanese year and the MMDD part
            taiwan_year = int(taiwan_date[:3]) + 1911  # Convert to Gregorian year
            month_day = taiwan_date[3:]
            # Combine into a full Gregorian date string (e.g., '20241227')
            gregorian_date = f"{taiwan_year}{month_day}"
            return pd.to_datetime(gregorian_date, format="%Y%m%d", errors="coerce")
        except Exception:
            return None

    def infer_column_type(
        self, series: pd.Series, is_taiwanese_date: bool = True
    ) -> str:
        """
        Infer the type of a column based on its values.

        Parameters
        ----------
        series : pd.Series
            A pandas Series representing a column.

        Returns
        -------
        str
            The inferred type: 'date', 'numeric', or 'categorical'.
        """

        # Replace "--" with None (to handle missing values)
        # *** ValueError: Unable to parse string "--" at position 53
        series = series.replace("--", None)

        if not is_taiwanese_date:
            # Try to infer date
            try:
                pd.to_datetime(series, format="%Y%m%d", errors="raise")
                return "date"
            except ValueError:
                pass
        else:
            # Try to infer Taiwanese date format
            if series.str.match(r"^\d{7}$").all():
                try:
                    series.apply(self.parse_taiwanese_date)
                    return "date"
                except Exception:
                    pass

        # Try to infer numeric
        try:
            pd.to_numeric(series.str.replace(",", ""), errors="raise")
            return "numeric"
        except (ValueError, AttributeError):
            pass

        # Default to categorical
        return "categorical"

    def parse_data(
        self,
        data: List[Dict[str, str]],
        parse_dates: bool = True,
        parse_numbers: bool = True,
        parse_categories: bool = True,
        is_taiwanese_date: bool = True,
        force_column_type: Dict[str, str] = {},
    ) -> pd.DataFrame:
        """
        Parse the raw list-of-dict data into a Pandas DataFrame,
        dynamically inferring column types.

        Parameters
        ----------
        data : List[Dict[str, str]]
            A list of dictionary objects (JSON) from TWSE OpenAPI.
        parse_dates : bool, optional
            If True, attempt to parse date-like columns to datetime.
        parse_numbers : bool, optional
            If True, attempt to parse number-like columns to numeric.
        parse_categories : bool, optional
            If True, attempt to parse other columns to categorical.

        Returns
        -------
        pd.DataFrame
            A DataFrame with parsed columns where applicable.
        """
        df = pd.DataFrame(data)

        if self.return_raw:
            return df

        # Replace "--" with NaN across the entire DataFrame
        df = df.replace("--", pd.NA)

        for col in df.columns:
            col_type = force_column_type.get(col, self.infer_column_type(df[col]))

            if col_type == "date" and parse_dates:
                if is_taiwanese_date:
                    df[col] = df[col].apply(self.parse_taiwanese_date)
                else:
                    df[col] = pd.to_datetime(df[col], format="%Y%m%d", errors="coerce")
            elif col_type == "numeric" and parse_numbers:
                df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")
            elif col_type == "categorical" and parse_categories:
                # https://www.kdnuggets.com/how-to-manage-categorical-data-effectively-with-pandas
                # categorical data is more memory-efficient
                df[col] = df[col].astype("category")
            else:
                # TODO: string, ...
                # https://www.kaggle.com/discussions/general/188478
                df[col] = df[col].astype("string")

        return df

    def get_industry_eps_stat_info(self) -> Optional[pd.DataFrame]:
        """
        取得「上市公司各產業EPS統計資訊」

        This method fetches data from the endpoint: opendata/t187ap14_L

        Returns
        -------
        Optional[pd.DataFrame]
            Returns a Pandas DataFrame if successful, or None if the
            request was not successful.
        """
        endpoint: str = "opendata/t187ap14_L"
        url: str = f"{self.base_url}{endpoint}"
        response = requests.get(url)

        if response.status_code == 200:
            data: List[Dict[str, str]] = response.json()
            df = self.parse_data(
                data,
                force_column_type={
                    "年度": "categorical",
                    "季別": "categorical",
                    "公司代號": "categorical",
                    "公司名稱": "string",
                },
            )
            return df
        else:
            print(f"Error {response.status_code} fetching data from {url}.")
            return None


if __name__ == "__main__":
    twse_api = TwseOpenApi()

    # Fetch and parse the industry EPS statistics data
    df_industry_eps = twse_api.get_industry_eps_stat_info()

    if df_industry_eps is not None:
        print(df_industry_eps.info())
        print(df_industry_eps.head())
    else:
        print("Failed to fetch or parse data from the TWSE OpenAPI.")

    import ipdb

    ipdb.set_trace()
