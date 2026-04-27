import pandas as pd


def target_finder(json_data, target_ref: str) -> dict:
    """
    Find the target reference in the JSON data.
    The target_ref will be in the format #/path/to/target, and the function will search for it recursively.

    Args:
        json_data (dict): The JSON data to search.
        target_ref (str): The target reference to find.

    Returns:
        dict: The found target reference or None if not found.
    """
    split_ref = target_ref.lstrip("#").split("/")
    current_data = json_data
    for key in split_ref:
        if isinstance(current_data, dict) and key in current_data:
            current_data = current_data[key]
        elif (
            isinstance(current_data, list)
            and key.isdigit()
            and int(key) < len(current_data)
        ):
            current_data = current_data[int(key)]
        elif key == "":
            current_data = json_data  # Target reference not found, return original JSON
        else:
            return json_data

    return current_data


def update_data_in_target(json_data, target_ref: str, new_data: dict) -> dict:
    """
    Update the data in the target reference within the JSON data.

    Args:
        json_data (dict): The JSON data to update.
        target_ref (str): The target reference to update.
        new_data (dict): The new data to set at the target reference.

    Returns:
        dict: The updated JSON data.
    """
    split_ref = target_ref.lstrip("#").split("/")
    current_data = json_data
    for key in split_ref[:-1]:
        if isinstance(current_data, dict) and key in current_data:
            current_data = current_data[key]
        elif (
            isinstance(current_data, list)
            and key.isdigit()
            and int(key) < len(current_data)
        ):
            current_data = current_data[int(key)]
        elif key == "":
            current_data = json_data  # Target reference not found, return original JSON
        else:
            return json_data  # If the path is invalid, return original JSON

    # Set the new data at the target reference
    last_key = split_ref[-1]
    if isinstance(current_data, dict):
        current_data[last_key] = new_data
    elif (
        isinstance(current_data, list)
        and last_key.isdigit()
        and int(last_key) < len(current_data)
    ):
        current_data[int(last_key)] = new_data

    return json_data


def update_table_header(json_data, target_ref: str, source_ref: str) -> dict:
    """
    Update the table header in the JSON data based on the source reference.

    Args:
        json_data (dict): The JSON data to update.
        target_ref (str): The target reference to update.
        source_ref (str): The source reference to copy from.

    Returns:
        dict: The updated JSON data.
    """
    target_data = target_finder(json_data, target_ref)
    source_data = target_finder(json_data, source_ref)

    if target_data is not None and source_data is not None:
        offset = 0
        for row in source_data.get("data", {}).get("grid", []):
            if len(row) > 0:
                # Assuming the first row is the header
                is_column_header = row[0].get("column_header", False)
                if is_column_header:
                    target_data["data"]["grid"].insert(offset, row)
                    offset += 1

        updated_json = update_data_in_target(json_data, target_ref, target_data)

        return updated_json

    return json_data


def remove_table_header(json_data, target_ref: str) -> dict:
    """
    Remove the table header from the JSON data at the specified target reference.

    Args:
        json_data (dict): The JSON data to update.
        target_ref (str): The target reference to remove the header from.

    Returns:
        dict: The updated JSON data with the header removed.
    """
    target_data = target_finder(json_data, target_ref)

    if target_data is not None and "data" in target_data and "grid" in target_data["data"]:
        # Assuming the first row is the header
        if len(target_data["data"]["grid"]) > 0:
            is_column_header = target_data["data"]["grid"][0].get("column_header", False)
            if is_column_header:
                del target_data["data"]["grid"][0]  # Remove the first row

        updated_json = update_data_in_target(json_data, target_ref, target_data)
        return updated_json

    return json_data


def validate_target_ref(json_data, target_ref: str) -> bool:
    """
    Validate the target reference format.

    Args:
        target_ref (str): The target reference to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    split_ref = target_ref.lstrip("#").split("/")
    current_data = json_data
    for key in split_ref[:-1]:
        if isinstance(current_data, dict) and key in current_data:
            current_data = current_data[key]
        elif (
            isinstance(current_data, list)
            and key.isdigit()
            and int(key) < len(current_data)
        ):
            current_data = current_data[int(key)]
        elif key == "":
            current_data = json_data  # Target reference not found, return original JSON
        else:
            return False  # If the path is invalid, return original JSON
    return True


def export_to_dataframe(table_json: dict) -> pd.DataFrame:
    """Export the table as a Pandas DataFrame."""
    print(
        f"🔧 STARTING DataFrame export for table with {table_json['data']['num_rows']} rows and {table_json['data']['num_cols']} columns"
    )

    if table_json["data"]["num_rows"] == 0 or table_json["data"]["num_cols"] == 0:
        print("❌ Empty table - returning empty DataFrame")
        return pd.DataFrame()

    # Count how many rows are column headers
    num_headers = 0
    for i, row in enumerate(table_json["data"]["grid"]):
        if len(row) == 0:
            raise RuntimeError(
                f"Invalid table. {len(row)=} but {table_json['data']['num_cols']=}."
            )

        if row[0].get("column_header", False):
            num_headers += 1
        else:
            break

    print(f"🔧 Found {num_headers} header rows")

    # Create the column names from all col_headers
    columns = None
    if num_headers > 0:
        columns = ["" for _ in range(table_json["data"]["num_cols"])]
        for i in range(num_headers):
            for j, cell in enumerate(table_json["data"]["grid"][i]):
                col_name = cell["text"]
                if columns[j] != "":
                    col_name = f".{col_name}"
                columns[j] += col_name
        print(f"🔧 Column headers created: {columns}")
    else:
        print("🔧 No headers found - using default column names")

    # Create table data
    table_data = [
        [cell["text"] for cell in row] for row in table_json["data"]["grid"][num_headers:]
    ]

    print(f"🔧 Extracted {len(table_data)} data rows")
    if len(table_data) > 0:
        print(f"🔧 Sample data row: {table_data[0][:5]}...")  # Show first 5 cells of first row

    # Create DataFrame
    df = pd.DataFrame(table_data, columns=columns)

    print(f"✅ DataFrame created successfully: Shape {df.shape}")
    return df

