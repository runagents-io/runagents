#!/usr/bin/env node
// Downloads the correct pre-built binary for the current platform at install time

const { execFileSync } = require('child_process');
const { existsSync, mkdirSync, chmodSync } = require('fs');
const { join } = require('path');
const https = require('https');
const crypto = require('crypto');
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
const checksumsURL = `${S3_BASE}/v${version}/checksums.txt`;
const binExt = platform === 'windows' ? '.exe' : '';
const binName = `runagents-bin${binExt}`;
const BIN_DIR = join(__dirname, 'bin');
const binPath = join(BIN_DIR, binName);

if (!existsSync(BIN_DIR)) mkdirSync(BIN_DIR, { recursive: true });
if (existsSync(binPath)) { console.log('runagents already installed.'); process.exit(0); }

console.log(`Downloading runagents v${version} for ${platform}/${arch}...`);

const tmpFile = join(BIN_DIR, assetName);
const maxRedirects = 5;

const downloadFile = (downloadURL, destination, redirects = 0) => new Promise((resolve, reject) => {
  https.get(downloadURL, (res) => {
    if ((res.statusCode === 301 || res.statusCode === 302) && res.headers.location) {
      if (redirects >= maxRedirects) {
        return reject(new Error(`Too many redirects while downloading ${downloadURL}`));
      }
      return downloadFile(res.headers.location, destination, redirects + 1).then(resolve).catch(reject);
    }
    if (res.statusCode !== 200) {
      return reject(new Error(`HTTP ${res.statusCode} from ${downloadURL}`));
    }
    const output = fs.createWriteStream(destination);
    res.pipe(output);
    output.on('finish', () => {
      output.close();
      resolve();
    });
    output.on('error', reject);
  }).on('error', reject);
});

const downloadText = (requestURL, redirects = 0) => new Promise((resolve, reject) => {
  https.get(requestURL, (res) => {
    if ((res.statusCode === 301 || res.statusCode === 302) && res.headers.location) {
      if (redirects >= maxRedirects) {
        return reject(new Error(`Too many redirects while requesting ${requestURL}`));
      }
      return downloadText(res.headers.location, redirects + 1).then(resolve).catch(reject);
    }
    if (res.statusCode !== 200) {
      return reject(new Error(`HTTP ${res.statusCode} from ${requestURL}`));
    }
    const chunks = [];
    res.on('data', (chunk) => chunks.push(chunk));
    res.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
  }).on('error', reject);
});

const lookupChecksum = (checksumsText, expectedAsset) => {
  const lines = checksumsText.split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const parts = trimmed.split(/\s+/);
    if (parts.length < 2) continue;
    const digest = parts[0].toLowerCase();
    const name = parts[1].replace(/^[*.\/]+/, '');
    if (name === expectedAsset) {
      return digest;
    }
  }
  return '';
};

const fileSHA256 = (path) => {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(path));
  return hash.digest('hex');
};

Promise.all([downloadFile(url, tmpFile), downloadText(checksumsURL)])
  .then(([, checksums]) => {
    const expectedChecksum = lookupChecksum(checksums, assetName);
    if (!expectedChecksum) {
      throw new Error(`Missing checksum entry for ${assetName}`);
    }
    const actualChecksum = fileSHA256(tmpFile);
    if (actualChecksum !== expectedChecksum) {
      throw new Error(`Checksum mismatch for ${assetName}`);
    }

    if (archiveExt === '.tar.gz') {
      execFileSync('tar', ['-xzf', tmpFile, '-C', BIN_DIR, 'runagents'], { stdio: 'inherit' });
      fs.renameSync(join(BIN_DIR, 'runagents'), binPath);
    } else {
      execFileSync('unzip', ['-o', tmpFile, 'runagents.exe', '-d', BIN_DIR], { stdio: 'inherit' });
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
