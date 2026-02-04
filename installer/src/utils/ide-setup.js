/**
 * CROAK IDE Setup Utility
 * Handles IDE detection and command directory setup
 */

import { existsSync, mkdirSync } from 'fs';

/**
 * Supported IDE configurations
 * Claude Code uses .claude/skills/<skill-name>/SKILL.md structure
 * Each skill is a directory containing a SKILL.md file with frontmatter
 */
export const IDE_CONFIGS = {
  'claude-code': {
    name: 'Claude Code',
    skillsDir: '.claude/skills',
    commandPrefix: 'croak-',
    projectFile: 'CLAUDE.md',
    enabled: true,
  },
  cursor: {
    name: 'Cursor',
    skillsDir: '.cursor/skills',
    commandPrefix: 'croak-',
    projectFile: null,
    enabled: false, // Future support
  },
  codex: {
    name: 'Codex',
    skillsDir: '.codex/skills',
    commandPrefix: 'croak-',
    projectFile: null,
    enabled: false, // Future support
  },
};

/**
 * Get list of available IDE choices for prompts
 * @returns {Array} Array of IDE choice objects
 */
export function getIDEChoices() {
  return Object.entries(IDE_CONFIGS)
    .filter(([_, config]) => config.enabled)
    .map(([key, config]) => ({
      name: key,
      message: config.name,
      value: key,
    }));
}

/**
 * Get IDE config by key
 * @param {string} ideKey - IDE identifier
 * @returns {Object} IDE configuration
 */
export function getIDEConfig(ideKey) {
  return IDE_CONFIGS[ideKey];
}

/**
 * Detect which IDEs are likely in use based on existing directories
 * @returns {Array} Array of detected IDE keys
 */
export function detectIDEs() {
  const detected = [];

  // Check for Claude Code
  if (existsSync('.claude') || existsSync('CLAUDE.md')) {
    detected.push('claude-code');
  }

  // Check for Cursor
  if (existsSync('.cursor')) {
    detected.push('cursor');
  }

  // Check for Codex
  if (existsSync('.codex')) {
    detected.push('codex');
  }

  return detected;
}

/**
 * Create IDE skills directories
 * @param {string} ideKey - IDE identifier
 * @returns {Object} Paths to created directories
 */
export function createIDEDirectories(ideKey) {
  const config = IDE_CONFIGS[ideKey];
  if (!config) {
    throw new Error(`Unknown IDE: ${ideKey}`);
  }

  const paths = {
    base: config.skillsDir,
  };

  // Create skills directory
  if (!existsSync(config.skillsDir)) {
    mkdirSync(config.skillsDir, { recursive: true });
  }

  return paths;
}

/**
 * Check if IDE skills are already set up
 * @param {string} ideKey - IDE identifier
 * @returns {boolean} True if skills directory exists
 */
export function isIDESetup(ideKey) {
  const config = IDE_CONFIGS[ideKey];
  if (!config) return false;

  return existsSync(config.skillsDir);
}

/**
 * Get the path for the project context file
 * @param {string} ideKey - IDE identifier
 * @returns {string|null} Path to project file or null if not supported
 */
export function getProjectFilePath(ideKey) {
  const config = IDE_CONFIGS[ideKey];
  return config?.projectFile || null;
}

/**
 * Get all enabled IDEs
 * @returns {Array} Array of enabled IDE keys
 */
export function getEnabledIDEs() {
  return Object.entries(IDE_CONFIGS)
    .filter(([_, config]) => config.enabled)
    .map(([key]) => key);
}
