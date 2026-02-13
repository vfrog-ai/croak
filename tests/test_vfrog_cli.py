"""Tests for VfrogCLI wrapper."""

import pytest
from unittest.mock import patch, MagicMock

from croak.integrations.vfrog import VfrogCLI, VfrogClient


class TestVfrogCLICheckInstalled:
    """Test check_installed method."""

    @patch("croak.core.commands.SecureRunner.check_command_available")
    def test_installed_when_binary_found(self, mock_check):
        mock_check.return_value = True
        assert VfrogCLI.check_installed() is True
        mock_check.assert_called_once_with("vfrog")

    @patch("croak.core.commands.SecureRunner.check_command_available")
    def test_not_installed_when_binary_missing(self, mock_check):
        mock_check.return_value = False
        assert VfrogCLI.check_installed() is False


class TestVfrogCLICheckAuthenticated:
    """Test check_authenticated method."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_authenticated_when_config_shows_true(self, mock_run):
        mock_run.return_value = {
            "success": True,
            "output": {"authenticated": True, "organisation_id": "org-1"},
        }
        assert VfrogCLI.check_authenticated() is True

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_not_authenticated_when_config_shows_false(self, mock_run):
        mock_run.return_value = {
            "success": True,
            "output": {"authenticated": False},
        }
        assert VfrogCLI.check_authenticated() is False

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_not_authenticated_when_command_fails(self, mock_run):
        mock_run.return_value = {"success": False, "output": None, "error": "not found"}
        assert VfrogCLI.check_authenticated() is False

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_not_authenticated_when_output_not_dict(self, mock_run):
        mock_run.return_value = {"success": True, "output": "some string"}
        assert VfrogCLI.check_authenticated() is False


class TestVfrogCLIGetConfig:
    """Test get_config method."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_returns_config_dict(self, mock_run):
        expected = {
            "authenticated": True,
            "organisation_id": "org-123",
            "project_id": "proj-456",
            "object_id": "",
        }
        mock_run.return_value = {"success": True, "output": expected}
        result = VfrogCLI.get_config()
        assert result["success"] is True
        assert result["output"] == expected
        mock_run.assert_called_once_with(["config", "show"])


