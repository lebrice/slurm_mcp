from datetime import datetime, timedelta


from slurm_mcp.s_mcp import get_job_gpu_compute_stats_fn, get_total_compute_usage_stats_fn


def test_sum_over_period():
    print(
        get_total_compute_usage_stats_fn(
            cluster="mila",
            state=None,
            start=datetime.now() - timedelta(days=7),
            end=datetime.now(),
        )
    )


def test_with_job_ids():
    job_ids = [
        7649171,
        7650320,
        7650346,
        7650400,
        7650465,
        7650563,
        7650828,
        7650860,
        7650965,
        7655610,
        7655926,
        7655998,
        7656119,
        7656334,
        7656427,
        7656570,
        7656572,
        7656733,
        7656735,
        7661805,
        7661813,
        7661856,
        7662316,
        7662469,
        7662470,
        7662621,
        7662647,
        7663216,
        7663219,
        7663220,
        7663221,
        7663222,
        7681085,
        7681404,
        7682600,
        7683080,
        7683082,
        7683098,
        7688094,
        7690116,
        7690969,
        7691725,
        7691753,
        7691767,
        7691776,
        7691917,
        7697234,
        7699086,
        7700703,
        7700821,
        7702475,
        7702991,
        7703070,
        7703079,
        7703080,
        7703083,
        7708017,
        7708019,
        7709011,
        7709012,
        7709589,
        7709590,
        7709674,
        7709681,
        7709682,
        7709683,
        7709692,
        7709694,
        7717572,
        7720790,
        7721930,
        7748920,
        7749325,
        7749333,
        7749341,
        7749353,
        7749354,
        7749358,
        7749359,
        7749361,
        7749363,
        7749365,
        7749385,
        7749774,
        7750882,
        7752116,
    ]
    print(get_job_gpu_compute_stats_fn(cluster="mila", job_ids=job_ids))


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG, handlers=[rich.logging.RichHandler()])
#     test_with_job_ids()
