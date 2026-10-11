import json
import pytest
from evaluation.prepare_human_review import prepare
from evaluation.evaluate_explanations import evaluate


def test_prepared_reviewer_does_not_count_as_completed_and_labels_cannot_be_overwritten(tmp_path):
    source = tmp_path / 'recording.json'
    source.write_text(json.dumps([{'case_id': 'test', 'question': 'Explain my score',
        'response': 'Score: 50 points.', 'allowed_numbers': ['50'],
        'answer': {'status': 'success', 'mode': 'deterministic', 'tool_calls': ['assessment'], 'result': {'score': 50}}}]))
    target = tmp_path / 'review.json'
    assert prepare(source, target, 'Somyadeep') == 1
    rows = json.loads(target.read_text())
    metrics = evaluate(rows)
    assert metrics['human_reviewed'] == 0
    assert metrics['targets_met'] is None
    rows[0]['review']['groundedness'] = False
    target.write_text(json.dumps(rows))
    with pytest.raises(ValueError, match='refusing to overwrite'):
        prepare(source, target, 'Somyadeep')
    assert json.loads(target.read_text())[0]['review']['groundedness'] is False
