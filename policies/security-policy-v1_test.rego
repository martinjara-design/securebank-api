package securepipeline.gate

import rego.v1

valid_input := {
    "critical": 0,
    "high": 0,
    "medium": 2,
    "secrets": 0,
    "coverage": 85,
    "internet_exposed": true,
    "dast_high": 0,
}

test_allow_valid_build if {
    allow with input as valid_input
}

test_block_critical if {
    not allow with input as object.union(
        valid_input,
        {"critical": 1},
    )
}

test_block_secrets if {
    not allow with input as object.union(
        valid_input,
        {"secrets": 1},
    )
}

test_block_low_coverage if {
    not allow with input as object.union(
        valid_input,
        {"coverage": 79},
    )
}

test_allow_coverage_at_threshold if {
    allow with input as object.union(
        valid_input,
        {"coverage": 80},
    )
}

test_block_high_when_exposed if {
    not allow with input as object.union(
        valid_input,
        {"high": 1},
    )
}

test_allow_two_high_when_internal if {
    allow with input as object.union(
        valid_input,
        {"high": 2, "internet_exposed": false},
    )
}

test_block_more_than_two_high if {
    not allow with input as object.union(
        valid_input,
        {"high": 3, "internet_exposed": false},
    )
}

test_allow_twenty_medium if {
    allow with input as object.union(
        valid_input,
        {"medium": 20},
    )
}

test_block_more_than_twenty_medium if {
    not allow with input as object.union(
        valid_input,
        {"medium": 21},
    )
}

test_block_dast_high if {
    not allow with input as object.union(
        valid_input,
        {"dast_high": 1},
    )
}

test_block_missing_metrics if {
    not allow with input as {}
}

test_block_invalid_type if {
    not allow with input as object.union(
        valid_input,
        {"coverage": "85"},
    )
}

test_block_negative_count if {
    not allow with input as object.union(
        valid_input,
        {"high": -1},
    )
}
