import functools
import json
import logging
import os
from pathlib import Path
import zoneinfo
from datetime import datetime
from typing import Literal, Sequence

import pandas as pd
import pydantic
from prometheus_api_client.metric_range_df import MetricRangeDataFrame
import numpy as np
from slurm_mcp.slurm_model import SlurmJob
# from sarc.client.job import SlurmJob as SarcSlurmJob

logger = logging.getLogger(__name__)

PROMETHEUS_URLS: dict[str, str] = {}
""" Dicts from cluster name to the Prometheus URL. """


MTL = zoneinfo.ZoneInfo("America/Montreal")
PST = zoneinfo.ZoneInfo("America/Vancouver")
UTC = zoneinfo.ZoneInfo("UTC")
slurm_job_metric_names = [
    "slurm_job_core_usage",
    "slurm_job_core_usage_total",
    "slurm_job_fp16_gpu",
    "slurm_job_fp32_gpu",
    "slurm_job_fp64_gpu",
    "slurm_job_memory_active_file",
    "slurm_job_memory_cache",
    "slurm_job_memory_inactive_file",
    "slurm_job_memory_limit",
    "slurm_job_memory_mapped_file",
    "slurm_job_memory_max",
    "slurm_job_memory_rss",
    "slurm_job_memory_rss_huge",
    "slurm_job_memory_unevictable",
    "slurm_job_memory_usage",
    "slurm_job_memory_usage_gpu",
    "slurm_job_nvlink_gpu",
    "slurm_job_nvlink_gpu_total",
    "slurm_job_pcie_gpu",
    "slurm_job_pcie_gpu_total",
    "slurm_job_power_gpu",
    "slurm_job_process_count",
    "slurm_job_sm_occupancy_gpu",
    "slurm_job_states",
    "slurm_job_tensor_gpu",
    "slurm_job_threads_count",
    "slurm_job_utilization_gpu",
    "slurm_job_utilization_gpu_memory",
]


class Statistics(pydantic.BaseModel):
    """Statistics for a timeseries."""

    mean: float
    std: float
    q05: float
    q25: float
    median: float
    q75: float
    max: float
    unused: int


class JobStatistics(pydantic.BaseModel):
    """Statistics for a job."""

    gpu_utilization: Statistics | None
    gpu_utilization_fp16: Statistics | None
    gpu_utilization_fp32: Statistics | None
    gpu_utilization_fp64: Statistics | None
    gpu_sm_occupancy: Statistics | None
    gpu_memory: Statistics | None
    gpu_power: Statistics | None

    # BUG: Getting some trouble with these metrics:
    # cpu_utilization: Statistics
    # system_memory: Statistics


class SimpleStatistics(pydantic.BaseModel):
    gpu_util: float
    gpu_sm_util: float


def get_job_gpu_metrics(job: SlurmJob) -> SimpleStatistics | None:
    # sarc_slurm_job = to_sarc_slurm_job(job)
    metrics = get_job_time_series(
        job,
        metric=list(slurm_job_metric_names),
        # metric=["slurm_job_utilization_gpu", "slurm_job_sm_occupancy_gpu"],
        # aggregation="interval",
        # min_interval=60,
        # measure="avg_over_time",
    )
    if metrics is None:
        return None
    stats = metrics.groupby("__name__")["value"].mean().to_dict()
    # TODO: If the job doesn't use GPUs, do we return None? or stats with nans?
    gpu_util = stats.get("slurm_job_utilization_gpu", np.nan) / 100
    gpu_sm_eff = stats.get("slurm_job_sm_occupancy_gpu", np.nan) / 100
    return SimpleStatistics(gpu_util=gpu_util, gpu_sm_util=gpu_sm_eff)


