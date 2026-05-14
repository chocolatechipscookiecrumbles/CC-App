from . import *
from programlauncher.common.pdf_manifest import build_pdf_manifest
from programlauncher.common.sports import MENS_ONLY_SPORTS, WOMENS_ONLY_SPORTS
from .config import SPORTOPS_TABLE_NUMS
from .Table_Extractor import extract_tables_by_title
from .write_report import write_report

def collect_sports_across_pdfs(folder_path, manifest=None):
    """
    Parse all PDFs in a folder using extract_tables_by_title and aggregate results.

    Returns:
        dict[str, pd.DataFrame]
        Key = sport name (or sport + " (Men)" / " (Women)" if split by gender)
        Value = dataframe where:
            - Rows = pdf filenames (universities)
            - Columns = table titles from extract_tables_by_title()
            - Cell = numeric value (or NaN if not present)
    """

    sport_dfs = {}  # sport_name -> pd.DataFrame
    mens_only = MENS_ONLY_SPORTS
    womens_only = WOMENS_ONLY_SPORTS
    table_nums = SPORTOPS_TABLE_NUMS
    mens_list = set()
    womens_list = set()
    skipped_list = []

    def ensure_sport_df(sport_key):
        """Initialize sport dataframe with all columns if it doesn't exist."""
        if sport_key not in sport_dfs:
            sport_dfs[sport_key] = pd.DataFrame(columns=table_nums)
    records = manifest if manifest is not None else build_pdf_manifest(folder_path)

    for record in records:
        filename = record.filename
        institution_name = record.institution_name
        pdf_path = record.path
        tables = extract_tables_by_title(pdf_path)
        if tables == 1:
            skipped_list.append(filename)
            continue

        for table_title, df in tables.items():
            #print(table_title,df)
            # normalize columns
            #df = df.rename(columns=lambda c: c.strip().lower())
            #mask_valid = ~df['category'].str.lower().str.contains("team")
            #df_fixed = fix_misattributions_coeffs(df.loc[mask_valid])


            df_fixed = fix_misattributions_coeffs(df)
            df.update(df_fixed)
            df = df.set_index('category')
            for row_tuple in df.itertuples(index=True, name=None):
                index = row_tuple[0]
                row = dict(zip(df.columns, row_tuple[1:]))
                sport_name = normalize_sport_name(index.strip())
                if "expenses" in sport_name.lower() or "team" in sport_name.lower()or "others" in sport_name.lower():
                    continue
                men_val = row.get('men', None)
                women_val = row.get('women', None)

                # Decide if we create one df or two
                if sport_name not in mens_only and sport_name not in womens_only:
                    # Two separate DFs (Men's and Women's)
                    for gender, val in [("Men's", men_val), ("Women's", women_val)]:
                        sport_key = f"{gender} {sport_name}"
                        if gender=="Men's":
                            mens_list.add(sport_key)
                        elif gender=="Women's":
                            womens_list.add(sport_key)
                        ensure_sport_df(sport_key)

                        sport_dfs[sport_key].loc[institution_name, table_title.split()[0]] = val
                else:
                    # Single-gender sports
                    if sport_name in mens_only:
                        sport_key = sport_name
                        ensure_sport_df(sport_key)
                        sport_dfs[sport_key].loc[institution_name, table_title.split()[0]] = men_val
                        if sport_key.lower() == "rifle":
                            womens_list.add(sport_key)
                            #sometimes rifle gets moved to women's column when its in the misattribution calculation, this makes sure it is captured
                            sport_dfs[sport_key].loc[institution_name, table_title.split()[0]] += women_val
                        else:
                            mens_list.add(sport_key)
                        #mens_list.add(sport_key)
                    elif sport_name in womens_only:
                        sport_key = sport_name
                        ensure_sport_df(sport_key)
                        sport_dfs[sport_key].loc[institution_name, table_title.split()[0]] = women_val
                        womens_list.add(sport_key)

    # sort rows and columns for readability
    for sport in sport_dfs:
        sport_dfs[sport] = sport_dfs[sport].sort_index().sort_index(axis=1)
    write_report(folder_path,skipped_list)
    return sport_dfs, mens_list, womens_list
