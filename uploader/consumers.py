from channels.generic.websocket import WebsocketConsumer
import json

from .models import UploadedFile, Comment
from .utils import update_data_in_target, update_table_header, target_finder, remove_table_header


class JsonUpdateConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            self.close()
        else:
            self.accept()
            self.send(text_data=json.dumps({"message": "Hello WebSocket!"}))

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            self.send(text_data=json.dumps({"error": "Authentication required"}))
            self.close()
            return

        data = json.loads(text_data)
        file_id = data.get("file_id")
        if not file_id:
            self.send(text_data=json.dumps({"error": "File ID is required"}))
            return

        try:
            uploaded_file = UploadedFile.objects.get(id=file_id)
        except UploadedFile.DoesNotExist:
            self.send(text_data=json.dumps({"error": "File not found"}))
            return

        update_type = data.get("type", "update")
        if update_type == "merge_table":
            source_ref = data.get("source_ref")
            if not source_ref:
                self.send(
                    text_data=json.dumps(
                        {"error": "Source reference is required for merge_table"}
                    )
                )
                return
            target_ref = data.get("target_ref")
            if not target_ref:
                self.send(
                    text_data=json.dumps(
                        {"error": "Target reference is required for merge_table"}
                    )
                )
                return
            docling_json = uploaded_file.docling_json
            if docling_json:
                updated_json = update_table_header(docling_json, target_ref, source_ref)
                uploaded_file.docling_json = updated_json
                uploaded_file.save()

        elif update_type == "update":
            target_ref = data.get("target_ref")
            if target_ref:
                docling_json = uploaded_file.docling_json
                if docling_json:
                    updated_json = update_data_in_target(
                        docling_json, target_ref, data.get("new_data", {})
                    )
                    uploaded_file.docling_json = updated_json
                    uploaded_file.save()

        elif update_type == "comment":
            comment = data.get("comment_id")
            comment_status = data.get("status", "PENDING")
            if not comment:
                self.send(text_data=json.dumps({"error": "Comment is required"}))
                return
            try:
                comment_obj = Comment.objects.get(file=uploaded_file, id=comment)
            except Comment.DoesNotExist:
                self.send(text_data=json.dumps({"error": "Comment not found"}))
                return

            if comment_status == "REJECTED":
                comment_obj.status = "REJECTED"
                comment_obj.save()
                response = {"message": "Comment rejected", "success": True}
                self.send(text_data=json.dumps(response))
                return

            if comment_obj.comment_type == "EDIT":
                existing_content = target_finder(
                    uploaded_file.docling_json, comment_obj.target_ref
                )
                updated_json = update_data_in_target(
                    uploaded_file.docling_json,
                    comment_obj.target_ref,
                    comment_obj.comment,
                )
                uploaded_file.docling_json = updated_json
                uploaded_file.save()
                comment_obj.existing_text = existing_content
                comment_obj.status = "ACCEPTED"
                comment_obj.save()
            elif comment_obj.comment_type == "REMOVE":
                existing_content = target_finder(
                    uploaded_file.docling_json, comment_obj.target_ref
                )
                updated_json = update_data_in_target(
                    uploaded_file.docling_json, comment_obj.target_ref, None
                )
                uploaded_file.docling_json = updated_json
                uploaded_file.save()
                comment_obj.existing_text = existing_content
                comment_obj.status = "ACCEPTED"
                comment_obj.save()
            elif comment_obj.comment_type == "TABLE_MERGE":
                source_ref = comment_obj.source_ref
                target_ref = comment_obj.target_ref
                if source_ref and target_ref:
                    docling_json = uploaded_file.docling_json
                    if docling_json:
                        updated_json = update_table_header(
                            docling_json, target_ref, source_ref
                        )
                        uploaded_file.docling_json = updated_json
                        uploaded_file.save()
                        comment_obj.status = "ACCEPTED"
                        comment_obj.save()

        elif update_type == "comment_undo":
            comment_id = data.get("comment_id")
            if not comment_id:
                self.send(text_data=json.dumps({"error": "Comment ID is required"}))
                return
            try:
                comment_obj = Comment.objects.get(file=uploaded_file, id=comment_id)
                if comment_obj.status == "ACCEPTED":
                    if comment_obj.comment_type == "EDIT":
                        updated_json = update_data_in_target(
                            uploaded_file.docling_json,
                            comment_obj.target_ref,
                            comment_obj.existing_text,
                        )
                        uploaded_file.docling_json = updated_json
                    elif comment_obj.comment_type == "REMOVE":
                        updated_json = update_data_in_target(
                            uploaded_file.docling_json,
                            comment_obj.target_ref,
                            comment_obj.existing_text,
                        )
                        uploaded_file.docling_json = updated_json
                    elif comment_obj.comment_type == "TABLE_MERGE":
                        updated_json = remove_table_header(
                            uploaded_file.docling_json, comment_obj.target_ref
                        )
                        uploaded_file.docling_json = updated_json
                elif comment_obj.status == "REJECTED":
                    comment_obj.status = "PENDING"
                else:
                    self.send(text_data=json.dumps({"error": "Invalid comment status"}))
                    return
                uploaded_file.save()
                comment_obj.save()
            except Comment.DoesNotExist:
                self.send(text_data=json.dumps({"error": "Comment not found"}))
                return

        response = {"message": "Update processed", "success": True}
        self.send(text_data=json.dumps(response))
