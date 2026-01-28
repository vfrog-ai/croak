/**
 * vfrog.ai configuration utilities
 */

import { execa } from 'execa';

/**
 * Check if vfrog API key is set
 */
export async function checkVfrogKey() {
  return !!process.env.VFROG_API_KEY;
}

/**
 * Get vfrog API key
 */
export function getVfrogKey() {
  return process.env.VFROG_API_KEY || null;
}

/**
 * Validate vfrog API key by making a test request
 */
export async function validateVfrogKey(apiKey) {
  try {
    const response = await fetch('https://api.vfrog.ai/v1/auth/verify', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Setup vfrog.ai integration
 */
export async function setupVfrog(options = {}) {
  const apiKey = options.apiKey || getVfrogKey();

  if (!apiKey) {
    return {
      success: false,
      error: 'VFROG_API_KEY environment variable not set'
    };
  }

  // Validate the API key
  const isValid = await validateVfrogKey(apiKey);

  if (!isValid) {
    return {
      success: false,
      error: 'Invalid vfrog API key'
    };
  }

  return {
    success: true,
    apiKey: apiKey.substring(0, 8) + '...' // Masked for display
  };
}

/**
 * Create a new vfrog project
 */
export async function createVfrogProject(name, description = '') {
  const apiKey = getVfrogKey();

  if (!apiKey) {
    throw new Error('VFROG_API_KEY not set');
  }

  try {
    const response = await fetch('https://api.vfrog.ai/v1/projects', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name,
        description,
        task_type: 'detection'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to create project');
    }

    const project = await response.json();
    return project;
  } catch (error) {
    throw new Error(`Failed to create vfrog project: ${error.message}`);
  }
}

/**
 * Get vfrog project status
 */
export async function getVfrogProjectStatus(projectId) {
  const apiKey = getVfrogKey();

  if (!apiKey) {
    throw new Error('VFROG_API_KEY not set');
  }

  try {
    const response = await fetch(`https://api.vfrog.ai/v1/projects/${projectId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to get project status');
    }

    return await response.json();
  } catch (error) {
    throw new Error(`Failed to get vfrog project status: ${error.message}`);
  }
}

/**
 * Upload images to vfrog for annotation
 */
export async function uploadToVfrog(projectId, imagePaths) {
  const apiKey = getVfrogKey();

  if (!apiKey) {
    throw new Error('VFROG_API_KEY not set');
  }

  // This would use the vfrog SDK or API to upload images
  // For now, return a placeholder response
  return {
    success: true,
    projectId,
    uploadedCount: imagePaths.length,
    status: 'pending_annotation'
  };
}

/**
 * Download annotations from vfrog
 */
export async function downloadFromVfrog(projectId, format = 'yolo') {
  const apiKey = getVfrogKey();

  if (!apiKey) {
    throw new Error('VFROG_API_KEY not set');
  }

  // This would use the vfrog SDK or API to download annotations
  // For now, return a placeholder response
  return {
    success: true,
    projectId,
    format,
    annotationPath: `./data/annotations/${projectId}`
  };
}

/**
 * Get help text for vfrog setup
 */
export function getVfrogSetupHelp() {
  return `
vfrog.ai Setup Instructions
============================

1. Create an account at https://vfrog.ai

2. Go to Settings > API Keys

3. Create a new API key

4. Set the environment variable:

   Linux/macOS:
   export VFROG_API_KEY=your_api_key_here

   Windows (PowerShell):
   $env:VFROG_API_KEY = "your_api_key_here"

   Windows (CMD):
   set VFROG_API_KEY=your_api_key_here

5. Add to your shell profile for persistence:

   Linux/macOS (.bashrc or .zshrc):
   echo 'export VFROG_API_KEY=your_api_key_here' >> ~/.bashrc

For more information, visit: https://docs.vfrog.ai/api-setup
`;
}
