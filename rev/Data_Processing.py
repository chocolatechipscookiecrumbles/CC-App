from . import *
from .config import REVENUE_COMBINATIONS
from programlauncher.common.sports import (
    MENS_ONLY_SPORTS,
    WOMENS_ONLY_SPORTS,
    normalize_sport_name,
)

def extract_unique_sports_from_rows(data_dict, column_name="category", use_index=False, exclude_words=None):
    """
    Extracts a list of unique sports from multiple DataFrames, either from a column or index,
    excluding rows containing certain words.

    Parameters:
        data_dict (dict): Dictionary where values are pandas DataFrames.
        column_name (str): The column that contains sport names (ignored if use_index=True).
        use_index (bool): If True, extract sports from the DataFrame index instead of a column.
        exclude_words (list): Words to exclude if they appear in the sport name.

    Returns:
        list: Sorted list of unique sports found across all DataFrame rows.
    """
    unique_sports = set()
    exclude_words = exclude_words or ["expenses", "team", "total", "other"]

    for key, df in data_dict.items():
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue

        # Choose the source of sport names
        if use_index:
            sports = pd.Series(df.index, dtype=str)
        elif column_name in df.columns:
            sports = df[column_name].dropna().astype(str)
        else:
            continue

        # Filter out excluded words
        exclude_pattern = "|".join(re.escape(word) for word in exclude_words)
        mask = ~sports.str.contains(exclude_pattern, case=False, regex=True, na=False)
        filtered_sports = sports[mask]

        for sport in filtered_sports:
            normalized_sport = normalize_sport_name(sport)
            unique_sports.add(normalized_sport)

    return sorted(unique_sports)

def combine_financial_columns(df):
    """
    Combine specific numeric columns in the athletics finance dataframe.

    Specifically:
        - Columns 2 and 4 are combined into '2'
        - Columns 12 and 13 are combined into '12'
        - Columns 13A and 19 are combined into '19'

    Non-mentioned columns remain unchanged.

    Returns:
        pd.DataFrame: A new DataFrame with combined columns.
    """

    df = df.copy()  # Avoid modifying the original

    for target, sources in REVENUE_COMBINATIONS.items():
        # Only sum columns that actually exist in df
        existing = [col for col in sources if col in df.columns]
        if not existing:
            continue

        df[target] = df[existing].sum(axis=1, skipna=True)

        # Drop the redundant ones, except the target itself
        to_drop = [col for col in existing if col != target]
        df.drop(columns=to_drop, inplace=True, errors='ignore')

    return df

def generate_ws_names(sports_list):
    expanded_list = []
    mens_only = MENS_ONLY_SPORTS
    womens_only = WOMENS_ONLY_SPORTS
    #coed = ["rifle"]

    for sport in sports_list:
        # Normalize sport name for comparison
        sport_clean = normalize_sport_name(sport)

        if sport_clean not in mens_only and sport_clean not in womens_only:
            expanded_list.append(f"Men's {sport_clean}")
            expanded_list.append(f"Women's {sport_clean}")
        else:
            expanded_list.append(sport)

    return expanded_list

def build_gender_sport_summaries(df_dict, client_uni=None, mens_only=None, womens_only=None):
    """
    Builds male/female sport summary DataFrames, but only includes sports where
    the given client university actually has at least one nonzero value.
    """
    if not df_dict:
        return pd.DataFrame(), pd.DataFrame()
    if mens_only is None:
        mens_only = MENS_ONLY_SPORTS
    if womens_only is None:
        womens_only = WOMENS_ONLY_SPORTS

    # collect all universities that appear in any of the sport dataframes
    all_universities = sorted({uni for df in df_dict.values() for uni in df.index})

    men_summary = pd.DataFrame(index=all_universities)
    women_summary = pd.DataFrame(index=all_universities)

    def clean_name(sport_key):
        return sport_key.replace("Men's ", "").replace("Women's ", "").strip()

    for sport_key, df in df_dict.items():
        # Normalize dataframe: ensure numeric values for summation
        df_numeric = df.apply(pd.to_numeric, errors='coerce').fillna(0)

        # Skip this sport entirely if client_uni is specified but has no data
        if client_uni is not None:
            if client_uni not in df_numeric.index:
                continue  # client not in sport
            # check if client has any nonzero data for this sport
            if df_numeric.loc[client_uni].sum() == 0:
                continue  # no values → skip

        # sum across columns (per-university totals for this sport)
        sport_sum = df_numeric.sum(axis=1)

        sport_name_clean = clean_name(sport_key)

        # Determine sport gender
        if sport_key.startswith("Men's "):
            gender = 'men'
        elif sport_key.startswith("Women's "):
            gender = 'women'
        elif sport_name_clean in mens_only and sport_name_clean not in womens_only:
            gender = 'men'
        elif sport_name_clean in womens_only and sport_name_clean not in mens_only:
            gender = 'women'
        else:
            gender = 'coed'

        # Assign to appropriate summary DataFrames
        if gender == 'men':
            men_summary[sport_name_clean] = sport_sum
        elif gender == 'women':
            women_summary[sport_name_clean] = sport_sum
        else:
            men_summary[sport_name_clean] = sport_sum
            women_summary[sport_name_clean] = sport_sum

    # Ensure missing combos are 0
    men_summary = men_summary.fillna(0).sort_index(axis=1)
    women_summary = women_summary.fillna(0).sort_index(axis=1)

    return men_summary, women_summary