def get_all_compute_metrics_for_job(job: SlurmJob) -> JobStatistics | None:
    # TODO: Finish implementing this.
    # sarc_slurm_job = to_sarc_slurm_job(job)
    metrics = get_job_time_series(
        job,
        metric=list(slurm_job_metric_names),
        # metric=["slurm_job_utilization_gpu", "slurm_job_sm_occupancy_gpu"],
        # aggregation="interval",
        # min_interval=60,
        # measure="avg_over_time",
    )
    if metrics is None:
        return None
    # stats = metrics.groupby("__name__")["value"].mean().to_dict()
    # TODO: If the job doesn't use GPUs, do we return None? or stats with nans?
    # gpu_util = stats.get("slurm_job_utilization_gpu", np.nan) / 100
    # gpu_sm_eff = stats.get("slurm_job_sm_occupancy_gpu", np.nan) / 100
    # return {"gpu_utilization": gpu_util, "gpu_sm_efficiency": gpu_sm_eff}
    # return SimpleStatistics(gpu_util=gpu_util, gpu_sm_util=gpu_sm_eff)
    from sarc.jobs.series import compute_job_statistics_from_dataframe

    statistics_dict = {
        "mean": lambda self: self.mean(),
        "std": lambda self: self.std(),
        "max": lambda self: self.max(),
        "q25": lambda self: self.quantile(0.25),
        "median": lambda self: self.median(),
        "q75": lambda self: self.quantile(0.75),
        "q05": lambda self: self.quantile(0.05),
    }
    metrics_dict = {
        metric: metrics[metrics["__name__"] == metric] for metric in slurm_job_metric_names
    }
    # metrics = {
    #     metric: MetricRangeDataFrame(results)
    #     for metric, results in metric_to_data.items()
    # }
    # compute_job_statistics_from_dataframe(df, )
    gpu_utilization = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_utilization_gpu"],
        statistics=statistics_dict,
        unused_threshold=0.01,
        normalization=lambda x: float(x / 100),
    )

    gpu_utilization_fp16 = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_fp16_gpu"],
        statistics=statistics_dict,
        unused_threshold=0.01,
        normalization=lambda x: float(x / 100),
    )

    gpu_utilization_fp32 = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_fp32_gpu"],
        statistics=statistics_dict,
        unused_threshold=0.01,
        normalization=lambda x: float(x / 100),
    )

    gpu_utilization_fp64 = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_fp64_gpu"],
        statistics=statistics_dict,
        unused_threshold=0.01,
        normalization=lambda x: float(x / 100),
    )

    gpu_sm_occupancy = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_sm_occupancy_gpu"],
        statistics=statistics_dict,
        unused_threshold=0.01,
        normalization=lambda x: float(x / 100),
    )

    gpu_memory = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_utilization_gpu_memory"],
        statistics=statistics_dict,
        normalization=lambda x: float(x / 100),
        unused_threshold=False,
    )

    gpu_power = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_power_gpu"],
        statistics=statistics_dict,
        unused_threshold=False,
    )

    # BUG: Issue with parsing the data from prometheus for cpu utilization.
    _cpu_utilization = compute_job_statistics_from_dataframe(
        metrics_dict["slurm_job_core_usage"],
        statistics=statistics_dict,
        unused_threshold=0.01,
        is_time_counter=True,
    )
    _system_memory = None
    # if job.steps[0].tres.allocated.mem is not None:
    # system_memory = compute_job_statistics_from_dataframe(
    #     metrics_dict["slurm_job_memory_usage"],
    #     statistics=statistics_dict,
    #     normalization=lambda x: float(
    #         x / 1e6 / typing.cast(int, job.allocated.mem)
    #     ),
    #     unused_threshold=False,
    # )
    # elif metrics_dict["slurm_job_memory_usage"] is not None:
    #     logger.warning(
    #         f"job.allocated.mem is None for job {job.job_id} (job status: {job.job_state.value})"
    #     )

    return JobStatistics(
        gpu_utilization=Statistics(**gpu_utilization) if gpu_utilization else None,
        gpu_utilization_fp16=Statistics(**gpu_utilization_fp16) if gpu_utilization_fp16 else None,
        gpu_utilization_fp32=Statistics(**gpu_utilization_fp32) if gpu_utilization_fp32 else None,
        gpu_utilization_fp64=Statistics(**gpu_utilization_fp64) if gpu_utilization_fp64 else None,
        gpu_sm_occupancy=Statistics(**gpu_sm_occupancy) if gpu_sm_occupancy else None,
        gpu_memory=Statistics(**gpu_memory) if gpu_memory else None,
        gpu_power=Statistics(**gpu_power) if gpu_power else None,
        # cpu_utilization=Statistics(**cpu_utilization) if cpu_utilization else None,
        # system_memory=Statistics(**system_memory) if system_memory else None,
    )


# pylint: disable=too-many-branches
def get_job_time_series(
    job: SlurmJob,
    metric: str | Sequence[str],
    min_interval: int = 30,
    max_points: int = 100,
    measure: str | None = None,
    aggregation: Literal["total", "interval"] | None = "total",
) -> pd.DataFrame | None:
    """Fetch job metrics.

    Arguments:
        job: The job for which to fetch metrics.
        metric: The metric or list of metrics, which must be in ``slurm_job_metric_names``.
        min_interval: The minimal reporting interval, in seconds.
        max_points: The maximal number of data points to return.
        measure: The aggregation measure to use ("avg_over_time", etc.)
            A format string can be passed, e.g. ("quantile_over_time(0.5, {})")
            to get the median.
        aggregation: Either "total", to aggregate over the whole range, or
            "interval", to aggregate over each interval.
        dataframe: If True, return a DataFrame. Otherwise, return the list of
            dicts returned by Prometheus's API.
    """
    # results = with_cache(
    #     _get_job_time_series_data,
    #     key=_get_job_time_series_data_cache_key,
    #     subdirectory="prometheus",
    # )(
    results = _get_job_time_series_data(
        job=job,
        metric=metric,
        min_interval=min_interval,
        max_points=max_points,
        measure=measure,
        aggregation=aggregation,
        # cache_policy is None,
        # so that it can be set
        # with env var SARC_CACHE
    )
    return MetricRangeDataFrame(results) if results else None


