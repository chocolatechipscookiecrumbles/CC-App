from . import *

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

def normalize_sport_name(name):
    """
    Normalizes a single sport name:
      - collapses whitespace
      - converts '&' to 'and'
      - strips trailing stray punctuation (hyphens, apostrophes, commas, etc.)
      - removes parenthetical gender markers like "(W)" or "(M)"
      - canonicalizes Track and Field X- variants to 'XCTF'
      - title-cases the remainder
    """
    s = name.strip()
    s = re.sub(r'\s+', ' ', s)           # collapse whitespace
    s = s.replace('&', 'and')            # unify ampersand
    s = re.sub(r'\s*\(.*?\)\s*$', '', s) # drop trailing parentheticals e.g. (W)
    s = re.sub(r"[-'\".,;:]+$", "", s)   # drop trailing punctuation like - ' ,
    s = s.strip()

    # Detect Track & Field X variants (flexible about spaces and comma)
    if re.search(r"track\s*(?:and|&)\s*field\s*,?\s*x", s, flags=re.I):
        return "XC/TF"

    # Add any other normalizations here (e.g., unify soccer gender variants)
    # Example: unify soccer
    if re.search(r'\bsoccer\b', s, flags=re.I):
        return "Soccer"

    if re.search(r'acrobatics\s*(?:and|&)\s*tumbling\s*,?\s*x', s, flags=re.I):
        return "Acrobatics and Tumbling"

    # Fallback: title-case the cleaned string
    return s.title()


