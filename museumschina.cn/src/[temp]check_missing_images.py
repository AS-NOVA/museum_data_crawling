import csv

csv_file = r'd:\LocalWorkSpace\20260202_museum_data_crawling\museumschina.cn\data\pottery_details_20260305_210613.csv'

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print(f"Checking file: {csv_file}")
    print(f"Columns found: {reader.fieldnames}")
    
    missing_data = []
    
    for i, row in enumerate(reader, start=1): # start=1 to match Excel row numbers (header is usually row 1, data starts row 2, but let's just say "Data Row X")
        # logical_row_number = i + 1 # if we consider header as row 1
        
        main_img = row.get('main_image_url', '').strip()
        gallery = row.get('gallery_urls', '').strip()
        
        missing = []
        if not main_img:
            missing.append('main_image_url')
        if not gallery:
            missing.append('gallery_urls')
            
        if missing:
            missing_data.append(f"Row {i+1} (ID: {row.get('id', 'N/A')}): Missing {', '.join(missing)}")

    if missing_data:
        print(f"Found {len(missing_data)} rows with missing information:")
        for item in missing_data:
            print(item)
    else:
        print("No rows found with missing main_image_url or gallery_urls.")
