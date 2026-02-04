/**
 * CROAK IDE Setup Utility
 * Handles IDE detection and command directory setup
 */

import { existsSync, mkdirSync } from 'fs';

/**
 * Supported IDE configurations
 * Note: Claude Code discovers commands directly in .claude/commands/ (not subdirectories)
 * Command files are named with full command name: croak-router.md, croak-data.md, etc.
 */
export const IDE_CONFIGS = {
  'claude-code': {
    name: 'Claude Code',
    commandDir: '.claude/commands',
    commandPrefix: 'croak-',
    projectFile: 'CLAUDE.md',
    enabled: true,
  },
  cursor: {
    name: 'Cursor',
    commandDir: '.cursor/commands',
    commandPrefix: 'croak-',
    projectFile: null,
    enabled: false, // Future support
  },
  codex: {
    name: 'Codex',
    commandDir: '.codex/commands',
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
 * Create IDE command directories
 * @param {string} ideKey - IDE identifier
 * @returns {Object} Paths to created directories
 */
export function createIDEDirectories(ideKey) {
  const config = IDE_CONFIGS[ideKey];
  if (!config) {
    throw new Error(`Unknown IDE: ${ideKey}`);
  }

  const paths = {
    base: config.commandDir,
  };

  // Create command directory
  if (!existsSync(config.commandDir)) {
    mkdirSync(config.commandDir, { recursive: true });
  }

  return paths;
}

/**
 * Check if IDE commands are already set up
 * @param {string} ideKey - IDE identifier
 * @returns {boolean} True if commands directory exists
 */
export function isIDESetup(ideKey) {
  const config = IDE_CONFIGS[ideKey];
  if (!config) return false;

  return existsSync(config.commandDir);
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
