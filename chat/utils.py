import asyncio
import io
import json
from litellm import completion
from django.conf import settings
from channels.db import database_sync_to_async
from qdrant_adapter.qdrant_adapter import init_connection
from vanna_adapter.core import init_vanna_adapter
from vanna_adapter.utils import extract_file_ids_from_documents, get_table_names_from_file_ids


def get_vanna_data(prompt):
    documents_data = []
    table_names = []
    try:
        qdrant_client = init_connection()
        print(f"Querying Qdrant for data")
        documents = qdrant_client.query(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_text=prompt,
            limit=min(100, settings.QDRANT_QUERY_LIMIT * 10),
        )
        print(f"Qdrant returned {len(documents) if documents else 0} documents")

        if documents:
            documents_data = [item.model_dump() for item in documents]
            file_ids = extract_file_ids_from_documents(documents_data)
            table_names = get_table_names_from_file_ids(file_ids)
    except Exception:
        pass

    vn = init_vanna_adapter(table_names=table_names)

    vn_response = vn.ask(prompt, allow_llm_to_see_data=True)
    if not vn_response:
        return {}

    text, df, fig = vn_response
    if df is not None:
        df = df.to_markdown()
    if fig is not None:
        buf = io.StringIO()
        fig.write_html(buf)
        buf.seek(0)
        figure = fig.to_json()
    else:
        figure = None

    return {
        "text": text,
        "dataframe": df,
        "figure": figure,
        "table_names_identified": table_names,
        "documents_relevance": documents_data,
    }


def get_qdrant_data(prompt, chat_id, kb_id=None):
    try:
        qdrant_client = init_connection()
        print(f"Querying Qdrant for chat data - chat_id: {chat_id}, kb_id: {kb_id}")
        
        # Build query filter based on available IDs
        filter_conditions = []
        if chat_id:
            filter_conditions.append({"key": "chat_id", "match": {"value": chat_id}})
        if kb_id:
            filter_conditions.append({"key": "knowledge_base_id", "match": {"value": kb_id}})
        
        query_filter = {"should": filter_conditions} if filter_conditions else None
        print(f"Query filter: {query_filter}")
        
        documents = qdrant_client.query(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_text=prompt,
            limit=settings.QDRANT_QUERY_LIMIT,
            query_filter=query_filter,
        )
        print(f"Qdrant returned {len(documents) if documents else 0} documents for chat")
        print("******************Qdrant document**************************", documents)
        print("******************End Qdrant document**************************")

    except Exception as e:
        print(f"Error querying Qdrant: {e}")
        documents = []

    return {
        'context': "\n\n".join([doc.document for doc in documents]) if documents else "",
        'citations': [
            {
                'document_name': doc.metadata.get('file_name', 'Unknown Document'),
                'document_link': doc.metadata.get('file_url', None),
                'content': doc.document
            }
            for doc in documents
        ] if documents else []
    }


@database_sync_to_async
def get_chat_messages(chat):
    return list(chat.messages.all())


async def get_llm_response(chat, user_message, language_id=None):
    try:
        # Get kb_id from chat if it has a knowledge_base
        kb_id = chat.knowledge_base_id if hasattr(chat, 'knowledge_base_id') and chat.knowledge_base_id else None
        print(f"Chat ID: {chat.id}, KB ID from chat: {kb_id}, Language ID: {language_id}")
        
        # Get LLM response
        qdrant_data = get_qdrant_data(user_message.content, chat.id, kb_id)
        

        # Get chat history
        messages = await get_chat_messages(chat)

        # Prepare messages for LLM
        with open(settings.LLM_PROMPT_FOLDER + "/user_chat_prompt.json", "r") as prompt_file:
            prompt = json.loads(prompt_file.read())
        llm_messages = [
            {
                "user": "system",
                "content": prompt.get("system_message", "")
            }
        ]
        for msg in messages:
            llm_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Prepare format data with context and language
        format_data = {**qdrant_data}
        
        # Add language to format data if language_id is provided
        if language_id:
            try:
                from chat.models import Language
                language = await asyncio.to_thread(Language.objects.get, id=language_id, is_active=True)
                format_data['language'] = language.name
                print(f"Using language: {language.name}")
            except Language.DoesNotExist:
                print(f"Language with ID {language_id} not found, using default (English)")
                format_data['language'] = "English"
            except Exception as e:
                print(f"Error fetching language: {e}, using default (English)")
                format_data['language'] = "English"
        else:
            format_data['language'] = "English"
        
        # Format the user_message with both context and language
        llm_messages[-1]["content"] += prompt.get("user_message", "\n\nContext: {context}").format(**format_data)
        
        print("******************LLM Messages**************************", llm_messages)
        print("******************End LLM Messages**************************")
        # Use your LiteLLM endpoint
        response = await asyncio.to_thread(
            completion,
            model=settings.AI_COMMENTS_LLM_MODEL_NAME,
            api_key=settings.AI_COMMENTS_LLM_API_KEY,
            base_url=settings.AI_COMMENTS_LLM_API_URL,
            api_version=settings.AI_COMMENTS_LLM_API_VERSION,
            messages=llm_messages,
        )

        return {
            "response": response.choices[0].message['content'] if response and response.choices else "I'm sorry, I couldn't generate a response.",
            "qdrant_data": qdrant_data,
        }

    except Exception as e:
        return f"Sorry, I encountered an error while processing your request: {str(e)}"
