/**
 * CROAK Command Generator
 * Generates IDE slash commands from agent and workflow definitions
 */

import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { join, basename } from 'path';
import yaml from 'yaml';

import { getIDEConfig, createIDEDirectories } from './ide-setup.js';
import { CROAK_DIR } from '../index.js';

/**
 * Template directory path
 */
const TEMPLATE_DIR = join(
  import.meta.url.replace('file://', '').replace(/\/src\/utils\/command-generator\.js$/, ''),
  'templates',
  'claude-code'
);

/**
 * Load and parse a YAML file
 * @param {string} filePath - Path to YAML file
 * @returns {Object} Parsed YAML content
 */
function loadYaml(filePath) {
  const content = readFileSync(filePath, 'utf8');
  return yaml.parse(content);
}

/**
 * Simple template rendering (replaces {{variable}} placeholders)
 * @param {string} template - Template string
 * @param {Object} data - Data to inject
 * @returns {string} Rendered template
 */
function renderTemplate(template, data) {
  let result = template;

  // Handle simple variable replacements
  for (const [key, value] of Object.entries(data)) {
    const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
    result = result.replace(regex, value ?? '');
  }

  // Handle {{#each array}}...{{/each}} blocks
  const eachRegex = /\{\{#each\s+(\w+)\}\}([\s\S]*?)\{\{\/each\}\}/g;
  result = result.replace(eachRegex, (match, arrayName, innerTemplate) => {
    const arr = data[arrayName];
    if (!Array.isArray(arr)) return '';

    return arr
      .map((item, index) => {
        let rendered = innerTemplate;
        // Replace {{this}} with the item itself (for simple arrays)
        rendered = rendered.replace(/\{\{this\}\}/g, item);
        // Replace {{@index}} with the index
        rendered = rendered.replace(/\{\{@index\}\}/g, String(index + 1));
        // Replace {{property}} for object arrays
        if (typeof item === 'object') {
          for (const [key, value] of Object.entries(item)) {
            const propRegex = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
            rendered = rendered.replace(propRegex, value ?? '');
          }
        }
        // Handle {{#if property}}...{{/if}}
        const ifRegex = /\{\{#if\s+(\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g;
        rendered = rendered.replace(ifRegex, (m, prop, content) => {
          return item[prop] ? content : '';
        });
        return rendered;
      })
      .join('');
  });

  return result;
}

/**
 * Extract agent metadata from YAML definition
 * @param {Object} agentDef - Parsed agent YAML
 * @returns {Object} Agent metadata for template
 */
function extractAgentMetadata(agentDef) {
  const agent = agentDef.agent || agentDef;

  return {
    agent_id: agent.metadata?.id?.split('/').pop() || 'unknown',
    agent_file: `${agent.metadata?.id?.split('/').pop()}.agent.yaml`,
    persona_name: agent.metadata?.name || 'Agent',
    title: agent.metadata?.title || 'Specialist',
    icon: agent.metadata?.icon || '🤖',
    role: agent.persona?.role || 'AI Assistant',
    description: `Activate ${agent.metadata?.name || 'Agent'} — CROAK ${agent.metadata?.title || 'Specialist'}`,
    commands: (agent.menu?.commands || []).slice(0, 8).map((cmd) => ({
      trigger: cmd.trigger,
      description: cmd.description,
    })),
  };
}

/**
 * Extract workflow metadata from YAML definition
 * @param {Object} workflowDef - Parsed workflow YAML
 * @returns {Object} Workflow metadata for template
 */
function extractWorkflowMetadata(workflowDef) {
  const workflow = workflowDef;

  return {
    workflow_id: workflow.metadata?.id?.split('/').pop() || 'unknown',
    workflow_file: workflow.metadata?.id?.split('/').pop() || 'unknown',
    workflow_name: workflow.metadata?.name || 'Workflow',
    agent: workflow.metadata?.agent || 'router',
    description: workflow.metadata?.description || 'Run CROAK workflow',
    steps: (workflow.steps || []).map((step) => ({
      name: step.name,
      file: step.file,
      required: step.required,
    })),
    checklist: workflow.checklist || [],
    completion_state: workflow.completion?.state_update || 'unknown',
    next_workflow: workflow.completion?.next_workflow || 'none',
    handoff_to: workflow.completion?.handoff_to || 'router',
  };
}

/**
 * Generate agent slash command file
 * @param {string} agentPath - Path to agent YAML file
 * @param {string} outputDir - Output directory for command file
 * @returns {string} Path to generated command file
 */
export function generateAgentCommand(agentPath, outputDir) {
  // Load agent definition
  const agentDef = loadYaml(agentPath);
  const metadata = extractAgentMetadata(agentDef);

  // Load template
  const templatePath = join(TEMPLATE_DIR, 'agent-command.md.tmpl');
  const template = readFileSync(templatePath, 'utf8');

  // Render template
  const rendered = renderTemplate(template, metadata);

  // Write output file
  const outputPath = join(outputDir, `${metadata.agent_id}.md`);
  writeFileSync(outputPath, rendered);

  return outputPath;
}

/**
 * Generate workflow slash command file
 * @param {string} workflowDir - Path to workflow directory
 * @param {string} outputDir - Output directory for command file
 * @returns {string} Path to generated command file
 */
export function generateWorkflowCommand(workflowDir, outputDir) {
  // Load workflow definition
  const workflowPath = join(workflowDir, 'workflow.yaml');
  const workflowDef = loadYaml(workflowPath);
  const metadata = extractWorkflowMetadata(workflowDef);

  // Load template
  const templatePath = join(TEMPLATE_DIR, 'workflow-command.md.tmpl');
  const template = readFileSync(templatePath, 'utf8');

  // Render template
  const rendered = renderTemplate(template, metadata);

  // Write output file
  const outputPath = join(outputDir, `${metadata.workflow_id}.md`);
  writeFileSync(outputPath, rendered);

  return outputPath;
}

/**
 * Generate all agent commands for a project
 * @param {string} ideKey - IDE identifier
 * @param {Object} options - Generation options
 * @returns {Array} Array of generated file paths
 */
export function generateAllAgentCommands(ideKey, options = {}) {
  const paths = createIDEDirectories(ideKey);
  const agentsDir = join(CROAK_DIR, 'agents');
  const generated = [];

  // Find all agent YAML files
  const agentFiles = readdirSync(agentsDir).filter((f) => f.endsWith('.agent.yaml'));

  for (const file of agentFiles) {
    // Skip if module filtering is enabled and agent not selected
    if (options.selectedAgents) {
      const agentId = file.replace('.agent.yaml', '');
      if (!options.selectedAgents.includes(agentId)) {
        continue;
      }
    }

    try {
      const outputPath = generateAgentCommand(join(agentsDir, file), paths.agents);
      generated.push(outputPath);
    } catch (error) {
      console.warn(`Warning: Failed to generate command for ${file}: ${error.message}`);
    }
  }

  return generated;
}

/**
 * Generate all workflow commands for a project
 * @param {string} ideKey - IDE identifier
 * @param {Object} options - Generation options
 * @returns {Array} Array of generated file paths
 */
export function generateAllWorkflowCommands(ideKey, options = {}) {
  const paths = createIDEDirectories(ideKey);
  const workflowsDir = join(CROAK_DIR, 'workflows');
  const generated = [];

  // Find all workflow directories (contain workflow.yaml)
  let workflowDirs;
  try {
    workflowDirs = readdirSync(workflowsDir).filter((d) => {
      const workflowPath = join(workflowsDir, d, 'workflow.yaml');
      try {
        return readFileSync(workflowPath);
      } catch {
        return false;
      }
    });
  } catch {
    workflowDirs = [];
  }

  for (const dir of workflowDirs) {
    try {
      const outputPath = generateWorkflowCommand(join(workflowsDir, dir), paths.workflows);
      generated.push(outputPath);
    } catch (error) {
      console.warn(`Warning: Failed to generate command for workflow ${dir}: ${error.message}`);
    }
  }

  return generated;
}

/**
 * Generate all IDE commands for a project
 * @param {string} ideKey - IDE identifier
 * @param {Object} options - Generation options
 * @returns {Object} Summary of generated files
 */
export function generateAllCommands(ideKey, options = {}) {
  const agents = generateAllAgentCommands(ideKey, options);
  const workflows = generateAllWorkflowCommands(ideKey, options);

  return {
    agents,
    workflows,
    total: agents.length + workflows.length,
  };
}
