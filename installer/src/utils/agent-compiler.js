/**
 * Agent Compiler Utility
 * Compiles YAML agent definitions into self-contained .md files
 * for improved reliability when loaded by Claude Code
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync } from 'fs';
import { join } from 'path';
import yaml from 'yaml';
import { CROAK_DIR } from '../index.js';

/**
 * Compile all agents in the project to markdown format
 * @param {Object} options - Compilation options
 * @param {string} options.outputDir - Directory to write compiled agents (default: .croak/compiled)
 * @param {boolean} options.includeKnowledge - Whether to inline knowledge files (default: true)
 * @param {boolean} options.verbose - Print verbose output (default: false)
 * @returns {Object} - Result with compiled agent paths
 */
export function compileAllAgents(options = {}) {
  const {
    outputDir = join(CROAK_DIR, 'compiled', 'agents'),
    includeKnowledge = true,
    verbose = false,
  } = options;

  const agentsDir = join(CROAK_DIR, 'agents');

  if (!existsSync(agentsDir)) {
    throw new Error('Agents directory not found. Run `croak init` first.');
  }

  // Create output directory
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  const compiledAgents = [];

  // Find all agent YAML files
  const agentFiles = findAgentFiles(agentsDir);

  for (const agentFile of agentFiles) {
    try {
      const result = compileAgent(agentFile, {
        outputDir,
        includeKnowledge,
        verbose,
      });
      compiledAgents.push(result);

      if (verbose) {
        console.log(`  Compiled: ${result.name} -> ${result.outputPath}`);
      }
    } catch (error) {
      if (verbose) {
        console.error(`  Failed to compile ${agentFile}: ${error.message}`);
      }
    }
  }

  return {
    count: compiledAgents.length,
    agents: compiledAgents,
    outputDir,
  };
}

/**
 * Compile a single agent YAML file to markdown
 * @param {string} agentPath - Path to the agent YAML file
 * @param {Object} options - Compilation options
 * @returns {Object} - Result with agent name and output path
 */
export function compileAgent(agentPath, options = {}) {
  const { outputDir = join(CROAK_DIR, 'compiled', 'agents'), includeKnowledge = true } = options;

  if (!existsSync(agentPath)) {
    throw new Error(`Agent file not found: ${agentPath}`);
  }

  // Read and parse YAML
  const yamlContent = readFileSync(agentPath, 'utf8');
  const agentDef = yaml.parse(yamlContent);

  if (!agentDef?.agent) {
    throw new Error(`Invalid agent file format: ${agentPath}`);
  }

  const agent = agentDef.agent;
  const metadata = agent.metadata || {};
  const agentName = metadata.name || agentPath.split('/').pop().replace('.agent.yaml', '');

  // Compile to markdown
  const markdown = generateAgentMarkdown(agent, { includeKnowledge, agentPath });

  // Write output
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  const outputPath = join(outputDir, `${agentName}.compiled.md`);
  writeFileSync(outputPath, markdown);

  return {
    name: agentName,
    title: metadata.title || agentName,
    outputPath,
    sourceFile: agentPath,
  };
}

/**
 * Generate markdown content from agent definition
 */
