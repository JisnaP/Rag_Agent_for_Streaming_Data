
from data_pipeline import ingest_pipeline
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

scheduler = AsyncIOScheduler()
# scheduler.add_job(ingest_pipeline, 'cron', hour=0, minute=0)
# Schedule your fetch_documents job
scheduler.add_job(
    ingest_pipeline, 
    'interval', 
    minutes=1, 
    args=['https://www.federalregister.gov/api/v1/documents.json']
)




async def main():
    scheduler.start()
    await asyncio.Event().wait()  # Keep the script running forever

asyncio.run(main())
