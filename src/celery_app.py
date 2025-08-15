from celery import Celery
from main import process_product
import os
from dotenv import load_dotenv  
load_dotenv()

app = Celery("celery_app", 
             broker= os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
             backend= os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"))

@app.task
def task_process_product(product):
    process_product(product)

@app.task
def task_process_batch_products(products):
    for product in products:
        task_process_product.delay(product) 

if __name__ == "__main__":
    app.start()
