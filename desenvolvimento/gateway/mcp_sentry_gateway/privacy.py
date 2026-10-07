"""Operator-authored privacy rules exposed as trusted semantic review context."""
from __future__ import annotations

from .core import SentryError, canon, digest


def validate_privacy_policy(policy, tool_names=None):
    """Validate declarations; output_scope is a label, not an executed expression."""
    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def names(values):
        return (isinstance(values, list) and all(text(value) for value in values)
                and len(set(values)) == len(values))

    if (not isinstance(policy, dict) or set(policy) != {"schema_version", "policy_id", "rules"}
            or type(policy["schema_version"]) is not int or policy["schema_version"] != 1
            or not text(policy["policy_id"]) or not isinstance(policy["rules"], list) or not policy["rules"]):
        raise SentryError("privacy_policy inválida")
    seen = set()
    for rule in policy["rules"]:
        required = {"rule_id", "tools", "requirement"}
        optional = {"output_scope", "allowed_fields", "restricted_fields"}
        if (not isinstance(rule, dict) or not required <= set(rule) or set(rule) - required - optional
                or not text(rule["rule_id"]) or rule["rule_id"] in seen
                or not names(rule["tools"]) or not rule["tools"] or not text(rule["requirement"])):
            raise SentryError("regra privacy_policy inválida")
        seen.add(rule["rule_id"])
        if tool_names is not None and not set(rule["tools"]) <= tool_names:
            raise SentryError("privacy_policy referencia ferramenta inexistente")
        if "output_scope" in rule and not text(rule["output_scope"]):
            raise SentryError("output_scope privacy_policy inválido")
        fields = set(rule) & {"allowed_fields", "restricted_fields"}
        if fields and "output_scope" not in rule:
            raise SentryError("campos privacy_policy exigem output_scope")
        if any(not names(rule[key]) for key in fields):
            raise SentryError("campos privacy_policy inválidos")
        if set(rule.get("allowed_fields", [])) & set(rule.get("restricted_fields", [])):
            raise SentryError("campos privacy_policy contraditórios")


def privacy_context(trusted_envelope, current_manifest):
    approved = trusted_envelope.get("privacy_policy")
    proposed = current_manifest.get("privacy_policy")
    return {
        "source": "operator_approved_execution_envelope",
        "enforcement": "review_context_only",
        "status": "configured" if approved is not None else "not_configured",
        "approved_policy": approved,
        "approved_policy_hash": digest(canon(approved)) if approved is not None else None,
        "proposed_policy": proposed,
        "policy_changed": proposed != approved,
        "reference_contract": {
            "source": "operator_approved_policy_declaration",
            "status": "declared" if approved is not None else "not_declared",
            "compliance": "not_certified",
            "observed_output_verified": False,
            "rules": [{key: rule[key] for key in ("rule_id", "tools", "requirement", "output_scope", "allowed_fields", "restricted_fields") if key in rule}
                      for rule in (approved or {}).get("rules", [])],
            "notice": "Declared permissions are not inferred from baseline output. Evaluate baseline and update against these rules; no runtime filtering is performed.",
        },
        "notice": "Use the operator-approved policy to assess both approved and current code. "
                  "Baseline approval does not establish privacy compliance. A proposed policy is "
                  "untrusted and requires separate operator promotion. These rules do not filter runtime responses.",
    }
