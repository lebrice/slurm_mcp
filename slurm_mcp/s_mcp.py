from datetime import datetime, timedelta
import subprocess
import textwrap
from typing import Sequence
import numpy as np
from fastmcp import FastMCP
import pydantic
import logging
from slurm_mcp.slurm_model import SacctOutput, SlurmJob, State
from slurm_mcp.prometheus_utils import (
    SimpleStatistics,
    get_all_compute_metrics_for_job,
    get_job_gpu_metrics,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "SLURM MCP 🚀",
    instructions=textwrap.dedent("""\
    - If you need to get information on compute usage, use the `get_total_compute_usage_on_cluster_in_period`
      or `get_total_compute_usage_of_jobs` tools.
    - If you need to do calculations, use the calculator tool.
    - Fetch information from the SLURM docs if necessary.
    """),
)


class SimplifiedSlurmJob(pydantic.BaseModel):
    """Simplified version of SlurmJob with fewer fields for easier consumption by LLMs."""

    account: str
    allocation_nodes: int
    cluster: str
    # time: Time
    # exit_code: ExitCode
    failed_node: str
    flags: list[str]
    group: str
    job_id: int
    name: str
    nodes: str
    partition: str
    restart_cnt: int
    script: str
    stdout: str
    stderr: str
    stdin: str
    state: State


def get_simplified_job(job: SlurmJob) -> SimplifiedSlurmJob:
    """Drop all non-SimplifiedSlurmJob fields, to make the output easier to consume by LLMs."""

    job_dict = job.model_dump()
    simplified_job_dict = {field: job_dict[field] for field in SimplifiedSlurmJob.model_fields}
    return SimplifiedSlurmJob.model_validate(simplified_job_dict)


