import asyncio
import os
from trainml import TrainML

trainml_client = TrainML()


async def create_job(build_serial):
    print(build_serial)
    job = await trainml_client.jobs.create(
        name=f"Git Automated Training - {build_serial}",
        type="training",
        gpu_type="RTX 2080 Ti",
        gpu_count=1,
        disk_size=10,
        worker_commands=[
            f"git checkout {build_serial} && python main.py --epochs 2 --batch-size 64 --arch resnet50 $TRAINML_DATA_PATH 2>&1 | tee train.log"
        ],
        data=dict(
            datasets=[dict(id="ImageNet", type="public")],
            output_type="trainml",
        ),
        model=dict(
            source_type="git",
            source_uri=f"https://github.com/{os.environ.get('GITHUB_REPOSITORY')}.git",
        ),
    )

    return job


if __name__ == "__main__":
    job = asyncio.run(create_job(os.environ.get("GITHUB_SHA")))

    ## Job information should be saved in a persistent datastore to pull for status and verify completion
    print(job)