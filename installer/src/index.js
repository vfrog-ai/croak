/**
 * CROAK - Computer Recognition Orchestration Agent Kit
 * Main module exports
 */

export { initCommand } from './commands/init.js';
export { doctorCommand } from './commands/doctor.js';
export { upgradeCommand } from './commands/upgrade.js';
export { checkPython, getPythonVersion } from './utils/python-check.js';
export { copyTemplates } from './utils/template-copy.js';
export { setupVfrog } from './utils/vfrog-setup.js';
export { getIDEChoices, createIDEDirectories, getIDEConfig, detectIDEs } from './utils/ide-setup.js';
export { generateAllCommands, generateAgentCommand, generateWorkflowCommand } from './utils/command-generator.js';
export { generateClaudeMd, hasCroakSection, updateClaudeMd } from './utils/claude-md-generator.js';
export { compileAllAgents, compileAgent, checkCompiledAgents } from './utils/agent-compiler.js';

// Version
export const VERSION = '0.1.0';

// Constants
export const CROAK_DIR = '.croak';
export const CONFIG_FILE = 'config.yaml';
export const STATE_FILE = 'pipeline-state.yaml';

// Default configuration
export const DEFAULT_CONFIG = {
  version: '1.0',
  project: {
    name: '',
    task_type: 'detection',
    created_at: new Date().toISOString(),
  },
  vfrog: {
    api_key_env: 'VFROG_API_KEY',
    project_id: '',
  },
  compute: {
    provider: 'modal',
    gpu_type: 'T4',
    timeout_hours: 4,
  },
  training: {
    framework: 'ultralytics',
    architecture: 'yolov8s',
    epochs: 100,
    batch_size: 16,
    image_size: 640,
    patience: 20,
  },
  tracking: {
    backend: 'mlflow',
    mlflow: {
      tracking_uri: './mlruns',
    },
  },
  data: {
    format: 'yolo',
    splits: {
      train: 0.8,
      val: 0.15,
      test: 0.05,
    },
  },
  deployment: {
    cloud: {
      provider: 'vfrog',
      auto_scaling: true,
      min_replicas: 1,
      max_replicas: 5,
    },
    edge: {
      format: 'tensorrt',
      precision: 'fp16',
    },
  },
  agents: {
    verbose: true,
    auto_confirm: false,
  },
};

// Default pipeline state
export const DEFAULT_STATE = {
  version: '1.0',
  current_stage: 'uninitialized',
  stages_completed: [],
  experiments: [],
  warnings: [],
  artifacts: {
    dataset: null,
    training: null,
    evaluation: null,
    deployment: null,
  },
  last_updated: new Date().toISOString(),
};
