"""El gate no debe promover errores, excepciones vencidas ni severidades altas."""
import pytest
from scripts.iac_gate import evaluate


def inputs():
    report = {
        'summary': {'passed': 9, 'failed': 1, 'skipped': 0,
                    'parsing_errors': 0, 'resource_count': 1},
        'results': {'passed_checks': [{}] * 9, 'skipped_checks': [],
                    'failed_checks': [{'check_id': 'CKV_AWS_145', 'resource': 'aws_s3_bucket.logs'}]},
    }
    policy = {
        'scope': 'aws-lab', 'minimum_score': 85, 'maximum_skipped_checks': 0,
        'exceptions': [{'check_id': 'CKV_AWS_145', 'resource': 'aws_s3_bucket.logs',
                        'reason': 'Destino de acceso S3 requiere SSE-S3.',
                        'expires': '2099-01-01', 'contextual_severity': 'MEDIUM'}],
    }
    return report, policy


def test_medium_justificado_permite_sin_ocultar_fallo():
    report, policy = inputs()
    decision = evaluate(report, policy)
    assert decision['allow'] is True
    assert decision['score'] == 90
    assert decision['failed'] == 1
    assert decision['severity_counts']['MEDIUM'] == 1


@pytest.mark.parametrize('severity', ['HIGH', 'CRITICAL'])
def test_scanner_alto_no_se_exceptua(severity):
    report, policy = inputs()
    report['results']['failed_checks'][0]['severity'] = severity
    assert evaluate(report, policy)['allow'] is False


def test_nuevo_fallo_no_hereda_excepcion():
    report, policy = inputs()
    report['results']['failed_checks'][0]['resource'] = 'aws_s3_bucket.otro'
    assert evaluate(report, policy)['allow'] is False


def test_excepcion_vencida_bloquea():
    report, policy = inputs()
    policy['exceptions'][0]['expires'] = '2000-01-01'
    assert evaluate(report, policy)['allow'] is False


def test_excepcion_high_invalida():
    report, policy = inputs()
    policy['exceptions'][0]['contextual_severity'] = 'HIGH'
    with pytest.raises(ValueError):
        evaluate(report, policy)


def test_score_bajo_bloquea_aunque_fallo_exceptuado():
    report, policy = inputs()
    policy['minimum_score'] = 95
    assert evaluate(report, policy)['allow'] is False


def test_error_de_parseo_bloquea():
    report, policy = inputs()
    report['summary']['parsing_errors'] = 1
    assert evaluate(report, policy)['allow'] is False


def test_contadores_inconsistentes_no_aprueban():
    report, policy = inputs()
    report['summary']['failed'] = 0
    with pytest.raises(ValueError):
        evaluate(report, policy)


def test_checks_omitidos_bloquean():
    report, policy = inputs()
    report['summary']['skipped'] = 1
    report['results']['skipped_checks'] = [{}]
    assert evaluate(report, policy)['allow'] is False
