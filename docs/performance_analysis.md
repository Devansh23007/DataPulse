# DataPulse Performance and Reliability Analysis

## Objective

Measure the execution time of the raw ingestion loader, dbt transformations, dbt tests, and the end-to-end repeat-run workflow.

## Measurements

The benchmark script records execution duration, exit status, and warehouse row counts.

| Stage | Duration | Status |
|---|---|---|
| Raw ingestion | Fill from performance report | Pass |
| dbt transformations | Fill from performance report | Pass |
| dbt tests | Fill from performance report | Pass |
| End-to-end run | Fill from performance report | Pass |

## Replay Validation

Record the before-and-after raw table counts and whether unchanged ingestion batches were skipped.

## Limitations

The repeat-run benchmark measures a pipeline in which unchanged raw batches may be skipped. It should not be presented as the throughput of a fresh full ingestion. Exact throughput requires measuring inserted or processed records during the operation.

## Conclusion

Complete this section after collecting actual results. Describe the measured runtime, any failures encountered, and the observed duplicate replay behavior.