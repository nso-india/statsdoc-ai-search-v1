import uuid
import requests
import json
import asyncio
import sys
from celery import shared_task
from litellm import completion

from django.conf import settings
from django.db.utils import DataError, OperationalError

from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from docling_core.types.doc.document import DoclingDocument
from docling.chunking import HybridChunker


from qdrant_adapter.qdrant_adapter import init_connection

from chat.utils import get_llm_response
from chat.models import Chat, Message
from chat.consumers import ChatConsumer

from .models import UploadedFile, ExtractedTableMapping, Comment
from .constants import (
    FAILED,
    COMPLETED,
    IN_PROGRESS,
    POST_REVIEW_PROCESSING,
)

from vanna_adapter.tasks import train_vanna
from .utils import validate_target_ref, export_to_dataframe
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


# This file contains the Celery tasks for the uploader app.
@shared_task
def process_uploaded_file(file_ids, knowledge_base_id=None):
    """
    Process uploaded file(s) without chat or websocket logic.
    Accepts a single file id or a list of file ids.
    """
    from .models import KnowledgeBase
    
    # Get knowledge base if provided
    knowledge_base = None
    if knowledge_base_id:
        try:
            knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
        except KnowledgeBase.DoesNotExist:
            print(f"Knowledge base with id {knowledge_base_id} not found, continuing without it.")

    # Normalize to list
    if not isinstance(file_ids, list):
        file_ids = [file_ids]

    for file_id in file_ids:
        try:
            file = UploadedFile.objects.get(id=file_id)
        except UploadedFile.DoesNotExist:
            print(f"File with id {file_id} not found, skipping.")
            continue

        print(f"Processing file: {file.file_name}")
        file.status = IN_PROGRESS
        file.save()

        file_process_url = settings.DOCLING_URL + "/v1/convert/file"
        headers = {}
        # Create JSON data for the file processing API
        json_data = {
            "to_formats": ["md", "json"],
            "image_export_mode": "embedded",
            "do_ocr": True,
            "force_ocr": False,
            "ocr_engine": settings.OCR_ENGINE,
            "ocr_lang": settings.OCR_LANG,
            "pdf_backend": "dlparse_v4",
            "table_mode": "accurate",
            "pipeline": "standard",
            "document_timeout": 604800,
            "abort_on_error": False,
            "return_as_file": False,
            "do_table_structure": True,
            "include_images": True,
        }

        # Send the request
        try:
            response = requests.post(
                url=file_process_url,
                headers=headers,
                data=json_data,
                files={"files": file.file},
            )
        except Exception as e:
            print(f"Error calling Docling service for file {file.id}: {e}")
            file.status = FAILED
            file.save()
            continue

        # Check the response
        print(f"Docling response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Docling returned non-200 for file {file.id}: {response.status_code}")
            file.status = FAILED
            file.save()
            continue

        print("File processed successfully.")
        # Save raw response for debugging if needed
        try:
            with open("processed_file.json", "wb") as f:
                f.write(response.content)
        except Exception:
            # ignore write errors in production
            pass

        try:
            response_json = response.json()
            docling_json = response_json.get("document", {}).get("json_content")
        except Exception as e:
            print(f"Error parsing Docling response for file {file.id}: {e}")
            file.status = FAILED
            file.save()
            continue

        if not docling_json:
            print(f"No docling json returned for file {file.id}")
            file.status = FAILED
            file.save()
            continue

        # Validate Docling JSON
        try:
            docling_obj: DoclingDocument = DoclingDocument.model_validate(docling_json)
            print("DoclingDocument validation successful!")
        except Exception as e:
            print(f"Error validating DoclingDocument for file {file.id}: {e}")
            file.status = FAILED
            file.save()
            continue

        # Process the Docling JSON data
        try:
            file.docling_json = docling_json
            file.save()
        except (DataError, OperationalError) as e:
            # Database error due to size constraint or other database issues
            print(f"Database error saving docling_json for file {file.id}: {e}")
            
            # Calculate size for error message
            try:
                json_str = json.dumps(docling_json)
                json_size_mb = sys.getsizeof(json_str) / (1024 * 1024)
                size_info = f" (size: {json_size_mb:.2f}MB)"
            except:
                size_info = ""
            
            file.docling_json = None  # Clear the oversized data
            file.status = FAILED
            file.other_info = {
                "error": "Document data exceeds database storage limits",
                "message": f"The document '{file.file_name}' was processed but could not be stored due to database constraints{size_info}. The database has a maximum storage limit for document data.",
                "technical_error": str(e)[:200]  # Truncate error message
            }
            file.save()
            continue
        except Exception as e:
            print(f"Unexpected error saving file {file.id}: {e}")
            file.status = FAILED
            file.save()
            continue

        tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(settings.QDRANT_EMBEDDING_MODEL),
        )
        chunker = HybridChunker(
            tokenizer=tokenizer,
        )

        chunk_iter = chunker.chunk(docling_obj)

        qdrant_client = init_connection()
        chunks_list = []
        metadata_list = []
        ids_list = []
        for index, chunk in enumerate(chunk_iter):
            contextualized_chunk = chunker.contextualize(chunk=chunk)

            if index > 0 and len(chunks_list) > 0:
                prev_chunk_tail = chunks_list[index - 1][-(int(settings.CHUNK_OVERLAP_TOKENS)):]
                new_chunk_head = contextualized_chunk[:int(settings.CHUNK_OVERLAP_TOKENS)]
                chunks_list[index - 1] = chunks_list[index - 1] + " " + new_chunk_head
                contextualized_chunk = prev_chunk_tail + " " + contextualized_chunk

            chunks_list.append(contextualized_chunk)
            # Prepare metadata for the chunk (no chat info)
            metadata = {
                "file_id": file.id,
                "file_name": file.file_name,
                "file_url": file.file.url if file.file else None,
            }
            if knowledge_base:
                metadata["knowledge_base_id"] = knowledge_base.id
            metadata_list.append(metadata)
            ids_list.append(uuid.uuid4().hex)

        # Add to Qdrant
        print(f"Adding {len(chunks_list)} chunks to Qdrant for file {file.id}")
        qdrant_client.add(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            documents=chunks_list,
            metadata=metadata_list,
            ids=ids_list,
        )
        print(f"Qdrant add completed for file {file.id}")

        file.status = COMPLETED
        file.save()

    print("✅ File processing complete.")


