"""
title: MOSPI RAG Pipeline
author: mospi-team
date: 2025-07-02
version: 1.0
license: MIT
description: A RAG pipeline for retrieving relevant information from document
knowledge base using Qdrant vector store and Vanna SQL generation.
requirements: requests
"""

from typing import List, Union, Generator, Iterator, Optional
import json
import logging
import requests
import os
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Pipeline:
    class Valves(BaseModel):
        MOSPI_API_BASE_URL: str
        QDRANT_QUERY_LIMIT: int
        REQUEST_TIMEOUT: int

    def __init__(self):
        self.pipeline_ready = False
        self.valves = self.Valves(
            **{
                "MOSPI_API_BASE_URL": os.getenv(
                    "MOSPI_API_BASE_URL", "http://web:8000"
                ),
                "QDRANT_QUERY_LIMIT": int(os.getenv("QDRANT_QUERY_LIMIT", "5")),
                "REQUEST_TIMEOUT": int(os.getenv("REQUEST_TIMEOUT", "30")),
            }
        )

    async def on_startup(self):
        """Initialize the RAG pipeline components."""
        try:
            # Test API connectivity
            health_check_url = f"{self.valves.MOSPI_API_BASE_URL}/health/"
            response = requests.get(health_check_url, timeout=10)

            if response.status_code == 200:
                self.pipeline_ready = True
                logger.info(
                    f"RAG Pipeline initialized successfully. "
                    f"API Base: {self.valves.MOSPI_API_BASE_URL}"
                )
            else:
                logger.warning(
                    f"API health check failed with status " f"{response.status_code}"
                )
                self.pipeline_ready = False

        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            self.pipeline_ready = False

    async def on_shutdown(self):
        """Cleanup resources when server stops."""
        self.pipeline_ready = False

    def _query_enhanced_via_api(self, query: str) -> dict:
        """Query using the enhanced RAG pipeline."""
        try:
            # Use the enhanced API endpoint
            enhanced_url = f"{self.valves.MOSPI_API_BASE_URL}/api/query-enhanced/"
            
            payload = {"prompt": query}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                enhanced_url,
                json=payload,
                headers=headers,
                timeout=self.valves.REQUEST_TIMEOUT,
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                logger.error(f"Enhanced query failed: {response.status_code}: {response.text}")
                return {"error": f"Enhanced query failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Enhanced query failed: {e}")
            return {"error": f"Enhanced query failed: {str(e)}"}

    def _query_documents_via_api(
        self, query: str, limit: Optional[int] = None
    ) -> List[dict]:
        """Query documents via MOSPI Qdrant API."""
        try:
            # Use the correct API endpoint from vanna_adapter
            search_url = f"{self.valves.MOSPI_API_BASE_URL}/api/query-qdrant/"

            payload = {"prompt": query}

            headers = {"Content-Type": "application/json"}

            response = requests.post(
                search_url,
                json=payload,
                headers=headers,
                timeout=self.valves.REQUEST_TIMEOUT,
            )

            if response.status_code == 201:
                # API returns 201 for successful queries
                result = response.json()
                return result.get("data", [])
            elif response.status_code == 404:
                logger.info("No documents found for query")
                return []
            else:
                logger.error(
                    f"Document query failed with status "
                    f"{response.status_code}: {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Document query failed: {e}")
            return []

    def _generate_sql_via_api(self, query: str) -> dict:
        """Generate SQL insights via Enhanced MOSPI API (uses table mappings)."""
        try:
            # Use the enhanced API endpoint that combines Qdrant + table mappings
            enhanced_url = f"{self.valves.MOSPI_API_BASE_URL}/api/query-enhanced/"

            payload = {"prompt": query}

            headers = {"Content-Type": "application/json"}

            response = requests.post(
                enhanced_url,
                json=payload,
                headers=headers,
                timeout=self.valves.REQUEST_TIMEOUT,
            )

            if response.status_code == 201:
                # API returns 201 for successful queries
                result = response.json()
                return {
                    "text": result.get("text", ""),
                    "data": result.get("dataframe", []),
                    "chart": result.get("figure", None),
                    "tables_used": result.get("table_names_identified", []),
                    "documents_relevance": result.get("documents_relevance", []),  # Extract document relevance data
                }
            elif response.status_code == 404:
                return {"error": "No response from enhanced API"}
            else:
                logger.error(
                    f"Enhanced SQL generation failed with status "
                    f"{response.status_code}: {response.text}"
                )
                return {"error": f"Enhanced SQL generation failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Enhanced SQL generation failed: {e}")
            return {"error": f"Enhanced SQL generation failed: {str(e)}"}

    def _create_markdown_table(self, data: List[dict]) -> str:
        """Convert list of dictionaries to markdown table format."""
        if not data or len(data) == 0:
            return "No data available."

        # Get all unique keys from all records to handle varying structures
        all_keys = set()
        for record in data:
            if isinstance(record, dict):
                all_keys.update(record.keys())

        if not all_keys:
            return "No valid data structure found."

        # Sort keys for consistent column order
        headers = sorted(list(all_keys))

        # Create markdown table
        table_lines = []

        # Header row
        header_row = "| " + " | ".join(headers) + " |"
        table_lines.append(header_row)

        # Separator row
        separator_row = "|" + "|".join([" --- " for _ in headers]) + "|"
        table_lines.append(separator_row)

        # Data rows
        for record in data:
            if isinstance(record, dict):
                row_values = []
                for header in headers:
                    value = record.get(header, "")
                    # Handle None values and convert to string
                    if value is None:
                        value = ""
                    else:
                        value = str(value)
                    # Escape pipe characters in values to avoid breaking table
                    value = value.replace("|", "\\|")
                    row_values.append(value)

                row = "| " + " | ".join(row_values) + " |"
                table_lines.append(row)

        return "\n".join(table_lines)

    def _format_response(
        self, query: str, documents: List[dict], sql_result: Optional[dict] = None
    ) -> str:
        """Format the RAG response combining document retrieval and SQL."""

        response_parts = []

        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response_parts.append(f"**MOSPI RAG Response** _(Generated at {timestamp})_\n")

        # Add SQL insights if available
        if sql_result and "error" not in sql_result:
            response_parts.append("## Data Analysis Results")

            if sql_result.get("text"):
                response_parts.append(sql_result["text"])

            if sql_result.get("data"):
                # Handle JSON string or list format
                data = sql_result["data"]
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        data = []

                if data and len(data) > 0:
                    data_count = len(data)
                    response_parts.append(
                        f"\n**Found {data_count} relevant data points**"
                    )

                    # Create markdown table from data
                    response_parts.append("\n**Data Table:**")
                    markdown_table = self._create_markdown_table(data)
                    response_parts.append(markdown_table)

            # if sql_result.get("chart"):
            #     response_parts.append(
            #         f"<iframe>\n{sql_result['chart']}\n</iframe>"
            #     )

        elif sql_result and "error" in sql_result:
            response_parts.append(f"## Data Analysis\n{sql_result['error']}")

        # Add document retrieval results
        if documents:
            response_parts.append(f"\n## Relevant Documents ({len(documents)} found)")

            for i, doc in enumerate(documents, 1):
                score = doc.get("score", 0)
                # Handle Qdrant response format
                payload = doc.get("payload", {})
                content = doc.get("document", {})
                metadata = doc.get("metadata", {})

                # Try different filename field names
                filename = (
                    payload.get("filename")
                    or payload.get("file_name")
                    or metadata.get("filename")
                    or metadata.get("file_name")
                    or f"Document {i}"
                )

                # Truncate content for display
                content_preview = content

                response_parts.append(f"\n**{filename}** (Relevance: {score:.2f})")
                response_parts.append(f"```\n{content_preview}\n```")

        else:
            response_parts.append("\n## Document Search")
            response_parts.append("No relevant documents found in the knowledge base.")

        return "\n".join(response_parts)

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """Main RAG pipeline processing."""

        if not self.pipeline_ready:
            return (
                "RAG Pipeline not ready. Please check configuration and "
                "ensure MOSPI API is accessible."
            )

        try:
            # Generate SQL insights using enhanced API (includes table mappings + document relevance)
            sql_result = self._generate_sql_via_api(user_message)
            
            # Extract document relevance data from the enhanced API response
            documents = []
            if sql_result and "error" not in sql_result:
                documents = sql_result.get("documents_relevance", [])
            
            # Format comprehensive response with both SQL results and document relevance
            response = self._format_response(user_message, documents, sql_result)

            return response

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            return (
                f"Error processing your request: {str(e)}\n\n"
                f"Please ensure MOSPI API is accessible at: "
                f"{self.valves.MOSPI_API_BASE_URL}"
            )

    def get_pipeline_status(self) -> dict:
        """Get current pipeline status."""
        return {
            "ready": self.pipeline_ready,
            "api_base_url": self.valves.MOSPI_API_BASE_URL,
            "qdrant_query_limit": self.valves.QDRANT_QUERY_LIMIT,
            "request_timeout": self.valves.REQUEST_TIMEOUT,
            "timestamp": datetime.now().isoformat(),
        }