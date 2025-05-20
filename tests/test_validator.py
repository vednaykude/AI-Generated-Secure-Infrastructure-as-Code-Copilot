import pytest
from pathlib import Path
from iac_cli.validator import ValidatorEngine, ValidationError

@pytest.fixture
def validator():
    return ValidatorEngine()

@pytest.fixture
def valid_tf_file(tmp_path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
  
  versioning {
    enabled = true
  }
}
""")
    return tf_file

@pytest.fixture
def invalid_tf_file(tmp_path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
  
  versioning {
    enabled = "true"  # Invalid: should be boolean
  }
}
""")
    return tf_file

def test_validate_valid_file(validator, valid_tf_file):
    errors = validator.validate(valid_tf_file)
    assert len(errors) == 0

def test_validate_invalid_file(validator, invalid_tf_file):
    errors = validator.validate(invalid_tf_file)
    assert len(errors) > 0
    assert any("Invalid value for argument" in error.message for error in errors)

def test_validate_nonexistent_file(validator):
    errors = validator.validate(Path("nonexistent.tf"))
    assert len(errors) > 0
    assert any("No such file" in error.message for error in errors) 