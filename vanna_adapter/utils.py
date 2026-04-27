from typing import List, Dict
from uploader.models import ExtractedTableMapping


def extract_file_ids_from_documents(documents: List[Dict]) -> List[str]:
    file_ids = []
    for doc in documents:
        payload = doc.get("payload", {})
        metadata = doc.get("metadata", {})
        
        file_id = payload.get("file_id") or metadata.get("file_id")
        if file_id:
            file_ids.append(str(file_id))
    
    return list(set(file_ids))


def get_table_names_from_file_ids(file_ids: List[str]) -> List[str]:
    if not file_ids:
        return []
    
    try:
        numeric_ids = []
        for fid in file_ids:
            try:
                numeric_ids.append(int(fid))
            except (ValueError, TypeError):
                continue
        
        if not numeric_ids:
            return []
        
        table_mappings = ExtractedTableMapping.objects.filter(
            file__id__in=numeric_ids
        ).values_list('table_name', flat=True)
        
        table_names = list(table_mappings)
        return table_names
        
    except Exception:
        return []