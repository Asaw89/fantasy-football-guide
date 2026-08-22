from ingest import ingest_season, init_db

init_db()
print("Loading 2023...")
n2023 = ingest_season(2023)
print(f"2023 total: {n2023} rows\n")
print("Loading 2024...")
n2024 = ingest_season(2024)
print(f"2024 total: {n2024} rows")
print(f"\nGrand total: {n2023 + n2024} rows across both seasons.")
