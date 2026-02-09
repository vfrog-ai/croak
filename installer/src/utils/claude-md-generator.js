/**
 * CROAK CLAUDE.md Generator
 * Generates project context file for Claude Code
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Template path for CLAUDE.md
 */
const TEMPLATE_PATH = join(__dirname, '..', '..', 'templates', 'CLAUDE.md.tmpl');

/**
 * Simple template rendering (replaces {{variable}} placeholders)
 * @param {string} template - Template string
 * @param {Object} data - Data to inject
 * @returns {string} Rendered template
 */
function renderTemplate(template, data) {
  let result = template;

  for (const [key, value] of Object.entries(data)) {
    const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
    result = result.replace(regex, value ?? '');
  }

  return result;
}

/**
 * Generate CLAUDE.md from project configuration
 * @param {Object} config - Project configuration from config.yaml
 * @param {Object} options - Generation options
 * @returns {string} Path to generated file
 */
export function generateClaudeMd(config, options = {}) {
  // Load template
  let template;
  try {
    template = readFileSync(TEMPLATE_PATH, 'utf8');
  } catch (error) {
    // Fallback template if file doesn't exist
    template = getDefaultTemplate();
  }

  // Extract values from config
  const data = {
    project_name: config.project?.name || 'Untitled Project',
    task_type: config.project?.task_type || 'detection',
    architecture: config.training?.architecture || 'yolov8s',
    compute_provider: config.compute?.provider || 'local',
    tracking_backend: config.tracking?.backend || 'none',
  };

  // Render template
  const rendered = renderTemplate(template, data);

  // Determine output path
  const outputPath = options.outputPath || 'CLAUDE.md';

  // Check if file already exists
  if (existsSync(outputPath) && !options.overwrite) {
    // Append CROAK section to existing file
    const existing = readFileSync(outputPath, 'utf8');
    if (!existing.includes('CROAK Project')) {
      writeFileSync(outputPath, existing + '\n\n---\n\n' + rendered);
    }
  } else {
    writeFileSync(outputPath, rendered);
  }

  return outputPath;
}

/**
 * Check if CLAUDE.md exists and contains CROAK section
 * @returns {boolean} True if CROAK section exists
 */
export function hasCroakSection() {
  try {
    const content = readFileSync('CLAUDE.md', 'utf8');
    return content.includes('CROAK Project') || content.includes('CROAK Agents');
  } catch {
    return false;
  }
}

/**
 * Update existing CLAUDE.md with new config values
 * @param {Object} config - Project configuration
 * @returns {boolean} True if updated successfully
 */
export function updateClaudeMd(config) {
  if (!existsSync('CLAUDE.md')) {
    return false;
  }

  const content = readFileSync('CLAUDE.md', 'utf8');

  // Find and replace config values
  let updated = content;

  // Update architecture
  if (config.training?.architecture) {
    updated = updated.replace(
      /\*\*Architecture:\*\*\s*\w+/,
      `**Architecture:** ${config.training.architecture}`
    );
  }

  // Update compute provider
  if (config.compute?.provider) {
    updated = updated.replace(
      /\*\*GPU provider:\*\*\s*\w+/,
      `**GPU provider:** ${config.compute.provider}`
    );
  }

  // Update tracking
  if (config.tracking?.backend) {
    updated = updated.replace(
      /\*\*Experiment tracking:\*\*\s*\w+/,
      `**Experiment tracking:** ${config.tracking.backend}`
    );
  }

  writeFileSync('CLAUDE.md', updated);
  return true;
}

/**
 * Get default template as fallback
 * @returns {string} Default CLAUDE.md template
 */
function getDefaultTemplate() {
  return `# CROAK Project — {{project_name}}

This is a computer vision project managed by the CROAK framework
(Computer Recognition Orchestration Agent Kit).

## Project Configuration

- **Task type:** {{task_type}}
- **Architecture:** {{architecture}}
- **GPU provider:** {{compute_provider}}
- **Experiment tracking:** {{tracking_backend}}

## CROAK Agents

Use slash commands to activate specialized agents:

- \`/croak-router\` — Pipeline coordinator (start here for guidance)
- \`/croak-data\` — Scan, validate, annotate (vfrog SSAT or classic import)
- \`/croak-training\` — Train on local GPU, Modal.com, or vfrog platform
- \`/croak-evaluation\` — Model evaluation and error analysis
- \`/croak-deployment\` — Deploy to vfrog inference, Modal serverless, or edge

## CROAK Workflows

Run end-to-end workflows:

- \`/croak-data-preparation\` — Full data pipeline (scan → validate → annotate → split → export)
- \`/croak-model-training\` — Training pipeline (recommend → configure → execute → handoff)
- \`/croak-model-evaluation\` — Evaluation pipeline (evaluate → analyze → diagnose → report)
- \`/croak-model-deployment\` — Deployment pipeline (export → optimize → deploy → verify)

## Annotation & Training Paths

CROAK supports two annotation workflows:

- **vfrog SSAT** — Auto-annotation via vfrog CLI. Upload images, run SSAT iterations, review in HALO. Train on vfrog's managed platform.
- **Classic** — Import annotations from external tools (CVAT, Label Studio, Roboflow) in YOLO/COCO/VOC format. Train on local GPU or Modal.com.

> \`VFROG_API_KEY\` is only needed for inference (\`croak deploy vfrog\`). Annotation and training use CLI authentication (\`croak vfrog setup\`).

## Pipeline State

Current progress is tracked in \`.croak/pipeline-state.yaml\`.
Always check pipeline state before suggesting next steps.

## Key Directories

- \`.croak/\` — Framework configuration, agents, workflows, knowledge
- \`data/\` — Raw and processed datasets
- \`training/\` — Configs, scripts, and experiment outputs
- \`evaluation/\` — Evaluation reports and analysis
- \`deployment/\` — Exported models and deployment packages

## CLI Commands

The \`croak\` CLI provides these commands:

- \`croak scan\` — Scan data directory for images
- \`croak validate\` — Validate data quality
- \`croak prepare\` — Prepare dataset for training
- \`croak annotate\` — Annotate images (vfrog SSAT or classic import)
- \`croak train\` — Train model (local GPU, Modal, or vfrog platform)
- \`croak evaluate\` — Evaluate model performance
- \`croak deploy\` — Deploy to vfrog inference, Modal, or edge
- \`croak status\` — Check pipeline status
- \`croak vfrog setup\` — Login to vfrog CLI and select organisation/project
- \`croak vfrog status\` — Show vfrog CLI auth and context status
- \`croak next\` — Advance to next SSAT iteration
- \`croak history\` — Show iteration history

## vfrog CLI

The vfrog CLI is a standalone Go binary (not a Python package). Authentication is email/password based via Supabase. The CLI stores auth tokens in \`~/.vfrog/\`.

Context hierarchy: organisation → project → object → iteration.

Setup: \`croak vfrog setup\` (walks through login, org selection, project selection).

## Conventions

- Always validate data before training
- Use handoff contracts for inter-agent communication
- Update pipeline-state.yaml after completing any workflow stage
- When in doubt, run \`croak status\` to check current state
- Consult the knowledge base in \`.croak/knowledge/\` for domain guidance
`;
}
