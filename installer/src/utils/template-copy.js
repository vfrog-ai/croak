/**
 * Template copying utilities
 * Copies agent definitions, workflows, and knowledge files to project
 */

import { existsSync, mkdirSync, cpSync, readdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Templates directory (relative to package root)
const TEMPLATES_DIR = join(__dirname, '..', '..', 'templates');

/**
 * Copy all templates to the CROAK directory
 */
export async function copyTemplates(croakDir) {
  const directories = [
    { src: 'agents', dest: 'agents' },
    { src: 'workflows', dest: 'workflows' },
    { src: 'knowledge', dest: 'knowledge' },
    { src: 'contracts', dest: 'contracts' },
    { src: 'templates', dest: 'templates' }
  ];

  for (const { src, dest } of directories) {
    const srcPath = join(TEMPLATES_DIR, src);
    const destPath = join(croakDir, dest);

    if (existsSync(srcPath)) {
      // Create destination if it doesn't exist
      if (!existsSync(destPath)) {
        mkdirSync(destPath, { recursive: true });
      }

      // Copy recursively
      cpSync(srcPath, destPath, { recursive: true });
    }
  }
}

/**
 * Copy a single agent definition
 */
export async function copyAgent(agentName, croakDir) {
  const srcPath = join(TEMPLATES_DIR, 'agents', agentName);
  const destPath = join(croakDir, 'agents', agentName);

  if (!existsSync(srcPath)) {
    throw new Error(`Agent template not found: ${agentName}`);
  }

  if (!existsSync(destPath)) {
    mkdirSync(destPath, { recursive: true });
  }

  cpSync(srcPath, destPath, { recursive: true });
}

/**
 * Copy a single workflow
 */
export async function copyWorkflow(workflowName, croakDir) {
  const srcPath = join(TEMPLATES_DIR, 'workflows', workflowName);
  const destPath = join(croakDir, 'workflows', workflowName);

  if (!existsSync(srcPath)) {
    throw new Error(`Workflow template not found: ${workflowName}`);
  }

  if (!existsSync(destPath)) {
    mkdirSync(destPath, { recursive: true });
  }

  cpSync(srcPath, destPath, { recursive: true });
}

/**
 * List available agent templates
 */
export function listAgentTemplates() {
  const agentsPath = join(TEMPLATES_DIR, 'agents');

  if (!existsSync(agentsPath)) {
    return [];
  }

  return readdirSync(agentsPath, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);
}

/**
 * List available workflow templates
 */
export function listWorkflowTemplates() {
  const workflowsPath = join(TEMPLATES_DIR, 'workflows');

  if (!existsSync(workflowsPath)) {
    return [];
  }

  return readdirSync(workflowsPath, { withFileTypes: true })
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name);
}

/**
 * Create a placeholder file if templates don't exist
 * This is used during development before templates are bundled
 */
export function createPlaceholders(croakDir) {
  const placeholders = {
    'agents/router/router.agent.yaml': '# Router agent - will be populated by croak upgrade',
    'agents/data/data.agent.yaml': '# Data agent - will be populated by croak upgrade',
    'agents/training/training.agent.yaml': '# Training agent - will be populated by croak upgrade',
    'agents/evaluation/evaluation.agent.yaml': '# Evaluation agent - will be populated by croak upgrade',
    'agents/deployment/deployment.agent.yaml': '# Deployment agent - will be populated by croak upgrade',
    'workflows/data-preparation/workflow.yaml': '# Data preparation workflow',
    'workflows/model-training/workflow.yaml': '# Model training workflow',
    'workflows/model-evaluation/workflow.yaml': '# Model evaluation workflow',
    'workflows/model-deployment/workflow.yaml': '# Model deployment workflow'
  };

  for (const [relativePath, content] of Object.entries(placeholders)) {
    const fullPath = join(croakDir, relativePath);
    const dir = dirname(fullPath);

    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }

    if (!existsSync(fullPath)) {
      writeFileSync(fullPath, content);
    }
  }
}
