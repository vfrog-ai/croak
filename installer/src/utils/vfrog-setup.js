/**
 * vfrog CLI integration utilities
 *
 * All functions invoke the vfrog Go binary (not HTTP API calls).
 * The CLI manages its own auth state in ~/.vfrog/.
 */

/**
 * Check if vfrog CLI binary is available on PATH.
 * @returns {Promise<boolean>}
 */
export async function checkVfrogCLI() {
  const { execa } = await import('execa');

  try {
    await execa('vfrog', ['version']);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get vfrog CLI version string.
 * @returns {Promise<string|null>} Version string or null if not installed.
 */
export async function getVfrogVersion() {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('vfrog', ['version']);
    return stdout.trim();
  } catch {
    return null;
  }
}

/**
 * Check if user is authenticated with vfrog CLI.
 * @returns {Promise<boolean>}
 */
export async function checkVfrogAuth() {
  const config = await getVfrogConfig();
  if (!config) return false;
  return config.authenticated === true;
}

/**
 * Get vfrog CLI config (auth status, org, project, object).
 * @returns {Promise<object|null>} Config object or null on failure.
 */
export async function getVfrogConfig() {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('vfrog', ['config', 'show', '--json']);
    return JSON.parse(stdout);
  } catch {
    return null;
  }
}

/**
 * Check if vfrog context is fully configured (org + project set).
 * @returns {Promise<{configured: boolean, organisation_id: string|null, project_id: string|null}>}
 */
export async function checkVfrogContext() {
  const config = await getVfrogConfig();

  if (!config) {
    return { configured: false, organisation_id: null, project_id: null };
  }

  const orgId = config.organisation_id || null;
  const projectId = config.project_id || null;

  return {
    configured: !!(orgId && projectId),
    organisation_id: orgId,
    project_id: projectId,
  };
}

/**
 * Create a new vfrog project in the active organisation.
 * @param {string} name - Project name.
 * @returns {Promise<object>} Created project data.
 */
export async function createVfrogProject(name) {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('vfrog', ['projects', 'create', name, '--json']);
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`Failed to create vfrog project: ${error.message}`);
  }
}

/**
 * List vfrog projects in the active organisation.
 * @returns {Promise<Array>} List of projects.
 */
export async function listVfrogProjects() {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('vfrog', ['projects', 'list', '--json']);
    const result = JSON.parse(stdout);
    return Array.isArray(result) ? result : [];
  } catch {
    return [];
  }
}

/**
 * Upload dataset images to vfrog (URL-based).
 * @param {string[]} urls - Image URLs to upload.
 * @returns {Promise<object>} Upload result.
 */
export async function uploadToVfrog(urls) {
  const { execa } = await import('execa');

  try {
    const { stdout } = await execa('vfrog', ['dataset_images', 'upload', ...urls, '--json'], {
      timeout: 600000,
    });
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`Failed to upload to vfrog: ${error.message}`);
  }
}

/**
 * Get help text for vfrog CLI setup.
 * @returns {string} Setup instructions.
 */
export function getVfrogSetupHelp() {
  return `
vfrog CLI Setup Instructions
=============================

1. Download the vfrog CLI from:
   https://github.com/vfrog/vfrog-cli/releases

2. Install the binary:

   macOS/Linux:
   chmod +x vfrog
   sudo mv vfrog /usr/local/bin/

   Windows:
   Add vfrog.exe directory to your PATH

3. Verify installation:
   vfrog version

4. Login and configure context:
   croak vfrog setup

   This will walk you through:
   - Email/password login
   - Organisation selection
   - Project selection or creation

5. For inference, set your API key:
   export VFROG_API_KEY=your_key_here

For more information, visit: https://github.com/vfrog/vfrog-cli
`;
}

/**
 * @deprecated Use checkVfrogCLI() and checkVfrogAuth() instead.
 * Kept for backward compatibility during migration.
 */
export async function checkVfrogKey() {
  return checkVfrogCLI() && (await checkVfrogAuth());
}