class TestVfrogCLIContextSetters:
    """Test context setter methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_set_organisation(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.set_organisation("org-123")
        mock_run.assert_called_once_with(
            ["config", "set", "organisation", "--organisation_id", "org-123"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_set_project(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.set_project("proj-456")
        mock_run.assert_called_once_with(
            ["config", "set", "project", "--project_id", "proj-456"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_set_object(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.set_object("obj-789")
        mock_run.assert_called_once_with(
            ["config", "set", "object", "--object_id", "obj-789"]
        )


class TestVfrogCLIDatasetImages:
    """Test dataset image methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_upload_dataset_images_urls(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"uploaded": 2}}
        urls = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
        result = VfrogCLI.upload_dataset_images(urls=urls)
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["dataset_images", "upload", urls[0], urls[1]],
            timeout=600,
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_upload_dataset_images_directory(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"uploaded": 5}}
        result = VfrogCLI.upload_dataset_images(directory="/path/to/images")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["dataset_images", "upload", "--dir", "/path/to/images"],
            timeout=600,
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_upload_dataset_images_file(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"uploaded": 1}}
        result = VfrogCLI.upload_dataset_images(file_path="/path/to/image.jpg")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["dataset_images", "upload", "--file", "/path/to/image.jpg"],
            timeout=600,
        )

    def test_upload_dataset_images_no_source_raises(self):
        with pytest.raises(ValueError, match="One of urls, file_path, or directory"):
            VfrogCLI.upload_dataset_images()

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_list_dataset_images(self, mock_run):
        mock_run.return_value = {"success": True, "output": []}
        VfrogCLI.list_dataset_images()
        mock_run.assert_called_once_with(["dataset_images", "list"])

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_delete_dataset_image(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.delete_dataset_image("img-123")
        mock_run.assert_called_once_with(
            ["dataset_images", "delete", "--dataset_image_id", "img-123"]
        )


class TestVfrogCLIObjects:
    """Test object (product image) methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_create_object_with_label(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"id": "obj-1"}}
        VfrogCLI.create_object(url="https://example.com/product.jpg", label="my-product")
        mock_run.assert_called_once_with(
            ["objects", "create", "https://example.com/product.jpg", "--label", "my-product"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_create_object_minimal(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"id": "obj-1"}}
        VfrogCLI.create_object(url="https://example.com/product.jpg")
        mock_run.assert_called_once_with(
            ["objects", "create", "https://example.com/product.jpg"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_create_object_from_file(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"id": "obj-1"}}
        VfrogCLI.create_object(file_path="/path/to/product.jpg", label="my-product")
        mock_run.assert_called_once_with(
            ["objects", "create", "--file", "/path/to/product.jpg", "--label", "my-product"]
        )

    def test_create_object_no_source_raises(self):
        with pytest.raises(ValueError, match="One of url or file_path"):
            VfrogCLI.create_object()

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_list_objects(self, mock_run):
        mock_run.return_value = {"success": True, "output": []}
        VfrogCLI.list_objects()
        mock_run.assert_called_once_with(["objects", "list"])


class TestVfrogCLIIterations:
    """Test iteration (SSAT loop) methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_create_iteration(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"id": "iter-1"}}
        VfrogCLI.create_iteration("obj-123", random_count=20)
        mock_run.assert_called_once_with(
            ["iterations", "create", "obj-123", "--random", "20"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_run_ssat_basic(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"status": "annotating"}}
        VfrogCLI.run_ssat("iter-123")
        mock_run.assert_called_once_with(
            ["iterations", "ssat", "--iteration_id", "iter-123"],
            timeout=600,
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_run_ssat_with_random_count(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.run_ssat("iter-123", random_count=40)
        args = mock_run.call_args[0][0]
        assert "--random" in args
        assert "40" in args

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_run_ssat_with_restart(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.run_ssat("iter-123", restart=True)
        args = mock_run.call_args[0][0]
        assert "--restart" in args

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_get_halo_url(self, mock_run):
        mock_run.return_value = {
            "success": True,
            "output": {"halo_url": "https://halo.vfrog.ai/review/iter-123"},
        }
        result = VfrogCLI.get_halo_url("iter-123")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["iterations", "halo", "--iteration_id", "iter-123"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_next_iteration(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"id": "iter-2"}}
        VfrogCLI.next_iteration("iter-1")
        mock_run.assert_called_once_with(
            ["iterations", "next", "--iteration_id", "iter-1"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_restart_iteration(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.restart_iteration("iter-1")
        mock_run.assert_called_once_with(
            ["iterations", "restart", "--iteration_id", "iter-1"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_list_iterations_with_object_filter(self, mock_run):
        mock_run.return_value = {"success": True, "output": []}
        VfrogCLI.list_iterations(object_id="obj-123")
        mock_run.assert_called_once_with(
            ["iterations", "list", "--object_id", "obj-123"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_list_iterations_no_filter(self, mock_run):
        mock_run.return_value = {"success": True, "output": []}
        VfrogCLI.list_iterations()
        mock_run.assert_called_once_with(["iterations", "list"])


class TestVfrogCLIIterationStatus:
    """Test iteration status, deploy, annotations methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_get_iteration_status(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"status": "annotating"}}
        result = VfrogCLI.get_iteration_status("iter-123")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["iterations", "status", "--iteration_id", "iter-123"],
            timeout=300,
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_get_iteration_status_watch(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"status": "complete"}}
        VfrogCLI.get_iteration_status("iter-123", watch=True)
        mock_run.assert_called_once_with(
            ["iterations", "status", "--iteration_id", "iter-123", "--watch"],
            timeout=600,
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_deploy_iteration(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"deployed": True}}
        result = VfrogCLI.deploy_iteration("iter-123")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["iterations", "deploy", "--iteration_id", "iter-123"]
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_get_annotations(self, mock_run):
        mock_run.return_value = {"success": True, "output": []}
        result = VfrogCLI.get_annotations("iter-123")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["iterations", "annotations", "--iteration_id", "iter-123"]
        )


class TestVfrogCLIExport:
    """Test export methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_export_yolo(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"path": "./export"}}
        result = VfrogCLI.export_yolo("iter-123", output_dir="./my-export")
        assert result["success"] is True
        mock_run.assert_called_once_with(
            ["export", "yolo", "--iteration_id", "iter-123", "--output", "./my-export"],
            timeout=600,
        )

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_export_yolo_default_dir(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.export_yolo("iter-123")
        args = mock_run.call_args[0][0]
        assert "--output" in args
        assert "./export" in args


class TestVfrogCLISSATIndustry:
    """Test SSAT industry parameter."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_run_ssat_with_industry(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.run_ssat("iter-123", industry="retail")
        args = mock_run.call_args[0][0]
        assert "--industry" in args
        assert "retail" in args

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_run_ssat_without_industry(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        VfrogCLI.run_ssat("iter-123")
        args = mock_run.call_args[0][0]
        assert "--industry" not in args


class TestVfrogCLITraining:
    """Test training method."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_train_iteration(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"status": "training"}}
        VfrogCLI.train_iteration("iter-123")
        mock_run.assert_called_once_with(
            ["iterations", "train", "--iteration_id", "iter-123"],
            timeout=3600,
        )


class TestVfrogCLIInference:
    """Test inference method."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_inference_with_image_path(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"detections": []}}
        VfrogCLI.run_inference(image_path="/path/to/img.jpg")
        args = mock_run.call_args[0][0]
        assert "inference" in args
        assert "--image" in args
        assert "/path/to/img.jpg" in args

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_inference_with_image_url(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"detections": []}}
        VfrogCLI.run_inference(image_url="https://example.com/img.jpg")
        args = mock_run.call_args[0][0]
        assert "--image_url" in args
        assert "https://example.com/img.jpg" in args

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_inference_with_api_key(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"detections": []}}
        VfrogCLI.run_inference(image_path="/img.jpg", api_key="test-key-123")
        args = mock_run.call_args[0][0]
        assert "--api-key" in args
        assert "test-key-123" in args


class TestVfrogCLILogin:
    """Test login method."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_login_passes_credentials(self, mock_run):
        mock_run.return_value = {"success": True, "output": "Logged in"}
        VfrogCLI.login("user@example.com", "password123")
        mock_run.assert_called_once_with(
            ["login", "--email", "user@example.com", "--password", "password123"],
            json_output=False,
        )


class TestVfrogCLIProjects:
    """Test project methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_list_projects(self, mock_run):
        mock_run.return_value = {"success": True, "output": [{"id": "p1", "title": "Test"}]}
        result = VfrogCLI.list_projects()
        assert result["success"] is True
        mock_run.assert_called_once_with(["projects", "list"])

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_create_project(self, mock_run):
        mock_run.return_value = {"success": True, "output": {"id": "p2"}}
        VfrogCLI.create_project("My Project")
        mock_run.assert_called_once_with(["projects", "create", "My Project"])


class TestVfrogCLIOrganisations:
    """Test organisation methods."""

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_list_organisations(self, mock_run):
        mock_run.return_value = {"success": True, "output": []}
        VfrogCLI.list_organisations()
        mock_run.assert_called_once_with(["organisations", "list"])


class TestVfrogCLIInputSanitization:
    """Test argument injection prevention."""

    def test_upload_rejects_flag_injection(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.upload_dataset_images(urls=["--malicious-flag"])

    def test_upload_rejects_non_http_url(self):
        with pytest.raises(ValueError, match="http:// or https://"):
            VfrogCLI.upload_dataset_images(urls=["ftp://example.com/img.jpg"])

    def test_create_object_rejects_flag_url(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.create_object(url="--inject")

    def test_create_object_rejects_flag_label(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.create_object(url="https://example.com/img.jpg", label="--inject")

    def test_create_object_rejects_flag_external_id(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.create_object(url="https://example.com/img.jpg", external_id="--inject")

    def test_delete_object_rejects_flag_id(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.delete_object("--drop-all")

    def test_run_ssat_rejects_flag_id(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.run_ssat("--inject")

    def test_inference_rejects_flag_path(self):
        with pytest.raises(ValueError, match="must not start with"):
            VfrogCLI.run_inference(image_path="--inject")

    def test_inference_rejects_invalid_url(self):
        with pytest.raises(ValueError, match="http:// or https://"):
            VfrogCLI.run_inference(image_url="file:///etc/passwd")

    @patch("croak.core.commands.SecureRunner.run_vfrog")
    def test_valid_inputs_pass_through(self, mock_run):
        mock_run.return_value = {"success": True, "output": {}}
        # These should not raise
        VfrogCLI.upload_dataset_images(urls=["https://example.com/img.jpg"])
        VfrogCLI.create_object(url="https://example.com/img.jpg", label="my-label")
        VfrogCLI.run_ssat("abc-123-def")
        assert mock_run.call_count == 3


class TestVfrogClientDeprecated:
    """Test that VfrogClient raises deprecation."""

    def test_vfrog_client_raises_not_implemented(self):
        with pytest.warns(DeprecationWarning):
            with pytest.raises(NotImplementedError):
                VfrogClient()