function generateAgentMarkdown(agent, options = {}) {
  const { includeKnowledge = true, agentPath = '' } = options;

  const metadata = agent.metadata || {};
  const persona = agent.persona || {};
  const capabilities = agent.capabilities || {};
  const menu = agent.menu || {};
  const criticalActions = agent.critical_actions || {};
  const guardrails = agent.guardrails || {};
  const handoffs = agent.handoffs || {};
  const knowledge = agent.knowledge || {};

  const sections = [];

  // Header
  sections.push(`# ${metadata.title || metadata.name || 'CROAK Agent'}`);
  sections.push('');
  sections.push(`> **${metadata.icon || '🤖'} ${persona.identity || 'AI Assistant'}**`);
  sections.push('');

  // Metadata
  sections.push('## Agent Metadata');
  sections.push('');
  sections.push('```yaml');
  sections.push(`id: ${metadata.id || 'unknown'}`);
  sections.push(`name: ${metadata.name || 'unknown'}`);
  sections.push(`version: ${metadata.version || '1.0'}`);
  sections.push(`agent_version: ${metadata.agent_version || '0.1.0'}`);
  sections.push('```');
  sections.push('');

  // Persona
  sections.push('## Persona');
  sections.push('');
  sections.push(`**Role:** ${persona.role || 'Assistant'}`);
  sections.push('');
  sections.push(`**Identity:** ${persona.identity || 'AI Assistant'}`);
  sections.push('');

  if (persona.communication_style) {
    sections.push('**Communication Style:**');
    sections.push('');
    if (persona.communication_style.tone) {
      sections.push(`- **Tone:** ${persona.communication_style.tone}`);
    }
    if (persona.communication_style.format) {
      sections.push(`- **Format:** ${persona.communication_style.format}`);
    }
    if (persona.communication_style.vocabulary) {
      sections.push(`- **Vocabulary:** ${persona.communication_style.vocabulary}`);
    }
    sections.push('');
  }

  if (persona.principles && persona.principles.length > 0) {
    sections.push('**Principles:**');
    sections.push('');
    persona.principles.forEach((principle) => {
      sections.push(`- ${principle}`);
    });
    sections.push('');
  }

  // Capabilities
  sections.push('## Capabilities');
  sections.push('');
  sections.push(capabilities.summary || 'This agent provides specialized assistance.');
  sections.push('');

  if (capabilities.items && capabilities.items.length > 0) {
    sections.push('### Available Capabilities');
    sections.push('');
    capabilities.items.forEach((cap) => {
      sections.push(`#### ${cap.name || cap.id}`);
      sections.push('');
      sections.push(cap.description || '');
      sections.push('');
    });
  }

  // Command Menu
  if (menu.commands && menu.commands.length > 0) {
    sections.push('## Command Menu');
    sections.push('');
    sections.push('| Command | Description | CLI |');
    sections.push('|---------|-------------|-----|');
    menu.commands.forEach((cmd) => {
      const cli = cmd.cli || '';
      const desc = cmd.description || '';
      sections.push(`| \`${cmd.trigger}\` | ${desc} | \`${cli}\` |`);
    });
    sections.push('');

    // Detailed command descriptions
    sections.push('### Command Details');
    sections.push('');
    menu.commands.forEach((cmd) => {
      sections.push(`#### \`${cmd.trigger}\``);
      sections.push('');
      sections.push(cmd.description || '');
      sections.push('');
      if (cmd.aliases && cmd.aliases.length > 0) {
        sections.push(`**Aliases:** ${cmd.aliases.join(', ')}`);
        sections.push('');
      }
      if (cmd.cli) {
        sections.push(`**CLI Command:** \`${cmd.cli}\``);
        sections.push('');
      }
      if (cmd.requires_confirmation) {
        sections.push('⚠️ **Requires user confirmation before execution**');
        sections.push('');
      }
    });
  }

  // Critical Actions
  if (criticalActions.items && criticalActions.items.length > 0) {
    sections.push('## Critical Actions');
    sections.push('');
    sections.push('> **IMPORTANT:** These rules must ALWAYS be followed.');
    sections.push('');
    criticalActions.items.forEach((action) => {
      sections.push(`### ${action.id}`);
      sections.push('');
      sections.push(`**Rule:** ${action.rule}`);
      sections.push('');
      sections.push(`**When:** ${action.when}`);
      sections.push('');
      sections.push(`**Violation:** ${action.violation}`);
      sections.push('');
    });
  }

  // Guardrails
  if (guardrails.checks && guardrails.checks.length > 0) {
    sections.push('## Guardrails');
    sections.push('');
    guardrails.checks.forEach((check) => {
      sections.push(`### ${check.name || check.id}`);
      sections.push('');
      sections.push(`**Trigger:** ${check.trigger}`);
      sections.push('');
      sections.push(`**Condition:** ${check.condition}`);
      sections.push('');
      sections.push(`**Severity:** ${check.severity}`);
      sections.push('');
      if (check.error_message) {
        sections.push(`**Error Message:** ${check.error_message}`);
        sections.push('');
      }
    });
  }

  // Handoffs
  if (handoffs.receives || handoffs.sends) {
    sections.push('## Handoffs');
    sections.push('');

    if (handoffs.receives && handoffs.receives.length > 0) {
      sections.push('### Receives');
      sections.push('');
      handoffs.receives.forEach((h) => {
        sections.push(`- **${h.type}** from ${h.from}`);
        if (h.required_fields) {
          sections.push(`  - Required fields: ${h.required_fields.join(', ')}`);
        }
      });
      sections.push('');
    }

    if (handoffs.sends && handoffs.sends.length > 0) {
      sections.push('### Sends');
      sections.push('');
      handoffs.sends.forEach((h) => {
        sections.push(`- **${h.type}** to ${h.to}`);
        if (h.trigger) {
          sections.push(`  - Trigger: ${h.trigger}`);
        }
      });
      sections.push('');
    }
  }

  // Knowledge References
  if (knowledge.files && knowledge.files.length > 0) {
    sections.push('## Knowledge Base');
    sections.push('');

    if (includeKnowledge) {
      sections.push('The following knowledge is available to this agent:');
      sections.push('');
      knowledge.files.forEach((file) => {
        sections.push(`### ${file.id}`);
        sections.push('');
        sections.push(`**Path:** \`${file.path}\``);
        sections.push('');
        sections.push(`**Description:** ${file.description || ''}`);
        sections.push('');
        sections.push(`**Load:** ${file.load}`);
        sections.push('');

        // Try to inline knowledge content
        if (file.path) {
          const knowledgePath = join(CROAK_DIR, file.path);
          if (existsSync(knowledgePath)) {
            try {
              const content = readFileSync(knowledgePath, 'utf8');
              sections.push('<details>');
              sections.push(`<summary>View ${file.id} content</summary>`);
              sections.push('');
              sections.push('```markdown');
              sections.push(content.substring(0, 2000)); // Limit inline content
              if (content.length > 2000) {
                sections.push('... (truncated)');
              }
              sections.push('```');
              sections.push('');
              sections.push('</details>');
              sections.push('');
            } catch {
              // Skip if can't read
            }
          }
        }
      });
    } else {
      sections.push('Knowledge files available:');
      sections.push('');
      knowledge.files.forEach((file) => {
        sections.push(`- \`${file.path}\` - ${file.description || file.id}`);
      });
      sections.push('');
    }
  }

  // Footer
  sections.push('---');
  sections.push('');
  sections.push(`*Compiled from: ${agentPath}*`);
  sections.push(`*Compiled at: ${new Date().toISOString()}*`);
  sections.push('');

  return sections.join('\n');
}