@shared_task
def process_chat_uploaded_file(file_ids, chat_id, user_message_id, language_id=None):
    """
    Process chat after files are uploaded and send LLM response.
    First processes files and adds to Qdrant, then sends LLM response.
    """
    chat = Chat.objects.get(id=chat_id)
    user_message = Message.objects.filter(
        id=user_message_id, chat__id=chat_id).first()
    
    channel_layer = get_channel_layer()
    
    # Send loading message at the start of processing
    async_to_sync(channel_layer.group_send)(
        chat.get_room_group_name(),
        {
            'type': 'loading_message',
            'loading': True
        }
    )
    
    try:
        # Get knowledge_base_id from chat if available
        knowledge_base_id = chat.knowledge_base_id if hasattr(chat, 'knowledge_base_id') and chat.knowledge_base_id else None
        
        # First, process the uploaded files and add to Qdrant
        # This ensures files are available for LLM context
        if not isinstance(file_ids, list):
            file_ids = [file_ids]
        
        for file_id in file_ids:
            try:
                file = UploadedFile.objects.get(id=file_id)
            except UploadedFile.DoesNotExist:
                print(f"File with id {file_id} not found, skipping.")
                continue

            print(f"Processing file for chat: {file.file_name}")
            file.status = IN_PROGRESS
            file.save()

            file_process_url = settings.DOCLING_URL + "/v1/convert/file"
            headers = {}
            # Create JSON data for the file processing API
            json_data = {
                "to_formats": ["md", "json"],
                "image_export_mode": "embedded",
                "do_ocr": True,
                "force_ocr": False,
                "ocr_engine": settings.OCR_ENGINE,
                "ocr_lang": settings.OCR_LANG,
                "pdf_backend": "dlparse_v4",
                "table_mode": "accurate",
                "pipeline": "standard",
                "document_timeout": 604800,
                "abort_on_error": False,
                "return_as_file": False,
                "do_table_structure": True,
                "include_images": True,
            }

            # Send the request
            try:
                response = requests.post(
                    url=file_process_url,
                    headers=headers,
                    data=json_data,
                    files={"files": file.file},
                )
            except Exception as e:
                print(f"Error calling Docling service for file {file.id}: {e}")
                file.status = FAILED
                file.save()
                continue

            # Check the response
            print(f"Docling response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Docling returned non-200 for file {file.id}: {response.status_code}")
                file.status = FAILED
                file.save()
                continue

            print("File processed successfully.")
            
            try:
                response_json = response.json()
                docling_json = response_json.get("document", {}).get("json_content")
            except Exception as e:
                print(f"Error parsing Docling response for file {file.id}: {e}")
                file.status = FAILED
                file.save()
                continue

            if not docling_json:
                print(f"No docling json returned for file {file.id}")
                file.status = FAILED
                file.save()
                continue

            # Validate Docling JSON
            try:
                docling_obj: DoclingDocument = DoclingDocument.model_validate(docling_json)
                print("DoclingDocument validation successful!")
            except Exception as e:
                print(f"Error validating DoclingDocument for file {file.id}: {e}")
                file.status = FAILED
                file.save()
                continue

            # Process the Docling JSON data
            file.docling_json = docling_json
            file.save()

            tokenizer = HuggingFaceTokenizer(
                tokenizer=AutoTokenizer.from_pretrained(settings.QDRANT_EMBEDDING_MODEL),
            )
            chunker = HybridChunker(
                tokenizer=tokenizer,
            )

            chunk_iter = chunker.chunk(docling_obj)

            qdrant_client = init_connection()
            chunks_list = []
            metadata_list = []
            ids_list = []
            for index, chunk in enumerate(chunk_iter):
                contextualized_chunk = chunker.contextualize(chunk=chunk)

                if index > 0 and len(chunks_list) > 0:
                    prev_chunk_tail = chunks_list[index - 1][-(int(settings.CHUNK_OVERLAP_TOKENS)):]
                    new_chunk_head = contextualized_chunk[:int(settings.CHUNK_OVERLAP_TOKENS)]
                    chunks_list[index - 1] = chunks_list[index - 1] + " " + new_chunk_head
                    contextualized_chunk = prev_chunk_tail + " " + contextualized_chunk

                chunks_list.append(contextualized_chunk)
                # Prepare metadata for the chunk with chat_id and knowledge_base_id
                metadata = {
                    "chat_id": chat.id,
                    "file_id": file.id,
                    "file_name": file.file_name,
                    "file_url": file.file.url if file.file else None,
                }
                if knowledge_base_id:
                    metadata["knowledge_base_id"] = knowledge_base_id
                metadata_list.append(metadata)
                ids_list.append(uuid.uuid4().hex)

            # Add to Qdrant
            print(f"Adding {len(chunks_list)} chunks to Qdrant for file {file.id}")
            qdrant_client.add(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                documents=chunks_list,
                metadata=metadata_list,
                ids=ids_list,
            )
            print(f"Qdrant add completed for file {file.id}")

            file.status = COMPLETED
            file.save()
        
        # Now handle the LLM response via WebSocket
        # Call the LLM response function
        llm_response = asyncio.run(get_llm_response(chat, user_message, language_id))

        complete_response = {
            'content': llm_response['response'],
            'qdrant_data': llm_response['qdrant_data']
        }

        # Save assistant message with complete JSON structure
        assistant_message = Message.objects.create(
            chat=chat,
            content=json.dumps(complete_response),
            role='assistant'
        )

        # Send assistant message through WebSocket
        async_to_sync(channel_layer.group_send)(
            chat.get_room_group_name(),
            {
                'type': 'chat_message',
                'message': {
                    'id': assistant_message.id,
                    'role': 'assistant',
                    'content': llm_response,
                    'timestamp': assistant_message.created_at.isoformat(),
                    'chat_id': chat.id
                }
            }
        )
        
        print("✅ Chat file processing and LLM response complete.")
        
    except Exception as e:
        print(f"❌ Error processing chat uploaded file: {str(e)}")
        # Send error message to the user via WebSocket
        async_to_sync(channel_layer.group_send)(
            chat.get_room_group_name(),
            {
                'type': 'chat_message',
                'message': {
                    'role': 'assistant',
                    'content': {
                        'response': f'Sorry, there was an error processing your file: {str(e)}',
                        'qdrant_data': []
                    },
                    'chat_id': chat.id
                }
            }
        )
        raise
    finally:
        # Always send loading stop, even if there's an error
        async_to_sync(channel_layer.group_send)(
            chat.get_room_group_name(),
            {
                'type': 'loading_message',
                'loading': False
            }
        )


