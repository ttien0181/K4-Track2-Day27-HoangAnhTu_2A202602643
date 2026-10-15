"""Online checks for the five Data Siege event types."""

from api import Verdict


def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def _result_or_error(result, pillar):
    if "error" in result:
        return Verdict(alert=False, pillar=pillar, reason=result["error"])
    return None


def check_data_batch(payload, ctx):
    profile = ctx.tools.batch_profile(payload["batch_id"])
    error = _result_or_error(profile, "checks")
    if error:
        return error

    baseline = ctx.baseline
    if not baseline["row_count_min"] <= profile["row_count"] <= baseline["row_count_max"]:
        return Verdict(alert=True, pillar="checks", reason="Order volume outside historical range")
    if profile["null_rate"]["customer_id"] > baseline["null_rate_max"]:
        return Verdict(alert=True, pillar="checks", reason="Customer ID null rate is high")
    if not baseline["mean_amount_min"] <= profile["mean_amount"] <= baseline["mean_amount_max"]:
        return Verdict(alert=True, pillar="checks", reason="Order amount mean outside historical range")
    if profile["staleness_min"] > baseline["staleness_min_max"]:
        return Verdict(alert=True, pillar="checks", reason="Order batch is stale")

    # A batch can deviate on several dimensions without crossing any one bound.
    row_mid = (baseline["row_count_min"] + baseline["row_count_max"]) / 2
    row_half_range = (baseline["row_count_max"] - baseline["row_count_min"]) / 2
    amount_mid = (baseline["mean_amount_min"] + baseline["mean_amount_max"]) / 2
    amount_half_range = (baseline["mean_amount_max"] - baseline["mean_amount_min"]) / 2
    row_distance = (profile["row_count"] - row_mid) / row_half_range
    amount_distance = (profile["mean_amount"] - amount_mid) / amount_half_range
    null_distance = profile["null_rate"]["customer_id"] / baseline["null_rate_max"]
    stale_distance = profile["staleness_min"] / baseline["staleness_min_max"]
    combined_distance_squared = (row_distance ** 2 + amount_distance ** 2
                                 + null_distance ** 2 + stale_distance ** 2)
    if combined_distance_squared > 1.3 ** 2:
        return Verdict(alert=True, pillar="checks", reason="Several order quality signals drifted together")
    return Verdict(alert=False, pillar="checks")


def check_contract_checkpoint(payload, ctx):
    diff = ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    error = _result_or_error(diff, "contracts")
    if error:
        return error

    if diff["violations"]:
        return Verdict(alert=True, pillar="contracts", reason="Contract violation: " + ", ".join(diff["violations"]))
    declared_sla = payload.get("declared_sla", {}).get("freshness_min")
    freshness_limit = ctx.baseline["freshness_delay_max_min"]
    if declared_sla is not None:
        freshness_limit = min(freshness_limit, declared_sla)
    if diff["freshness_delay_min"] > freshness_limit:
        return Verdict(alert=True, pillar="contracts", reason="Contract freshness limit exceeded")
    return Verdict(alert=False, pillar="contracts")


def check_lineage_run(payload, ctx):
    graph = ctx.tools.lineage_graph_slice(payload["run_id"])
    error = _result_or_error(graph, "lineage")
    if error:
        return error

    if graph["actual_downstream_count"] == 0:
        return Verdict(alert=True, pillar="lineage", reason="Transform output has no downstream consumer")
    if not {"raw.orders", "raw.customers"}.issubset(graph["actual_upstream"]):
        return Verdict(alert=True, pillar="lineage", reason="Required upstream source is missing")
    if graph["duration_ms"] > ctx.baseline["lineage_duration_ms_max"]:
        return Verdict(alert=True, pillar="lineage", reason="Transform runtime exceeds historical range")
    return Verdict(alert=False, pillar="lineage")


def check_feature_materialization(payload, ctx):
    drift = ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    error = _result_or_error(drift, "ai_infra")
    if error:
        return error

    # The published 3-sigma bound is below the observed clean-stream maximum.
    if drift["mean_shift_sigma"] > 0.65:
        return Verdict(alert=True, pillar="ai_infra", reason="Training-serving feature mean shifted")
    return Verdict(alert=False, pillar="ai_infra")


def check_embedding_batch(payload, ctx):
    drift = ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    error = _result_or_error(drift, "ai_infra")
    if error:
        return error

    if drift["centroid_shift"] > 0.04:
        return Verdict(alert=True, pillar="ai_infra", reason="Embedding centroid drifted")
    if drift["avg_doc_age_days"] > 44.5:
        return Verdict(alert=True, pillar="ai_infra", reason="Document corpus is stale")
    return Verdict(alert=False, pillar="ai_infra")