def generate_ws_names(sports_list):
    expanded_list = []
    mens_only = ['Football', 'Baseball',"Rifle"]
    womens_only = ["Softball", "Beach Volleyball", "Field Hockey", "Bowling", "Equestrian", "Rugby"]
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
    if mens_only is None:
        mens_only = ['Football', 'Baseball',  'Crew']  # any coed sport goes to men's
    if womens_only is None:
        womens_only = ["Softball", "Beach Volleyball", "Field Hockey", "Bowling", "Equestrian", "Rugby",'Rifle']

    if not df_dict:
        return pd.DataFrame(), pd.DataFrame()

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
        #handle if its rifle causing misattribution
        rifle_mask = body['category'].str.lower().str.contains('Rifle', na=False, regex=False)
        rifle_rows = body[rifle_mask]
        if not rifle_rows.empty:
            for rifle_idx in rifle_rows.index:
                rifle_left = float(body.at[rifle_idx, left_col])
                rifle_right = float(body.at[rifle_idx, right_col])

                if verbose:
                    print(f"Rifle row: {left_col}={rifle_left}, {right_col}={rifle_right}")

                # Adjust totals by removing rifle values
                '''adjusted_total_left = total_left - rifle_left
                adjusted_total_right = total_right - rifle_right'''

                '''# Recalculate sums excluding rifle row
                #body_no_rifle = body.drop(rifle_idx)
                adjusted_sum_left = float(body_no_rifle[left_col].sum())
                adjusted_sum_right = float(body_no_rifle[right_col].sum())'''

                adjusted_over = sum_left - total_left -rifle_left
                adjusted_under = total_right - rifle_right - sum_right


                # Check if adjustment makes it balanced
                if adjusted_over > 0 and abs(adjusted_over - adjusted_under) < 1e-6:
                    if verbose:
                        print("Rifle adjustment creates balanced misattribution. Proceeding with adjusted values.")

                    # Update variables for the rest of the function
                    #body = body_no_rifle

                    over = adjusted_over
                    under = adjusted_under
                    break
                else:
                    if verbose:
                        print('No balanced misattribution detected after rifle adjustments.')
                    return df
        if over <= 0:
            if verbose:
                print("Negative or zero value.")
            return df
        '''if rifle_rows.empty and verbose:
            print(f"Balanced misattribution detected (over={over}). No possible match.")

        if verbose and over <= 0:
            print("No balanced misattribution detected (nothing to fix or unbalanced).")'''
    # first checks if all rows move can fix it
    all_unallocated = body[(body[left_col] != 0) & (body[right_col] == 0)].copy()

    if not all_unallocated.empty:
        total_unallocated = all_unallocated[left_col].sum()

        if abs(total_unallocated - over) < 1e-6:
            if verbose:
                print(f"All {len(all_unallocated)} unallocated rows (including negatives) sum exactly to target.")
                cats = [(df.at[i, 'category'], df.at[i, left_col]) for i in all_unallocated.index]
                print(f"Moving all rows: {cats}")

            # Move all unallocated rows
            for ridx in all_unallocated.index:
                v = df.at[ridx, left_col]
                df.at[ridx, left_col] = 0
                df.at[ridx, right_col] = df.at[ridx, right_col] + v

            return df
        # STRATEGY 2: Separate positive and negative candidates
        cand_positive = body[(body[left_col] > 0) & (body[right_col] == 0)].copy()
        cand_negative = body[(body[left_col] < 0) & (body[right_col] == 0)].copy()

        if cand_positive.empty and cand_negative.empty:
            if verbose:
                print("No candidate rows found.")
            return df

        # Handle negatives: they MUST be moved (they reduce the amount we need from positives)
        negative_sum = cand_negative[left_col].sum() if not cand_negative.empty else 0

        # Adjusted target: we need to find positives that sum to (over - negative_sum)
        # Because: positive_sum + negative_sum = over
        # Therefore: positive_sum = over - negative_sum
        adjusted_target = over - negative_sum

        if verbose and not cand_negative.empty:
            print(f"Found {len(cand_negative)} negative rows with sum={negative_sum}")
            print(f"Adjusted target for positive rows: {adjusted_target}")

        # Numeric handling: if values are essentially integers, use integer DP for subset-sum
        def is_integer_like(x):
            return abs(x - round(x)) < 1e-6

        target = adjusted_target
        integer_mode = is_integer_like(target) and all(is_integer_like(v) for v in cand_positive[left_col].tolist())

        # STRATEGY 3: Try exact subset-sum on positive candidates only
        if integer_mode:
            target_int = int(round(target))

            if target_int <= 0:
                if verbose:
                    print(f"Adjusted target is non-positive ({target_int}).")
                # Just move the negative rows if they exist
                if not cand_negative.empty:
                    if verbose:
                        print("Moving negative rows only.")
                    for ridx in cand_negative.index:
                        v = df.at[ridx, left_col]
                        df.at[ridx, left_col] = 0
                        df.at[ridx, right_col] = df.at[ridx, right_col] + v
                    return df
                return df

            vals = [int(round(v)) for v in cand_positive[left_col].tolist()]
            idxs = cand_positive.index.tolist()
            cap = sum(vals)

            if cap >= target_int:
                # DP to find one subset that sums exactly to target
                dp = [False] * (target_int + 1)
                prev = [None] * (target_int + 1)
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

                    # Move chosen positive rows
                    for ridx in chosen_df_indices:
                        v = int(round(df.at[ridx, left_col]))
                        df.at[ridx, left_col] = 0
                        df.at[ridx, right_col] = df.at[ridx, right_col] + v

                    # Also move all negative rows
                    for ridx in cand_negative.index:
                        v = df.at[ridx, left_col]
                        df.at[ridx, left_col] = 0
                        df.at[ridx, right_col] = df.at[ridx, right_col] + v

                    if verbose:
                        cats_pos = [(df.at[i, 'category'], int(round(df.at[i, right_col]))) for i in chosen_df_indices]
                        cats_neg = [(df.at[i, 'category'], int(round(df.at[i, right_col]))) for i in
                                    cand_negative.index]
                        print(f"Exact subset found. Moved positive rows: {cats_pos}")
                        if cats_neg:
                            print(f"Also moved negative rows: {cats_neg}")

                    return df
                else:
                    if verbose:
                        print(f"No exact subset sum found for adjusted target={target_int}")
            else:
                if verbose:
                    print(f"Sum of positive candidates ({cap}) < adjusted target ({target_int}). Cannot fix.")
        else:
            if verbose:
                print("Target or candidates are non-integer. Cannot use DP.")

        return df