def fix_misattributions_coeffs(df: pd.DataFrame,
                               left_col: str = 'men',
                               right_col: str = 'women',
                               total_row_index: int = -1,
                               verbose: bool = False) -> pd.DataFrame:
    """
    Fix misattributed values by solving for coefficients on rows where left_col>0 and right_col==0.
    Strategy (in order):
      1) exact subset-sum (move whole rows)
    Returns a corrected copy of df (leaves original df untouched).
    """
    df = df.copy(deep=True)
    if len(df) == 0:
        if verbose:
            print("Empty dataframe - nothing to fix.")
        return df

    if abs(total_row_index) > len(df):
        if verbose:
            print(f"Warning: total_row_index={total_row_index} out of bounds for df with {len(df)} rows. Skipping.")
        return df

    # Identify totals (assume last row or given index)
    total_row = df.iloc[total_row_index]
    total_left = float(total_row[left_col])
    total_right = float(total_row[right_col])

    # sums excluding the total row
    body = df.drop(df.index[total_row_index])
    sum_left = float(body[left_col].sum())
    sum_right = float(body[right_col].sum())

    over = sum_left - total_left                # how much left has too much
    under = total_right - sum_right             # how much right is missing

    if verbose:
        print(f"sum({left_col})={sum_left} reported_total={total_left} -> over={over}")
        print(f"sum({right_col})={sum_right} reported_total={total_right} -> under={under}")

    # sanity checks
    if over <= 0 or abs(over - under) > 1e-6:
        if verbose:
            print("No balanced misattribution detected (nothing to fix or unbalanced).")
        return df

    # candidate rows where left>0 and right==0
    cand = body[(body[left_col] > 0) & (body[right_col] == 0)].copy()
    if cand.empty:
        if verbose: print("No candidate rows found (no rows with left>0 and right==0).")
        return df

    # numeric handling: if values are essentially integers, use integer DP for subset-sum.
    def is_integer_like(x):
        return abs(x - round(x)) < 1e-6

    target = over
    integer_mode = is_integer_like(target) and all(is_integer_like(v) for v in cand[left_col].tolist())

    # Try exact subset-sum (binary coefficients)
    if integer_mode:
        target_int = int(round(target))
        vals = [int(round(v)) for v in cand[left_col].tolist()]
        idxs = cand.index.tolist()
        cap = sum(vals)
        if cap >= target_int:
            # DP to find one subset that sums exactly to target
            dp = [False] * (target_int + 1)
            prev = [None] * (target_int + 1)   # store (prev_sum, item_index)
            dp[0] = True
            for i, v in enumerate(vals):
                # iterate backwards
                for s in range(target_int, v - 1, -1):
                    if dp[s - v] and not dp[s]:
                        dp[s] = True
                        prev[s] = (s - v, i)
            if dp[target_int]:
                # reconstruct chosen items
                chosen_item_indices: List[int] = []
                s = target_int
                while s > 0:
                    s_prev, i = prev[s]
                    chosen_item_indices.append(i)
                    s = s_prev
                chosen_df_indices = [idxs[i] for i in chosen_item_indices]

                # Move full rows for chosen indices
                for ridx in chosen_df_indices:
                    v = int(round(df.at[ridx, left_col]))
                    df.at[ridx, left_col] = 0
                    df.at[ridx, right_col] = df.at[ridx, right_col] + v

                if verbose:
                    cats = [(df.at[i, 'category'], int(round(df.at[i, right_col]))) for i in chosen_df_indices]
                    print(f"Exact subset found. Moved full rows: {cats}")
                return df
        # if cap < target_int or no subset found, fall through to the unchanged result

    return df
