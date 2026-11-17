package securepipeline.gate

import rego.v1

default allow := false

required := {
    "critical",
    "high",
    "medium",
    "secrets",
    "coverage",
    "internet_exposed",
    "dast_high",
}

valid_metrics if {
    every key in {"critical", "high", "medium", "secrets", "dast_high"} {
        is_number(input[key])
        input[key] >= 0
        input[key] == floor(input[key])
    }

    is_number(input.coverage)
    input.coverage >= 0
    input.coverage <= 100

    is_boolean(input.internet_exposed)
}

deny contains "Faltan metricas obligatorias" if {
    count(required - object.keys(input)) > 0
}

deny contains "Las metricas tienen valores invalidos" if {
    not valid_metrics
}

deny contains "No se permiten hallazgos Critical" if {
    input.critical > 0
}

deny contains "Se permiten como maximo dos hallazgos High" if {
    input.high > 2
}

deny contains "Se permiten como maximo veinte hallazgos Medium" if {
    input.medium > 20
}

deny contains "No se permiten secretos detectados" if {
    input.secrets > 0
}

deny contains "La cobertura minima requerida es 80%" if {
    input.coverage < 80
}

deny contains "Servicio expuesto a Internet: High debe ser cero" if {
    input.internet_exposed
    input.high > 0
}

deny contains "DAST no permite hallazgos High" if {
    input.dast_high > 0
}

allow if {
    count(deny) == 0
}
