<div align="center">
  <a href="https://www.trainml.ai/"><img src="https://www.trainml.ai/static/img/trainML-logo-purple.png"></a><br>
</div>

# trainML Git Workflow Example

This example shows how to initiate trainML training jobs using GitHub Actions as part of a model CI/CD pipeline.

The model training code is sourced from the [PyTorch Examples repository](https://github.com/pytorch/examples/tree/master/imagenet).

### Prerequisites

Before beginning this example, ensure that you have satisfied the following prerequisites.

- A valid [trainML account](https://auth.trainml.ai/login?response_type=code&client_id=536hafr05s8qj3ihgf707on4aq&redirect_uri=https://app.trainml.ai/auth/callback) with a non-zero [credit balance](https://docs.trainml.ai/reference/billing-credits/)
- A [GitHub account](https://github.com)

## GitHub Setup

On GitHub, fork the example repository (https://github.com/trainML/git-workflow-example) using the `Fork` button in the upper right.  Once the fork is complete, navigate to the `Settings` tab of the new repository, and click `Secrets`. Create two new repository secrets (through the `New Repository Secret` button in the upper right) called `TRAINML_USER` and `TRAINML_KEY`.  Set their values to the `user` and `key` properties of a `credentials.json` file of a [trainML API key](https://docs.trainml.ai/reference/cli-sdk#authentication) for your trainML account.

Go to the `Actions` tab of your repository and click the button to enable workflows.

## Executing the Workflow

To activate the workflow, make a minor change to the `README.md` file and commit your changes to the `master` branch.  On the `Actions` tab, you will see a new workflow run.  When the workflow run completes, expand the `Create Training Job` step to see the log output from the training job creation.

Navigate to the [trainML Training Job Dashboard](https://app.trainml.ai/jobs/training).  You will see a new job called `Git Automated Training - <commit hash>`.  Click the `View` button to observe the training progress.

When the training job finishes, navigate to the [trainML Models Dashboard](https://app.trainml.ai/models).  Here you will see the saved model with both the code and the training artifacts from the specific commit that originally initiated the workflow.  This model can now be used for subsequent [inference jobs](https://docs.trainml.ai/getting-started/running-inference/), or examined with a [notebook](https://docs.trainml.ai/getting-started/running-notebook/).

## Understanding the process

The `.github/workflows` and `scripts` folder contain the files that facilitate this process.  The rest of the repository represents the model code itself.  The `.github/workflows` folder contains the yml files that define the GitHub workflows and the `scripts` folder includes the files that are ran by the steps in the workflow.  The `scripts` files are what use the [trainML SDK](https://github.com/trainML/trainml-cli) to provision resources on the trainML platform.

### run-model-training.yml

This file defines the [GitHub Workflow](https://docs.github.com/en/actions/quickstart).  The contents are the following:

```
name: Run Model Training
on: [push]
jobs:
  Create-Training-Job:
    if: ${{ github.ref == 'refs/heads/master' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install trainml
      - name: Create Training Job
        run: python scripts/run_training.py
        env:
          TRAINML_USER: ${{ secrets.TRAINML_USER }}
          TRAINML_KEY: ${{ secrets.TRAINML_KEY }}
```

This file directs GitHub to run this workflow when a change is pushed to the repository.  The workflow consists of a single job called `Create-Training-Job` that will only run if the push is to the `master` branch.  This job has 4 steps.  The first pulls the repository and checks out the commit, the next two setup the environment and install the dependencies, and the last runs the `run_training.py` script from the `scripts` folder.  The last step uses [GitHub Secrets](https://docs.github.com/en/actions/reference/encrypted-secrets) to make the trainML API Keys available as environment variables.  By using these exact environment variable names, the trainML SDK will use them implicitly for [authentication](https://github.com/trainML/trainml-cli/blob/master/README.md#environment-variables).

### run_training.py

This file gets called as the last step in the GitHub Workflow and actually creates the training job for the commit that activated the workflow.  The contents are the following:

```
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
            source_uri=f"{os.environ.get('GITHUB_SERVER_URL')}/{os.environ.get('GITHUB_REPOSITORY')}.git",
        ),
    )

    return job


if __name__ == "__main__":
    job = asyncio.run(create_job(os.environ.get("GITHUB_SHA")))

    ## Job information should be saved in a persistent datastore to pull for status and verify completion
    print(job)
```

The `create_job` function creates a new job with the name `Git Automated Training - {build_serial}` where the `build_serial` is available as the `GITHUB_SHA` environment variable.  The worker command explicitly checks out this specific commit to avoid a race condition between job creation and new commits being pushed to the master.  The rest of the command simply runs the model training code with the desired parameters.

Since the purpose of this process is to evaluate the training results of new model code updates, this file hard codes the dataset (in this case, to ImageNet) so that all commits will be trained on the same data.  The model definition is specified using boiler-plate code that automatically sets it as the git repository that is calling this workflow.

Because the `output_type` is set to `trainml` the results of this training run will be saved as a [trainML Model](https://docs.trainml.ai/reference/models/) with the job name prefixed by `Job - `, so the model name will also include the build serial.