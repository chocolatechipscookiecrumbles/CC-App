from . import *
from programlauncher.common.pdf_manifest import build_pdf_manifest
from programlauncher.common.sports import normalize_sport_name
from .write_report import write_report


def clean_sport_name(name):
    return normalize_sport_name(name)

def extract_scholarships(pdf_path):
    male_data = {}
    female_data = {}

    section = None   # track across pages
    buffer_line = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                #return None, None
                continue

            # Only enter once we are in the Athletic Student Aid block
            if section is None and re.search(r"Male\s*Athlete\s*Scholarships", text, re.I) is False:
                    continue
            #print(3)
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                #print(line)

                # Switch capture state
                # Detect section switches (allow missing spaces or extra spaces)
                if re.search(r"Female\s*Athlete\s*Scholarships", line, re.I):
                    section = "female"
                    # print(f"DEBUG: Switched to FEMALE section, line was: '{line}'")
                    buffer_line = ""
                    continue
                elif re.search(r"^Male\s*Athlete\s*Scholarships", line, re.I):
                    section = "male"
                    #print(f"DEBUG: Switched to MALE section: '{line}'")
                    buffer_line = ""
                    continue



                elif re.search(r"Not\s*Allocated\s*by\s*Gender\s*Scholarships", line, re.I):
                    section = None
                    buffer_line = ""
                    continue

                if section in ["male", "female"]:
                    # Merge split sport names across lines
                    if re.search(r"NCAA|Page|Report|System|AthleticAid|Equivalencies|Receiving|Medical|Totals", line, re.I):
                        continue
                    if buffer_line:
                        line = buffer_line + " " + line
                        buffer_line = ""

                    if line.endswith(",") or line.endswith("-"):
                        buffer_line = line
                        continue

                    #match = re.match(r"([A-Za-z ,\-]+)\s+([\d]+(?:\.\d+)?)", line)
                    #match = re.match(r"([A-Za-z ,\-]+)\s+(-?\d[\d,]*(?:\.\d+)?)", line)
                    match = re.match(r"([A-Za-z ,\-]+?)\s+(-?\d[\d,]*(?:\.\d+)?)", line)
                    if match:
                        sport = match.group(1).strip()
                        #equivalency = float(match.group(2))
                        equivalency = float(match.group(2).replace(",", ""))
                        if section == "male":
                            male_data[sport] = equivalency
                        elif section == "female":
                            female_data[sport] = equivalency
                    else:
                        #print('no match')
                        pass

    return male_data, female_data

def process_folder(
    folder_path,
    exclude_words=None,
    manifest=None,
    summary=None,
    progress_reporter=None,
    cancel_token=None,
):
    """
    Process an entire folder of PDFs, return two DataFrames (male, female)
    and a list of all unique sports across all files.
    """
    nonpdf= []
    all_male_data = {}
    all_female_data = {}
    unique_sports_m = set()
    unique_sports_f = set()
    #pdf_count = len([f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")])
    count = 0

    records = manifest if manifest is not None else build_pdf_manifest(folder_path)

    total = len(records)

    for index, record in enumerate(records, start=1):
        if cancel_token and cancel_token.is_cancelled:
            if summary:
                summary.cancelled = True
            break

        file = record.filename
        pdf_path = record.path
        institution_name = record.institution_name

        if progress_reporter:
            progress_reporter.update(
                current=index,
                total=total,
                institution=institution_name,
                stage="Extracting scholarships",
                skipped_count=summary.skipped_count if summary else len(nonpdf),
            )

        '''male, female = extract_scholarships(pdf_path)
        if male == {} and female == {}:
            print(2)
            continue'''


        male, female = extract_scholarships(pdf_path)

        # Apply exclusion FIRST
        if exclude_words:
            pattern = re.compile(r"|".join(re.escape(w) for w in exclude_words), re.IGNORECASE)
            male = {k: v for k, v in male.items() if not pattern.search(k)}
            female = {k: v for k, v in female.items() if not pattern.search(k)}

        # THEN check emptiness
        if not male and not female:
            if summary:
                summary.add_skipped(
                    file,
                    path=pdf_path,
                    institution_name=institution_name,
                    reason="empty_result",
                    stage="scholarship_extraction",
                )
            else:
                nonpdf.append(file)
            continue

        # Save for DataFrame construction
        count += 1
        if summary:
            summary.add_processed()
        all_male_data[institution_name] = male or {}
        all_female_data[institution_name] = female or {}
        '''if client:
            if client and str(client).lower() in str(institution_name).lower():'''
        unique_sports_m.update(male.keys())
        unique_sports_f.update(female.keys())

        '''# Add to unique sports list
        unique_sports.update(male.keys())
        unique_sports.update(female.keys())'''
    parsed_unique_sports_m = []
    parsed_unique_sports_f = []


    parsed_unique_sports_m = [normalize_sport_name(sport) for sport in unique_sports_m]
    parsed_unique_sports_f = [normalize_sport_name(sport) for sport in unique_sports_f]

    # Deduplicate + sort each
    parsed_unique_sports_m = sorted(set(parsed_unique_sports_m))
    parsed_unique_sports_f = sorted(set(parsed_unique_sports_f))


    # Build DataFrames
    # Makes sure that female/male only unis still appear

    # Get full union of columns for male/female
    all_sports_m = sorted(set().union(*[d.keys() for d in all_male_data.values()])) if all_male_data else []
    all_sports_f = sorted(set().union(*[d.keys() for d in all_female_data.values()])) if all_female_data else []


    # Build DataFrames with all columns
    male_df = pd.DataFrame(all_male_data, index=all_sports_m).T.fillna(0)
    female_df = pd.DataFrame(all_female_data, index=all_sports_f).T.fillna(0)

    female_sorted = female_df.sort_index(ascending=True)
    male_sorted = male_df.sort_index(ascending=True)
    '''print("Unique sports for client:", parsed_unique_sports)
    print("Columns in male_df:", male_sorted.columns.tolist())
    print("Columns in female_df:", female_sorted.columns.tolist())'''
    '''names = list(all_male_data.keys())
    dupes = [name for name, cnt in Counter(names).items() if cnt > 1]

    print("Duplicate institution names:", dupes)
    print("Number duplicates:", len(dupes))
    print("Total unique institutions:", len(names))'''
    write_report(folder_path, summary.skipped_files if summary else nonpdf)
    #print(male_df, female_df)
    return male_sorted, female_sorted, parsed_unique_sports_m,parsed_unique_sports_f, count
