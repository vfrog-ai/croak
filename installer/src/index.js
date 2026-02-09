/**
 * CROAK - Computer Recognition Orchestration Agent Kit
 * Main module exports
 */

export { initCommand } from './commands/init.js';
export { doctorCommand } from './commands/doctor.js';
export { upgradeCommand } from './commands/upgrade.js';
export { checkPython, getPythonVersion } from './utils/python-check.js';
export { copyTemplates } from './utils/template-copy.js';
export { checkVfrogCLI, checkVfrogAuth, checkVfrogContext, getVfrogConfig, getVfrogSetupHelp, syncVfrogConfig } from './utils/vfrog-setup.js';
export { getIDEChoices, createIDEDirectories, getIDEConfig, detectIDEs } from './utils/ide-setup.js';
export { generateAllCommands, generateAgentCommand, generateWorkflowCommand } from './utils/command-generator.js';
export { generateClaudeMd, hasCroakSection, updateClaudeMd } from './utils/claude-md-generator.js';
export { compileAllAgents, compileAgent, checkCompiledAgents } from './utils/agent-compiler.js';

// Version
export const VERSION = '0.2.0';

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
    cli_path: null,
    organisation_id: '',
    project_id: '',
    object_id: '',
    current_iteration_id: '',
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
    cloud_provider: 'vfrog',
    edge_format: 'tensorrt',
    precision: 'fp16',
  },
  agents: {
    verbose: true,
    auto_confirm: false,
  },
};

// Default pipeline state (matches Python PipelineState model)
export const DEFAULT_STATE = {
  version: '1.0',
  current_stage: 'uninitialized',
  stages_completed: [],
  annotation: {
    source: null,
    method: null,
    format: null,
    vfrog_iteration_id: null,
    vfrog_object_id: null,
  },
  training_state: {
    provider: null,
    architecture: null,
    experiment_id: null,
    vfrog_iteration_id: null,
  },
  deployment_state: {
    target: null,
    vfrog_api_key_env: 'VFROG_API_KEY',
  },
  artifacts: {
    dataset: null,
    model: null,
    evaluation: null,
    deployment: null,
  },
  experiments: [],
  warnings: [],
  errors: [],
  workflow_progress: {},
  workflow_artifacts: {},
  last_updated: new Date().toISOString(),
};
