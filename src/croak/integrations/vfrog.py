"""vfrog.ai platform integration for annotation and deployment."""

import os
from pathlib import Path
from typing import Optional
import httpx
from pydantic import BaseModel


class VfrogProject(BaseModel):
    """vfrog project information."""

    id: str
    name: str
    url: str
    task_type: str
    classes: list[str]
    status: str = "created"


class VfrogDeployment(BaseModel):
    """vfrog deployment information."""

    id: str
    name: str
    endpoint_url: str
    api_key: str
    dashboard_url: str
    status: str = "pending"


class VfrogClient:
    """Client for vfrog.ai API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize vfrog client.

        Args:
            api_key: vfrog API key. If not provided, reads from VFROG_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found.
        """
        self.api_key = api_key or os.environ.get("VFROG_API_KEY")
        if not self.api_key:
            raise ValueError(
                "vfrog API key required. Set VFROG_API_KEY environment variable "
                "or pass api_key to VfrogClient. "
                "Get your key at https://vfrog.ai/settings/api"
            )
        self.base_url = "https://api.vfrog.ai/v1"
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )

    def create_project(
        self,
        name: str,
        task_type: str = "detection",
        classes: Optional[list[str]] = None,
    ) -> VfrogProject:
        """Create a new annotation project.

        Args:
            name: Project name.
            task_type: Task type (detection, segmentation, classification).
            classes: List of class names to detect.

        Returns:
            VfrogProject with project details.
        """
        response = self._client.post(
            "/projects",
            json={
                "name": name,
                "task_type": task_type,
                "classes": classes or [],
            },
        )
        response.raise_for_status()
        data = response.json()

        return VfrogProject(
            id=data["id"],
            name=data["name"],
            url=data["url"],
            task_type=data["task_type"],
            classes=data["classes"],
        )

    def upload_images(
        self,
        project_id: str,
        image_paths: list[Path],
        batch_size: int = 50,
    ) -> dict:
        """Upload images to a project.

        Args:
            project_id: vfrog project ID.
            image_paths: List of paths to image files.
            batch_size: Number of images to upload per batch.

        Returns:
            Upload statistics.
        """
        uploaded = 0
        failed = []

        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i : i + batch_size]
            files = []

            for path in batch:
                files.append(("images", (path.name, open(path, "rb"))))

            try:
                response = self._client.post(
                    f"/projects/{project_id}/images",
                    files=files,
                )
                response.raise_for_status()
                uploaded += len(batch)
            except Exception as e:
                failed.extend(batch)
            finally:
                for _, (_, f) in files:
                    f.close()

        return {
            "uploaded": uploaded,
            "failed": len(failed),
            "failed_files": [str(p) for p in failed],
        }

    def get_project_status(self, project_id: str) -> dict:
        """Get project annotation status.

        Args:
            project_id: vfrog project ID.

        Returns:
            Status with completed and total counts.
        """
        response = self._client.get(f"/projects/{project_id}/status")
        response.raise_for_status()
        return response.json()

    def export_annotations(
        self,
        project_id: str,
        format: str = "yolo",
    ) -> list[dict]:
        """Export annotations from a project.

        Args:
            project_id: vfrog project ID.
            format: Export format (yolo, coco, voc).

        Returns:
            List of annotation dicts with filename and content.
        """
        response = self._client.get(
            f"/projects/{project_id}/export",
            params={"format": format},
        )
        response.raise_for_status()
        return response.json()["annotations"]

    def create_deployment(
        self,
        name: str,
        model_path: str,
        class_names: list[str],
        config: Optional[dict] = None,
    ) -> VfrogDeployment:
        """Create a model deployment.

        Args:
            name: Deployment name.
            model_path: Path to model weights (.pt file).
            class_names: List of class names.
            config: Optional deployment configuration.

        Returns:
            VfrogDeployment with endpoint details.
        """
        with open(model_path, "rb") as f:
            response = self._client.post(
                "/deployments",
                data={
                    "name": name,
                    "class_names": ",".join(class_names),
                    **(config or {}),
                },
                files={"model": (Path(model_path).name, f)},
            )
        response.raise_for_status()
        data = response.json()

        return VfrogDeployment(
            id=data["id"],
            name=data["name"],
            endpoint_url=data["endpoint_url"],
            api_key=data["api_key"],
            dashboard_url=data["dashboard_url"],
        )

    def deploy_to_staging(self, deployment_id: str) -> VfrogDeployment:
        """Deploy model to staging environment.

        Args:
            deployment_id: vfrog deployment ID.

        Returns:
            Updated VfrogDeployment.
        """
        response = self._client.post(f"/deployments/{deployment_id}/staging")
        response.raise_for_status()
        data = response.json()

        return VfrogDeployment(**data)

    def deploy_to_production(self, deployment_id: str) -> VfrogDeployment:
        """Deploy model to production environment.

        Args:
            deployment_id: vfrog deployment ID.

        Returns:
            Updated VfrogDeployment with production endpoint.
        """
        response = self._client.post(f"/deployments/{deployment_id}/production")
        response.raise_for_status()
        data = response.json()

        return VfrogDeployment(**data)

    def test_endpoint(
        self,
        endpoint_url: str,
        api_key: str,
        image_path: str,
    ) -> dict:
        """Test a deployed endpoint.

        Args:
            endpoint_url: Model endpoint URL.
            api_key: API key for authentication.
            image_path: Path to test image.

        Returns:
            Inference results.
        """
        with open(image_path, "rb") as f:
            response = httpx.post(
                endpoint_url,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"image": f},
            )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
