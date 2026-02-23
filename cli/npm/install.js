#!/usr/bin/env node
// Downloads the correct pre-built binary for the current platform at install time

const { execSync } = require('child_process');
const { existsSync, mkdirSync, chmodSync } = require('fs');
const { join } = require('path');
const https = require('https');
const fs = require('fs');

const pkg = require('./package.json');
const version = pkg.binaryVersion || pkg.version;

const S3_BASE = 'https://runagents-releases.s3.amazonaws.com/cli';

const PLATFORM_MAP = { darwin: 'darwin', linux: 'linux', win32: 'windows' };
const ARCH_MAP = { x64: 'amd64', arm64: 'arm64' };

const platform = PLATFORM_MAP[process.platform];
const arch = ARCH_MAP[process.arch];

if (!platform || !arch) {
  console.error(`Unsupported platform: ${process.platform}/${process.arch}`);
  process.exit(1);
}

const archiveExt = platform === 'windows' ? '.zip' : '.tar.gz';
const assetName = `runagents_${platform}_${arch}${archiveExt}`;
const url = `${S3_BASE}/v${version}/${assetName}`;
const binExt = platform === 'windows' ? '.exe' : '';
const binName = `runagents-bin${binExt}`;
const BIN_DIR = join(__dirname, 'bin');
const binPath = join(BIN_DIR, binName);

if (!existsSync(BIN_DIR)) mkdirSync(BIN_DIR, { recursive: true });
if (existsSync(binPath)) { console.log('runagents already installed.'); process.exit(0); }

console.log(`Downloading runagents v${version} for ${platform}/${arch}...`);

const tmpFile = join(BIN_DIR, assetName);
const file = fs.createWriteStream(tmpFile);

const download = (url) => new Promise((resolve, reject) => {
  https.get(url, (res) => {
    if (res.statusCode === 301 || res.statusCode === 302) {
      return download(res.headers.location).then(resolve).catch(reject);
    }
    if (res.statusCode !== 200) {
      return reject(new Error(`HTTP ${res.statusCode} from ${url}`));
    }
    res.pipe(file);
    file.on('finish', () => { file.close(); resolve(); });
  }).on('error', reject);
});

download(url)
  .then(() => {
    if (archiveExt === '.tar.gz') {
      execSync(`tar -xzf "${tmpFile}" -C "${BIN_DIR}" runagents`);
      fs.renameSync(join(BIN_DIR, 'runagents'), binPath);
    } else {
      execSync(`unzip -o "${tmpFile}" runagents.exe -d "${BIN_DIR}"`);
      fs.renameSync(join(BIN_DIR, 'runagents.exe'), binPath);
    }
    fs.unlinkSync(tmpFile);
    chmodSync(binPath, 0o755);
    console.log(`runagents v${version} installed successfully.`);
  })
  .catch((err) => {
    console.error('Failed to download runagents binary:', err.message);
    console.error(`Download manually: ${url}`);
    process.exit(1);
  });