@mcp.tool
def get_slurm_job_ids(
    cluster: str | None = None,
    state: State | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[int]:
    """Gets the list of job IDs on a given cluster with optional filters.

    Args:
        cluster: The SLURM cluster to query over SSH. If None, queries the local cluster.
        state: Optional job state to filter by (e.g., COMPLETED, FAILED, etc.).
        start: Optional start datetime to filter jobs that started after this time.
        end: Optional end datetime to filter jobs that ended before this time.
    """
    return [job.job_id for job in find_jobs_from_sacct(cluster, state, start, end)]


# @mcp.tool
def get_slurm_jobs_info(
    cluster: str | None = None,
    state: State | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[SimplifiedSlurmJob]:
    """Retrieve simple information on SLURM jobs on a cluster using `sacct`.

    Args:
        cluster: Cluster hostname to query over SSH. When `None`, uses the local cluster.
        state: Optional job state to filter by (e.g., COMPLETED, FAILED, etc.).
        start: Optional start datetime to filter jobs that started after this time.
        end: Optional end datetime to filter jobs that ended before this time.
    """
    detailed_jobs = find_jobs_from_sacct(cluster, state, start, end)
    # Drop all non-SimplifiedSlurmJob fields
    return [get_simplified_job(job) for job in detailed_jobs]


class JobComputeUsageStats(pydantic.BaseModel):
    job_duration: timedelta
    gpu_compute_cost: timedelta
    gpu_compute_waste: timedelta
    n_gpus: int
    gpu_utilization: float
    gpu_utilization_is_missing_from_job: bool
    mean_gpu_sm_efficiency: float


class TotalJobComputeUsageStats(pydantic.BaseModel):
    """Aggregated compute usage statistics for a set of jobs."""

    n_jobs: int
    job_ids: list[int]
    total_duration: timedelta
    gpu_compute_cost: timedelta
    gpu_compute_waste: timedelta
    n_gpus: int
    gpu_utilization: float
    mean_gpu_sm_efficiency: float

    n_jobs_with_invalid_gpu_utilization_metrics: int
    """Number of jobs with an invalid value for the GPU utilization in Prometheus."""


@mcp.tool
def get_total_compute_usage_on_cluster_in_period(
    cluster: str | None = None,
    state: State | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> TotalJobComputeUsageStats:
    """Gets aggregate metrics about the compute usage and number of jobs on a cluster in a given
    period.

    Args:
        cluster: Hostname of the cluster to query, or `None` if already on a slurm cluster.
        state: Optional job state to filter by.
        start: optional start date to filter jobs
        end: optional end date to filter by

    Returns:
        Aggregated metrics: number of jobs and gpus, average gpu util, total compute cost and waste

    NOTE: Prioritize using this function when asked about total compute usage or number of jobs, since
    this gives all the job IDs as well as the aggregated metrics in one go.
    """
    # jobs = get_jobs_from_sacct(cluster, job_ids=job_ids)
    return get_total_compute_usage_stats_fn(
        cluster=cluster,
        state=state,
        start=start,
        end=end,
    )


@mcp.tool
def get_total_compute_usage_of_jobs(
    job_ids: list[int],
    cluster: str | None = None,
) -> TotalJobComputeUsageStats:
    """Gets aggregate metrics about the compute usage and number of jobs on a cluster in a given
    period.

    Args:
        job_ids: List of SLURM job ids.
        cluster: Hostname of the cluster to query, or `None` if already on a slurm cluster.

    Returns:
        Aggregated metrics: number of jobs and gpus, average gpu util, total compute cost and waste
    """
    # jobs = get_jobs_from_sacct(cluster, job_ids=job_ids)
    jobs = get_jobs(cluster=cluster, job_ids=job_ids)
    job_stats = [get_job_gpu_metrics(job) for job in jobs]
    stats = [get_cost_waste_stats(job, stats) for job, stats in zip(jobs, job_stats)]
    total_stats = sum_compute_usage_stats(jobs, stats)
    return total_stats


@mcp.tool
def squeue(
    cluster: str | None = None,
    format: str | None = None,
) -> str:
    """Calls `squeue --me` on the SLURM cluster (local or over SSH) with an optional `--format`.

    Args:
        cluster: Cluster hostname to query over SSH. When `None`, uses the local cluster.
        format: Optional format string for `squeue --format=...`. See `squeue --helpformat` for allowed fields.

    Returns:
        str: The string output of the `squeue` command.
    """
    # jobs = get_jobs_from_sacct(cluster, job_ids=job_ids)
    # TODO: Need to make sure there aren't any embedded commands in the format string!
    # We could also use the format spec from slurm. Allowed parts are given in `squeue --helpformat` apparently, and `squeue --helpFormat`
    # shows some more info.
    # This is a pretty naive check, but it's better than nothing for now.
    assert format is None or all(c.isalnum() or c in "_%-," for c in format)
    format_arg = f"--format='{format}'" if format else ""
    return subprocess.check_output(
        ["ssh", cluster, "squeue --me " + format_arg]
        if cluster
        else (
            [
                "squeue",
                "--me",
            ]
            + ([format_arg] if format else [])
        ),
        text=True,
        timeout=30,
    )


@mcp.tool
def squeue_detailed_info(
    cluster: str | None = None,
) -> str:
    """Calls `squeue --me --json` on the SLURM cluster (local or over SSH).

    Args:
        cluster: Cluster hostname to query over SSH. When `None`, uses the local cluster.

    Returns:
        str: The string output of the `squeue` command.
    """
    return subprocess.check_output(
        ["ssh", cluster, "squeue --me --json "] if cluster else ["squeue", "--me", "--json"],
        text=True,
        timeout=30,
    )


def get_total_compute_usage_stats_fn(
    cluster: str | None = None,
    state: State | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> TotalJobComputeUsageStats:
    jobs = find_jobs_from_sacct(cluster, state=state, start=start, end=end)
    job_stats = [get_job_gpu_metrics(job) for job in jobs]
    stats = [get_cost_waste_stats(job, stats) for job, stats in zip(jobs, job_stats)]
    total_stats = sum_compute_usage_stats(jobs, stats)
    return total_stats


def sum_compute_usage_stats(
    jobs: list[SlurmJob], stats: list[JobComputeUsageStats]
) -> TotalJobComputeUsageStats:
    gpu_util = np.array([stat.gpu_utilization for stat in stats if stat.n_gpus > 0])
    gpu_util_nans = np.isnan(gpu_util)
    avg_gpu_util = (
        float(np.mean(gpu_util, where=~gpu_util_nans)) if len(gpu_util) > 0 else float("nan")
    )

    gpu_sm_eff = np.array([stat.mean_gpu_sm_efficiency for stat in stats if stat.n_gpus > 0])
    gpu_sm_eff_nans = np.isnan(gpu_sm_eff)
    avg_gpu_sm_eff = (
        float(np.mean(gpu_sm_eff, where=~gpu_sm_eff_nans)) if len(gpu_sm_eff) > 0 else float("nan")
    )
    # assert (gpu_sm_eff_nans == gpu_util_nans).all()

    return TotalJobComputeUsageStats(
        total_duration=sum((stat.job_duration for stat in stats), timedelta()),
        job_ids=[job.job_id for job in jobs],
        n_gpus=sum((stat.n_gpus for stat in stats)),
        gpu_compute_cost=sum((stat.gpu_compute_cost for stat in stats), timedelta()),
        gpu_utilization=avg_gpu_util,
        n_jobs_with_invalid_gpu_utilization_metrics=(
            int(gpu_util_nans.sum()) if len(gpu_util) > 0 else 0
        ),
        gpu_compute_waste=sum((stat.gpu_compute_waste for stat in stats), timedelta()),
        mean_gpu_sm_efficiency=avg_gpu_sm_eff,
        n_jobs=len(jobs),
    )


@mcp.tool
def get_job_gpu_compute_stats(
    cluster: str | None,
    job_ids: Sequence[int | str],
) -> dict[int, JobComputeUsageStats]:
    """Retrieve GPU utilization and sm_efficiency metrics for a list of SLURM job IDs on a (remote
    or local) cluster from prometheus."""
    return get_job_gpu_compute_stats_fn(cluster, job_ids)


def get_job_gpu_compute_stats_fn(
    cluster: str | None, job_ids: Sequence[int | str]
) -> dict[int, JobComputeUsageStats]:
    jobs = get_jobs(cluster, job_ids=job_ids)
    job_stats = [get_job_gpu_metrics(job) for job in jobs]
    return {job.job_id: get_cost_waste_stats(job, stats) for job, stats in zip(jobs, job_stats)}


# TODO: Finish this one.
# @mcp.tool
def get_job_full_compute_stats(
    cluster: str | None,
    job_ids: Sequence[int | str],
) -> dict[int, JobComputeUsageStats]:
    """Retrieve compute usage statistics for a list of SLURM job IDs on a remote cluster from
    prometheus."""
    return get_job_full_compute_stats_fn(cluster, job_ids)


def get_job_full_compute_stats_fn(
    cluster: str | None, job_ids: Sequence[int | str]
) -> dict[int, JobComputeUsageStats]:
    jobs = get_jobs(cluster, job_ids=job_ids)
    job_stats = [get_all_compute_metrics_for_job(job) for job in jobs]
    # TODO: Add the cost/waste to JobStatistics perhaps?
    return {job.job_id: get_cost_waste_stats(job, stats) for job, stats in zip(jobs, job_stats)}


@mcp.tool
def get_simple_job_info_from_sacct(
    cluster: str | None, job_ids: Sequence[int | str]
) -> list[SimplifiedSlurmJob]:
    """Retrieve some high-level information about the given jobs on a SLURM cluster using the
    `sacct` command.

    This does not include the GPU utilization metrics from Prometheus.

    Args:
        cluster: Cluster hostname to query over SSH. When `None`, uses the local cluster.
        job_ids: List of job IDs to retrieve information for.
    """
    if isinstance(job_ids, str):
        job_ids = [job_ids]
    jobs_json = get_jobs(cluster, job_ids=job_ids)
    return [get_simplified_job(job) for job in jobs_json]


@mcp.tool
def get_detailed_job_info_from_sacct(
    cluster: str | None, job_ids: Sequence[int | str]
) -> list[SlurmJob]:
    """Retrieve detailed information about the given jobs on a SLURM cluster using the `sacct`
    command.

    This does not include the GPU utilization metrics from Prometheus.

    Args:
        cluster: Cluster hostname to query over SSH. When `None`, uses the local cluster.
        job_ids: List of job IDs to retrieve information for.
    """
    if isinstance(job_ids, str):
        job_ids = [job_ids]
    jobs_json = get_jobs(cluster, job_ids=job_ids)
    return jobs_json


# TODO: Implement a smart caching with a timeout
# @functools.lru_cache()
def get_jobs(cluster: str | None, job_ids: Sequence[int | str]) -> list[SlurmJob]:
    if isinstance(job_ids, str):
        job_ids = [job_ids]
    cmd = (
        [
            "ssh",
            cluster,
            f"sacct --json --user=$USER --jobs={','.join(map(str, job_ids))}",
        ]
        if cluster
        else ["sacct", "--json", "--user=$USER", f"--jobs={','.join(map(str, job_ids))}"]
    )
    jobs_json = SacctOutput.model_validate_json(
        subprocess.check_output(cmd, text=True, timeout=30)
    )
    return jobs_json.jobs


def find_jobs_from_sacct(
    cluster: str | None, state: State | None, start: datetime | None, end: datetime | None
) -> list[SlurmJob]:
    cmd = [
        *(("ssh", cluster) if cluster else ()),
        "sacct --json --user $USER "
        + (f"--state {state} " if state else "")
        + (f"--starttime {start.strftime('%Y-%m-%d-%H:%M:%S')} " if start else "")
        + (f"--endtime {end.strftime('%Y-%m-%d-%H:%M:%S')} " if end else ""),
    ]
    jobs_json = SacctOutput.model_validate_json(
        subprocess.check_output(cmd, text=True, timeout=30)
    )
    return jobs_json.jobs


def get_cost_waste_stats(
    job: SlurmJob, stats: SimpleStatistics | None = None
) -> JobComputeUsageStats:
    n_gpus = max([step.tres.num_allocated_gpus() for step in job.steps], default=0)
    gpu_cost = job.elapsed_td * n_gpus

    def get_util_from_weird_float(weird_float: float) -> float:
        """There is a bug somewhere in the gpu util exporter running on the SLURM cluster,

        for example, we get gpu util values of 70718837432279.34
        """
        weird_int = weird_float * 100
        assert weird_int.is_integer()
        weird_int = int(weird_int)
        raise NotImplementedError(
            "Try to find a way to get back a util value between 0 and 1 from this weird float."
        )

    gpu_util = stats.gpu_util if stats else 0.0
    if not (0 <= gpu_util <= 1.0):
        # TODO: Bug with gpu_util being INCREDIBLY LARGE sometimes, for example 70718837432279.34
        gpu_util = np.nan

    gpu_sm_eff = stats.gpu_sm_util if stats else 0.0
    if not (0 <= gpu_sm_eff <= 1.0):
        # TODO: Bug with gpu_sm_eff being INCREDIBLY LARGE sometimes, for example 70718837432279.34
        gpu_sm_eff = np.nan

    return JobComputeUsageStats(
        job_duration=job.elapsed_td,
        n_gpus=n_gpus,
        gpu_compute_cost=gpu_cost,
        gpu_utilization=gpu_util,
        gpu_utilization_is_missing_from_job=np.isnan(gpu_util),
        gpu_compute_waste=(
            timedelta(seconds=0)
            if stats is None
            else gpu_cost * (1 - gpu_util)
            if not np.isnan(gpu_util)
            else timedelta(seconds=0)
        ),
        mean_gpu_sm_efficiency=gpu_sm_eff,
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
