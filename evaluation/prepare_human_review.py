"""Prepare actual recorded answers for a named reviewer; never manufacture labels."""
import argparse
import hashlib
import json
from pathlib import Path
from evaluation.evaluate_explanations import REVIEW_FIELDS, evaluate


def prepare(source, output, reviewer):
    if output.exists():
        raise ValueError('Review already exists; refusing to overwrite human labels')
    rows = json.loads(source.read_text())
    evaluate(rows)  # Reject missing responses before creating a review.
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    reviews = [{**row, 'reviewer': reviewer, 'review': {k: None for k in REVIEW_FIELDS},
                'review_notes': '', 'recording_sha256': digest} for row in rows]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(reviews, indent=2) + '\n')
    text = [f'# Advisor review for {reviewer}', '',
        'These are actual recorded answers. Fill each `review` field in the JSON with `true` or `false`; leave unresolved judgements `null`. Add notes for failures. A named reviewer with null labels does not count as a completed review.', '',
        'Check groundedness (claims supported by supplied evidence), factual accuracy (values, units and attribution), completeness (answers the question), tool invocation (what-if uses fresh simulation; conditional packages are blocked), unavailable handling (no invented replacement), and no unsupported claims (including nonnumeric promises). Do not approve merely because the numeric check passes.', '',
        f'Recorded source SHA256: `{digest}`', '',
        f'After reviewing: `python -m evaluation.evaluate_explanations --input {output.as_posix()}`', '',
        'The PRD targets are ≥90% groundedness, ≥90% factual accuracy and <5% unsupported claims. Existing answers may fail completeness; mark that accurately and fix/rerecord failing cases before claiming success.', '']
    for row in rows:
        answer = row['answer']
        text += [f"## {row['case_id']}: {row['question']}", '',
            f"Status: {answer['status']}; mode: {answer['mode']}; tools: {', '.join(answer['tool_calls']) or 'none'}.", '',
            row['response'], '', '### Structured evidence', '', '```json',
            json.dumps(answer.get('result'), indent=2), '```', '']
    output.with_suffix('.md').write_text('\n'.join(text))
    return len(reviews)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviewer', required=True)
    args = parser.parse_args()
    print(f'Prepared {prepare(args.input, args.output, args.reviewer)} answers; review labels remain pending.')
