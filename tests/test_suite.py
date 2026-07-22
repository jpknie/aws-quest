import pytest

from aws_quest import calculate_damage, is_correct_answer, normalize_answer, load_questions, Question, Choice


def test_normalize_answer():
    assert normalize_answer("  Amazon S3  ") == "amazon s3"


def test_is_correct_answer_when_case_and_spaces_differ():
    assert is_correct_answer("  Lambda ", "lambda") is True


def test_is_correct_answer_when_wrong():
    assert is_correct_answer("EC2", "S3") is False


@pytest.mark.parametrize(
    ("difficulty", "expected_damage"),
    [
        ("easy", 30),
        ("medium", 20),
        ("hard", 10),
    ],
)
def test_calculate_damage(difficulty, expected_damage):
    assert calculate_damage(difficulty) == expected_damage


def test_calculate_damage_rejects_unknown_difficulty():
    with pytest.raises(ValueError):
        calculate_damage("nightmare")

def test_load_questions_json():
    path = "tests/fixtures/questions.json"
    questions: list[Question] = load_questions(path)
    assert len(questions) == 1
    assert questions[0].difficulty == "easy"
    assert questions[0].prompt == "Which AWS service is object storage?"

    expected_choices = [
        ("A", "Amazon S3"),
        ("B", "Amazon EC2"),
        ("C", "Amazon RDS"),
        ("D", "AWS Lambda"),
    ]

    for choice, expected in zip(questions[0].choices, expected_choices):
        expected_id, expected_text = expected
        assert choice.id == expected_id and choice.text == expected_text
    
    
    