@shared_task
def process_reviewed_file(file_id):
    """
    Process the reviewed file.
    This is a placeholder function that simulates processing the reviewed file.
    """
    # Simulate some processing
    file = UploadedFile.objects.get(id=file_id)
    print(f"Processing reviewed file: {file.file_name}")
    file.status = POST_REVIEW_PROCESSING
    file.save()

    docling_obj: DoclingDocument = DoclingDocument.model_validate(file.docling_json)
    chunker = HybridChunker()
    chunk_iter = chunker.chunk(docling_obj)

    qdrant_client = init_connection()
    chunks_list = []
    metadata_list = []
    ids_list = []
    for index, chunk in enumerate(chunk_iter):
        contextualized_chunk = chunker.contextualize(chunk=chunk)
        chunks_list.append(contextualized_chunk)
        # Prepare metadata for the chunk
        metadata = {
            "file_id": file.id,
            "file_name": file.file_name,
            "file_url": file.file.url if file.file else None,
        }
        metadata_list.append(metadata)
        ids_list.append(uuid.uuid4().hex)

    # Here you would add logic to process the chunks
    print(f"Adding {len(chunks_list)} chunks to Qdrant")
    qdrant_client.add(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        documents=chunks_list,
        metadata=metadata_list,
        ids=ids_list,
    )
    print(f"Qdrant add completed")

    # Table processing
    tables = docling_obj.tables
    if tables:
        print(f"🔍 FOUND {len(tables)} TABLES in document: {file.file_name}")
        for index, table in enumerate(tables):
            table_name = f"table_{file.id}_{index}_{uuid.uuid4().hex[:8]}"
            df = export_to_dataframe(file.docling_json['tables'][index])
            print(f"\n📊 PROCESSING TABLE {index + 1}/{len(tables)}: {table_name}")
            
            # Extract DataFrame and print its content
            df = export_to_dataframe(file.docling_json["tables"][index])
            
            # Print DataFrame details
            print(f"📋 TABLE SHAPE: {df.shape} (rows: {df.shape[0]}, columns: {df.shape[1]})")
            print(f"📋 TABLE COLUMNS: {list(df.columns)}")
            print(f"📋 TABLE CAPTION: {table.caption_text(doc=docling_obj)}")
            
            # Print first few rows of the DataFrame
            print("📋 TABLE DATA (first 10 rows):")
            print("=" * 100)
            print(df.head(10).to_string(index=True, max_cols=20, max_colwidth=30))
            print("=" * 100)
            
            # Print data types
            print("📋 TABLE DATA TYPES:")
            print(df.dtypes.to_string())
            print("-" * 50)
            
            # Save to SQL database
            df.to_sql(name=table_name, con=settings.SQLALCHEMY_ENGINE)
            print(f"✅ TABLE SAVED TO SQL DATABASE: {table_name}")

            # Save the table mapping to the database
            ExtractedTableMapping.objects.create(
                file=file,
                table_name=table_name,
                caption_text=table.caption_text(doc=docling_obj),
            )
            print(f"✅ TABLE MAPPING SAVED: {table_name}")

            train_vanna.apply_async(table_name=table_name)
            print(f"🚀 VANNA TRAINING STARTED FOR: {table_name}")

    else:
        print("❌ No tables found in the document.")

    # Simulate successful processing
    file.status = COMPLETED
    file.save()
    print("Reviewed file processing complete.")