/**
 * Find all agent YAML files in a directory
 */
function findAgentFiles(dir) {
  const files = [];

  if (!existsSync(dir)) {
    return files;
  }

  const entries = readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);

    if (entry.isDirectory()) {
      // Look for agent file in subdirectory
      const agentFile = join(fullPath, `${entry.name}.agent.yaml`);
      if (existsSync(agentFile)) {
        files.push(agentFile);
      }
      // Also check for any .agent.yaml files
      const subFiles = readdirSync(fullPath).filter((f) => f.endsWith('.agent.yaml'));
      subFiles.forEach((f) => files.push(join(fullPath, f)));
    } else if (entry.name.endsWith('.agent.yaml')) {
      files.push(fullPath);
    }
  }

  return [...new Set(files)]; // Remove duplicates
}

/**
 * Check if compiled agents exist and are up to date
 */
export function checkCompiledAgents() {
  const compiledDir = join(CROAK_DIR, 'compiled', 'agents');
  const agentsDir = join(CROAK_DIR, 'agents');

  if (!existsSync(compiledDir)) {
    return { exists: false, count: 0, needsUpdate: true };
  }

  const compiledFiles = existsSync(compiledDir)
    ? readdirSync(compiledDir).filter((f) => f.endsWith('.compiled.md'))
    : [];

  const sourceFiles = findAgentFiles(agentsDir);

  return {
    exists: compiledFiles.length > 0,
    count: compiledFiles.length,
    sourceCount: sourceFiles.length,
    needsUpdate: compiledFiles.length !== sourceFiles.length,
    compiledDir,
  };
}
