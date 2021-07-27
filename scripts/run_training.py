import asyncio
import os
from trainml import TrainML

trainml_client = TrainML()

async def create_job(build_serial):
    print(build_serial)
    jobs = await trainml_client.jobs.list()
    print(jobs)


if __name__ == '__main__':
    asyncio.run(create_job(os.environ.get("GITHUB_SHA")))