@shared_task
def process_ai_comments(file_id):
    """
    Process AI comments for the file.
    This is a placeholder function that simulates processing AI comments.
    """
    # Simulate some processing
    file = UploadedFile.objects.get(id=file_id)
    print(f"Processing AI comments for file: {file.file_name}")

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "comments",
            "description": "List of comments to be applied to the document",
            "schema": {
                "type": "object",
                "properties": {
                    "comments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "target_ref": {
                                    "type": "string",
                                    "description": "Reference to the target element in the document",
                                },
                                "source_ref": {
                                    "type": "string",
                                    "description": "Reference to the source element in the document if TABLE_MERGE type",
                                },
                                "suggested_content": {
                                    "type": "string",
                                    "description": "Suggested content to replace or add",
                                },
                                "comment_type": {
                                    "type": "string",
                                    "description": "Type of comment (e.g., EDIT, REMOVE, TABLE_MERGE)",
                                    "enum": ["EDIT", "REMOVE", "TABLE_MERGE"],
                                },
                            },
                            "required": [
                                "target_ref",
                                "suggested_content",
                                "comment_type",
                            ],
                        },
                    }
                },
                "required": ["comments"],
            },
        },
    }
    with open(settings.LLM_PROMPT_FOLDER + "/ai_comments_prompt.json", "r") as prompt_file:
        prompt = json.loads(prompt_file.read())
        messages = prompt.get("messages", [])

    json_data = file.docling_json.copy()
    if not json_data:
        print("No docling JSON data found in the file.")
        return
    json_data.pop("pages", None)  # Remove pages if present
    json_data.pop("origin", None)  # Remove origin if present
    json_data.pop("images", None)  # Remove images if present
    json_data.pop("pictures", None)  # Remove pictures if present
    if "tables" in json_data:
        docling_obj = DoclingDocument.model_validate(file.docling_json)
        tables_markdown = [
            table.export_to_markdown(docling_obj) for table in docling_obj.tables
        ]
        json_data["tables"] = tables_markdown
    if "texts" in json_data:
        docling_obj = DoclingDocument.model_validate(file.docling_json)
        texts_markdown = []
        for text in docling_obj.texts:
            updated_text = {
                "label": text.label,
                "text": text.text,
                "hyperlink": text.hyperlink,
            }
            if getattr(text, "level", None) is not None:
                updated_text["level"] = text.level

            texts_markdown.append(updated_text)

        json_data["texts"] = texts_markdown

    # Add the docling JSON content to the messages
    if messages:
        if messages[-1]["role"] == "user":
            messages[-1]["content"] = messages[-1]["content"].format(
                docling_json=json.dumps(json_data, indent=2)
            )
        else:
            messages.append({
                "role": "user",
                "content": f"Here is the document content to analyze:\n\n{json.dumps(json_data, indent=2)}"
            })
    else:
        messages.append({
            "role": "user",
            "content": f"Here is the document content to analyze:\n\n{json.dumps(json_data, indent=2)}"
        })

    # Send parts of docling JSON to AI for comments
    if settings.AI_COMMENTS_LLM_TYPE == "ollama":
        failure_count = 0
        while failure_count < settings.LLM_MAX_RETRIES:
            try:
                response = completion(
                    model=settings.AI_COMMENTS_LLM_MODEL_NAME,
                    base_url=settings.LLM_API_URL,
                    format="json",
                    response_format=response_format,
                    messages=messages,
                )
                response_json = response.json()
                choices = response_json.get("choices", [{}])
                comments = choices[0].get("text", "").strip()
                # Check structure of comments it should be a a "comments" list
                # First convert to a dictionary
                if isinstance(comments, str):
                    comments = eval(
                        comments
                    )  # Convert string representation to list of dicts
                for comment in comments:
                    target_ref = comment.get("target_ref", "")
                    suggested_content = comment.get("suggested_content", "")
                    source_ref = comment.get("source_ref", "")
                    comment_type = comment.get("comment_type", "EDIT")
                    if not target_ref:
                        if validate_target_ref(file.docling_json, target_ref):
                            failure_count += 1
                            continue
                    if not source_ref:
                        if validate_target_ref(file.docling_json, source_ref):
                            failure_count += 1
                            continue
                    if target_ref and suggested_content:
                        Comment.objects.create(
                            file=file,
                            comment=suggested_content,
                            target_ref=target_ref,
                            source_ref=source_ref,
                            comment_type=comment_type,
                        )
                    break  # Exit loop after processing comments
            except Exception as e:
                print(f"Error in AI completion: {e}")
                failure_count += 1

    elif settings.AI_COMMENTS_LLM_TYPE == "openai":
        failure_count = 0
        while failure_count < settings.LLM_MAX_RETRIES:
            try:
                response = completion(
                    model=settings.AI_COMMENTS_LLM_MODEL_NAME,
                    api_key=settings.AI_COMMENTS_LLM_API_KEY,
                    base_url=settings.AI_COMMENTS_LLM_API_URL,
                    api_version=settings.AI_COMMENTS_LLM_API_VERSION,
                    format="json",
                    response_format=response_format,
                    messages=messages,
                )
                response_json = response.choices[0].message.content
                # Parse the response JSON
                response_json = json.loads(response_json)
                comments = response_json.get("comments", [])
                if not isinstance(comments, list):
                    print("Invalid response format for comments.")
                    failure_count += 1
                    continue
                # Check structure of comments it should be a a "comments" list
                # First convert to a dictionary
                if isinstance(comments, str):
                    comments = eval(
                        comments
                    )  # Convert string representation to list of dicts
                for comment in comments:
                    target_ref = comment.get("target_ref", "")
                    suggested_content = comment.get("suggested_content", "")
                    source_ref = comment.get("source_ref", "")
                    comment_type = comment.get("comment_type", "EDIT")
                    if target_ref and suggested_content:
                        Comment.objects.create(
                            file=file,
                            comment=suggested_content,
                            target_ref=target_ref,
                            source_ref=source_ref,
                            comment_type=comment_type,
                        )
                break
            except Exception as e:
                print(f"Error in AI completion: {e}")
                failure_count += 1
    else:
        # Fallback to legacy configuration for backward compatibility
        if settings.LLM_TYPE == "ollama":
            failure_count = 0
            while failure_count < settings.LLM_MAX_RETRIES:
                try:
                    response = completion(
                        model=settings.LLM_NAME,
                        base_url=settings.LLM_API_URL,
                        format="json",
                        response_format=response_format,
                        messages=messages,
                    )
                    response_json = response.json()
                    choices = response_json.get("choices", [{}])
                    comments = choices[0].get("text", "").strip()
                    # Check structure of comments it should be a a "comments" list
                    # First convert to a dictionary
                    if isinstance(comments, str):
                        comments = eval(
                            comments
                        )  # Convert string representation to list of dicts
                    for comment in comments:
                        target_ref = comment.get("target_ref", "")
                        suggested_content = comment.get("suggested_content", "")
                        source_ref = comment.get("source_ref", "")
                        comment_type = comment.get("comment_type", "EDIT")
                        if not target_ref:
                            if validate_target_ref(file.docling_json, target_ref):
                                failure_count += 1
                                continue
                        if not source_ref:
                            if validate_target_ref(file.docling_json, source_ref):
                                failure_count += 1
                                continue
                        if target_ref and suggested_content:
                            Comment.objects.create(
                                file=file,
                                comment=suggested_content,
                                target_ref=target_ref,
                                source_ref=source_ref,
                                comment_type=comment_type,
                            )
                    break
                except Exception as e:
                    print(f"Error in AI completion: {e}")
                    failure_count += 1

        elif settings.LLM_TYPE == "openai":
            failure_count = 0
            while failure_count < settings.LLM_MAX_RETRIES:
                try:
                    response = completion(
                        model=settings.LLM_NAME,
                        api_key=settings.LLM_API_KEY,
                        base_url=settings.LLM_API_URL,
                        api_version=settings.LLM_API_VERSION,
                        format="json",
                        response_format=response_format,
                        messages=messages,
                    )
                    response_json = response.choices[0].message.content
                    # Parse the response JSON
                    response_json = json.loads(response_json)
                    comments = response_json.get("comments", [])
                    if not isinstance(comments, list):
                        print("Invalid response format for comments.")
                        failure_count += 1
                        continue
                    # Check structure of comments it should be a a "comments" list
                    # First convert to a dictionary
                    if isinstance(comments, str):
                        comments = eval(
                            comments
                        )  # Convert string representation to list of dicts
                    for comment in comments:
                        target_ref = comment.get("target_ref", "")
                        suggested_content = comment.get("suggested_content", "")
                        source_ref = comment.get("source_ref", "")
                        comment_type = comment.get("comment_type", "EDIT")
                        if target_ref and suggested_content:
                            Comment.objects.create(
                                file=file,
                                comment=suggested_content,
                                target_ref=target_ref,
                                source_ref=source_ref,
                                comment_type=comment_type,
                            )
                    break
                except Exception as e:
                    print(f"Error in AI completion: {e}")
                    failure_count += 1

    # Simulate successful processing
    file.save()
    print("AI comments processing complete.")

