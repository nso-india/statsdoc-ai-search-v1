import copy

from docling_core.types.doc.document import DoclingDocument


def strip_null_meta_from_docling_json(docling_json):
    """
    docling-serve can return null `meta` on tables/body nodes while older
    docling-core schemas reject those values. Remove them before validation.
    """
    data = copy.deepcopy(docling_json)

    def walk(node):
        if isinstance(node, dict):
            if node.get("meta") is None:
                node.pop("meta", None)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return data


def parse_docling_document(docling_json):
    cleaned = strip_null_meta_from_docling_json(docling_json)
    return DoclingDocument.model_validate(cleaned)
