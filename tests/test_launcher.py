import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import launcher

class LauncherTests(unittest.TestCase):
    def test_model_is_saved_and_reused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); model=root/'test model.gguf';model.write_bytes(b'GGUFtest')
            config=root/'config.json'
            self.assertEqual(launcher.get_model(str(model),config=config),model)
            with patch('builtins.input',side_effect=AssertionError('não deve perguntar')):
                self.assertEqual(launcher.get_model(config=config),model)
    def test_invalid_model_does_not_save(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'bad.gguf';p.write_bytes(b'bad')
            with self.assertRaises(ValueError):launcher.get_model(str(p),config=root/'config')
            self.assertFalse((root/'config').exists())
    def test_integrated_start_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);proc=MagicMock();proc.poll.return_value=None
            with patch('sys.argv',['cambuca','--workspace',d]), patch.object(Path,'home',return_value=root), patch.object(launcher.shutil,'which',return_value='/fake/server'), patch.object(launcher,'get_model',return_value=root/'test.gguf'), patch.object(launcher.subprocess,'Popen',return_value=proc), patch.object(launcher,'ready',return_value=True), patch.object(launcher.campos,'main',return_value=0), patch.object(launcher,'stop') as stop:
                self.assertEqual(launcher.main(),0)
                stop.assert_called_once_with(proc)
    def test_installer_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(Path,'home',return_value=Path(d)), patch('venv.EnvBuilder.create'), patch('subprocess.run'):
                runpy.run_path(str(Path(__file__).resolve().parents[1]/'instalar.py'))
                runpy.run_path(str(Path(__file__).resolve().parents[1]/'instalar.py'))
            self.assertEqual((Path(d)/'.zshrc').read_text().count('export PATH='),1)
            self.assertTrue(os.access(Path(d)/'.local/bin/cambuca',os.X_OK))
