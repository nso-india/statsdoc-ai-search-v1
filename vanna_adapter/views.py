import json
import io
from typing import List, Dict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from qdrant_adapter.qdrant_adapter import init_connection
from .core import init_vanna_adapter, get_universal_sql_prompt
from .utils import extract_file_ids_from_documents, get_table_names_from_file_ids


class QueryEnhancedView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"error": "Prompt is required"}, status=400)
        
        documents_data = []
        table_names = []
        try:
            qdrant_client = init_connection()
            print(f"Querying Qdrant for enhanced data")
            documents = qdrant_client.query(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_text=prompt,
                limit=min(100, settings.QDRANT_QUERY_LIMIT * 10),
            )
            print(f"Qdrant returned {len(documents) if documents else 0} documents for enhanced query")
            
            if documents:
                documents_data = [item.model_dump() for item in documents]
                file_ids = extract_file_ids_from_documents(documents_data)
                table_names = get_table_names_from_file_ids(file_ids)
        except Exception:
            pass
        
        vn = init_vanna_adapter(table_names=table_names)
        
        vn_response = vn.ask(prompt, allow_llm_to_see_data=True)
        if not vn_response:
            return Response({"error": "No response from Vanna"}, status=404)
            
        text, df, fig = vn_response
        if df is not None:
            df = df.to_json(orient="records")
        if fig is not None:
            buf = io.StringIO()
            fig.write_html(buf)
            buf.seek(0)
            figure = buf.getvalue()
        else:
            figure = None
            
        return Response({
            "text": text,
            "dataframe": df,
            "figure": figure,
            "table_names_identified": table_names,
            "documents_relevance": documents_data,
        }, status=201)

