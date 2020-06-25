# Rechunk a cloud Zarr file running Dask with Pywren

import sys

import gcsfs
import zarr
import dask.array as da

from rechunker import api

import pywren_ibm_cloud as pywren

from dask_executor_scheduler import executor_scheduler, PywrenExecutor

if __name__ == '__main__':
    
    args = sys.argv[1:]
    if len(args) != 2:
        print("Usage: python rechunk_cloud_storage_cloud_compute.py <project_id> <bucket>")
        sys.exit(1)

    project_id = args[0]
    bucket = args[1]

    fs = gcsfs.GCSFileSystem(project=project_id)
    source_store = gcsfs.mapping.GCSMap(f"{bucket}/source.zarr", gcs=fs)
    target_store = gcsfs.mapping.GCSMap(f"{bucket}/target.zarr", gcs=fs)
    temp_store = gcsfs.mapping.GCSMap(f"{bucket}/temp.zarr", gcs=fs)

    shape = (4000, 4000)
    source_chunks = (200, 4000)
    dtype = "f4"

    a_source = zarr.ones(shape, chunks=source_chunks, dtype=dtype, store=source_store)

    max_mem = 25_600_000
    target_chunks = (4000, 200)
    delayed = api.rechunk_zarr2zarr_w_dask(
        a_source, target_chunks, max_mem, target_store, temp_store=temp_store
    )

    # Use conda runtime since pip needs a compiler to build zarr numcodecs
    runtime = f"{project_id}/pywren-cloudrun-conda-v37:latest"
    delayed.compute(scheduler=executor_scheduler, executor=PywrenExecutor(pywren.cloudrun_executor(runtime=runtime)), batch_size=10)