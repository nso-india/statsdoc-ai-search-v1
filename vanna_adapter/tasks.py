from celery import shared_task

from .core import init_vanna_adapter


@shared_task
def train_vanna(table_name: str = None):
    vanna_client = init_vanna_adapter()
    if table_name is not None:
        vanna_client.train_on_table(table_name)
    else:
        vanna_client.train_on_db()
    return "Training completed successfully."
