#!/usr/bin/env node
'use strict';

const { spawnSync, execSync } = require('child_process');
const { join } = require('path');
const { existsSync } = require('fs');

const platform =
  process.platform === 'win32'
    ? 'windows'
    : process.platform === 'darwin'
      ? 'darwin'
      : 'linux';
const ext = platform === 'windows' ? '.exe' : '';
const binPath = join(__dirname, `runagents-bin${ext}`);

// Download the native CLI lazily so npm installs stay small.
if (!existsSync(binPath)) {
  try {
    execSync(`node "${join(__dirname, '..', 'install.js')}"`, { stdio: 'inherit' });
  } catch (e) {
    process.stderr.write('Failed to download runagents binary. Install manually:\n');
    process.stderr.write('  curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh\n');
    process.exit(1);
  }
}

const result = spawnSync(binPath, process.argv.slice(2), { stdio: 'inherit' });
process.exit(result.status ?? 1);