# pylint: disable=too-many-branches
def _get_job_time_series_data(
    job: SlurmJob,
    metric: str | Sequence[str],
    min_interval: int = 30,
    max_points: int = 100,
    measure: str | None = None,
    aggregation: Literal["total", "interval"] | None = "total",
) -> list:
    """Fetch job metrics.

    Arguments:
        job: The job for which to fetch metrics.
        metric: The metric or list of metrics, which must be in ``slurm_job_metric_names``.
        min_interval: The minimal reporting interval, in seconds.
        max_points: The maximal number of data points to return.
        measure: The aggregation measure to use ("avg_over_time", etc.)
            A format string can be passed, e.g. ("quantile_over_time(0.5, {})")
            to get the median.
        aggregation: Either "total", to aggregate over the whole range, or
            "interval", to aggregate over each interval.
    """
    metrics = [metric] if isinstance(metric, str) else metric
    if not metrics:
        raise ValueError("No metrics given")
    for m in metrics:
        if m not in slurm_job_metric_names:
            raise ValueError(f"Unknown metric name: {m}")
    if aggregation not in ("interval", "total", None):
        raise ValueError(f"Aggregation must be one of ['total', 'interval', None]: {aggregation}")

    if job.state.current[0] != "RUNNING" and not job.elapsed_time:
        return []

    if len(metrics) == 1:
        (prefix,) = metrics
        label_exprs = []
    else:
        prefix = ""
        label_exprs = [f'__name__=~"^({"|".join(metrics)})$"']

    label_exprs.append(f'slurmjobid="{job.job_id}"')
    selector = prefix + "{" + ", ".join(label_exprs) + "}"

    now = datetime.now(tz=UTC).astimezone(MTL)

    if job.start_time is None:
        raise ValueError("Job hasn't started yet")

    ago = now - job.start_time.astimezone(now.tzinfo)
    duration = (job.end_time or now) - job.start_time

    offset = int((ago - duration).total_seconds())
    offset_string = f" offset {offset}s" if offset > 0 else ""

    duration_seconds = int(duration.total_seconds())

    # Duration should not be looking in the future
    if offset < 0:
        duration_seconds += offset

    if duration_seconds <= 0:
        return []

    interval = int(max(duration_seconds / max_points, min_interval))

    query = selector

    if measure and aggregation:
        if aggregation == "interval":
            range_seconds = interval
        elif aggregation == "total":
            range_seconds = duration_seconds
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

        query = f"{query}[{range_seconds}s]"
        if "(" in measure:
            query = measure.format(f"{query} {offset_string}")
        else:
            query = f"{measure}({query} {offset_string})"
        query = f"{query}[{duration_seconds}s:{range_seconds}s]"
    else:
        query = f"{query}[{duration_seconds}s:{interval}s] {offset_string}"

    logger.debug(f"prometheus query with offset: {query}")
    return get_prometheus_client(job.cluster).custom_query(query)


@functools.cache
def get_prometheus_client(cluster: str):
    from prometheus_api_client import PrometheusConnect

    prometheus_url: str
    if f"PROMETHEUS_URL_{cluster.upper()}" in os.environ:
        prometheus_url = os.environ[f"PROMETHEUS_URL_{cluster.upper()}"]
    elif cluster in PROMETHEUS_URLS:
        prometheus_url = PROMETHEUS_URLS[cluster]
    else:
        raise NotImplementedError(f"Prometheus URL is not known for cluster {cluster}!")
    headers = {}
    if (
        prometheus_headers_file := os.environ.get(f"PROMETHEUS_HEADERS_FILE_{cluster.upper()}")
    ) and Path(prometheus_headers_file).exists():
        headers = json.loads(Path(prometheus_headers_file).read_text(encoding="utf-8"))
    return PrometheusConnect(url=prometheus_url, headers=headers)


# UGLY!
# os.environ["SARC_CONFIG"] = str(
#     Path.home() / "repos" / "SARC" / "config" / "sarc-client.yaml"
# )
# from sarc.jobs.series import get_job_time_series

logger = logging.getLogger(__name__)
