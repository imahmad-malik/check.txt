"""Shared final QA runtime helpers; private authentication remains outside package."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

path = Path(__file__).resolve().parent / 'wp-final-import-qa.py'
spec = spec_from_file_location('final_import_qa', path)
module = module_from_spec(spec)
spec.loader.exec_module(module)
inspect = module.inspect
authenticate = module.authenticate
SITE = module.SITE
TESTS = module.TESTS
