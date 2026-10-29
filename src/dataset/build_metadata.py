from pathlib import Path
import re
import pandas as pd


# ============================================================
# OASIS-1 SOURCE DIRECTORIES
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_ROOTS = [
    PROJECT_ROOT / "data" / "raw" / "oasis_cross-sectional_disc5",
    PROJECT_ROOT / "data" / "raw",
    Path(r"C:\Users\ACER\Downloads\oasis_cross-sectional_disc1 (1)\disc1"),
    Path(r"C:\Users\ACER\Downloads\oasis_cross-sectional_disc2\disc2"),
    Path(r"C:\Users\ACER\Downloads\oasis_cross-sectional_disc3\disc3"),
    Path(r"C:\Users\ACER\Downloads\oasis_cross-sectional_disc4\disc4"),
]

OFFICIAL_EXCEL_FILE = PROJECT_ROOT / "data" / "metadata" / "oasis1_official.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "data" / "metadata" / "oasis_metadata.csv"


# ============================================================
# CDR → CLASS MAPPING (OFFICIAL OASIS CLINICAL CRITERIA)
# ============================================================

CDR_TO_CLASS = {
    0.0: (0, "Cognitively Normal"),
    0.5: (1, "Very Mild Dementia"),
    1.0: (2, "Mild Dementia"),
    2.0: (3, "Moderate Dementia"),
}


# ============================================================
# PARSE PATIENT INFORMATION
# ============================================================

def parse_patient(patient_folder: Path, official_excel_df: pd.DataFrame = None):
    """
    Extract patient metadata using both local session text files and
    the official OASIS clinical Excel document.
    """
    patient_folder = Path(patient_folder)
    txt_files = list(patient_folder.glob("*.txt"))

    text_info = {}
    if txt_files:
        text = txt_files[0].read_text(encoding="utf-8", errors="ignore")

        def extract(pattern):
            match = re.search(pattern, text, re.MULTILINE)
            return match.group(1).strip() if match else None

        text_info["patient_id"] = extract(r"^\s*SESSION ID:\s*(.+)")
        text_info["age"] = extract(r"^\s*AGE:\s*(\d+)")
        text_info["sex"] = extract(r"^\s*M/F:\s*(.+)")
        text_info["education"] = extract(r"^\s*EDUC:\s*(\d+)")
        text_info["cdr"] = extract(r"^\s*CDR:\s*([0-9.]+)")
        text_info["mmse"] = extract(r"^\s*MMSE:\s*([0-9.]+)")

    patient_id = text_info.get("patient_id") or patient_folder.name
    
    # Priority check with official OASIS Excel file
    excel_row = None
    if official_excel_df is not None and patient_id in official_excel_df.index:
        excel_row = official_excel_df.loc[patient_id]

    age_val = None
    sex_val = text_info.get("sex")
    education_val = None
    cdr_val = None
    mmse_val = None

    if excel_row is not None:
        if pd.notna(excel_row.get("Age")):
            age_val = int(excel_row["Age"])
        if pd.notna(excel_row.get("M/F")):
            sex_val = str(excel_row["M/F"]).strip()
        if pd.notna(excel_row.get("Educ")):
            education_val = int(excel_row["Educ"])
        if pd.notna(excel_row.get("CDR")):
            cdr_val = float(excel_row["CDR"])
        if pd.notna(excel_row.get("MMSE")):
            mmse_val = float(excel_row["MMSE"])
    else:
        if text_info.get("age"):
            age_val = int(text_info["age"])
        if text_info.get("education"):
            education_val = int(text_info["education"])
        if text_info.get("cdr"):
            cdr_val = float(text_info["cdr"])
        if text_info.get("mmse"):
            mmse_val = float(text_info["mmse"])

    if cdr_val is None or cdr_val not in CDR_TO_CLASS:
        return None

    class_id, class_name = CDR_TO_CLASS[cdr_val]

    return {
        "patient_id": patient_id,
        "age": age_val,
        "sex": sex_val,
        "education": education_val,
        "cdr": cdr_val,
        "mmse": mmse_val,
        "class_id": class_id,
        "class_name": class_name,
        "mri_folder": str(patient_folder),
    }


# ============================================================
# BUILD METADATA
# ============================================================

def main():
    records = []

    print("=" * 60)
    print("Building / Updating OASIS-1 Metadata")
    print("=" * 60)

    # 1. Load official clinical Excel if available
    df_excel = None
    if OFFICIAL_EXCEL_FILE.exists():
        try:
            df_excel = pd.read_excel(OFFICIAL_EXCEL_FILE)
            if "ID" in df_excel.columns:
                df_excel["ID"] = df_excel["ID"].astype(str).str.strip()
                df_excel = df_excel.set_index("ID")
                print(f"Loaded official OASIS clinical Excel: {len(df_excel)} records")
        except Exception as e:
            print(f"Warning: Could not read official Excel: {e}")

    # 2. Preserve existing metadata records if present
    existing_records = {}
    if OUTPUT_FILE.exists():
        try:
            df_existing = pd.read_csv(OUTPUT_FILE)
            for _, row in df_existing.iterrows():
                existing_records[row["patient_id"]] = row.to_dict()
            print(f"Loaded existing metadata: {len(existing_records)} patients")
        except Exception as e:
            print(f"Warning loading existing CSV: {e}")

    # 3. Scan directories
    scanned_folders = {}
    for root in DATA_ROOTS:
        if not root.exists():
            continue

        print(f"\nScanning: {root}")
        if root.name.startswith("OAS1_"):
            patient_folders = [root]
        else:
            patient_folders = [
                p for p in root.iterdir()
                if p.is_dir() and p.name.startswith("OAS1_")
            ]

        print(f"Patients discovered: {len(patient_folders)}")
        for pf in patient_folders:
            if pf.name not in scanned_folders:
                scanned_folders[pf.name] = pf

    # 4. Parse records
    for patient_id, pf in scanned_folders.items():
        rec = parse_patient(pf, official_excel_df=df_excel)
        if rec is not None:
            records.append(rec)

    # Combine with existing if any paths weren't re-scanned
    for pid, old_rec in existing_records.items():
        if pid not in [r["patient_id"] for r in records]:
            records.append(old_rec)

    df = pd.DataFrame(records)

    if df.empty:
        print("\nERROR: No valid patients found.")
        return

    df = df.drop_duplicates(subset=["patient_id"], keep="first")
    df = df.sort_values("patient_id").reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 60)
    print(f"Total Valid Patients with CDR: {len(df)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("=" * 60)

    print("\n4-Class Distribution:")
    classes = [
        ("Cognitively Normal", 0),
        ("Very Mild Dementia", 1),
        ("Mild Dementia", 2),
        ("Moderate Dementia", 3),
    ]
    moderate_count = 0
    for name, c_id in classes:
        cnt = int((df["class_id"] == c_id).sum()) if "class_id" in df.columns else 0
        if c_id == 3:
            moderate_count = cnt
        print(f"  {name}: {cnt} patients")

    print("\nCDR Distribution:")
    print(df["cdr"].value_counts().sort_index())

    if moderate_count == 0:
        print("\n" + "=" * 70)
        print("Moderate Dementia samples are currently unavailable in dataset.")
        print("=" * 70)

    print("\nDone.")


if __name__ == "__main__":
    main()