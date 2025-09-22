#!/usr/bin/env node

// Smithery Environment Validation Script
// This script validates that all required environment variables for Smithery deployment are present

import { configSchema } from '../dist/smithery.js';

function validateSmitheryEnvironment() {
  console.log('🔍 Validating Smithery Environment Variables...\n');

  // Check for required environment variables
  const envConfig = {
    greptileApiKey: process.env.GREPTILE_API_KEY,
    githubToken: process.env.GITHUB_TOKEN,
    greptileBaseUrl: process.env.GREPTILE_BASE_URL,
    transport: process.env.TRANSPORT,
    host: process.env.HOST,
    port: process.env.PORT ? parseInt(process.env.PORT, 10) : undefined
  };

  console.log('📋 Environment Variables Status:');
  console.log(`   GREPTILE_API_KEY: ${envConfig.greptileApiKey ? '✅ SET' : '❌ MISSING'}`);
  console.log(`   GITHUB_TOKEN: ${envConfig.githubToken ? '✅ SET' : '❌ MISSING'}`);
  console.log(`   GREPTILE_BASE_URL: ${envConfig.greptileBaseUrl ? '✅ SET' : '🔧 USING DEFAULT'}`);
  console.log(`   TRANSPORT: ${envConfig.transport ? '✅ SET' : '🔧 USING DEFAULT'}`);
  console.log(`   HOST: ${envConfig.host ? '✅ SET' : '🔧 USING DEFAULT'}`);
  console.log(`   PORT: ${envConfig.port ? '✅ SET' : '🔧 USING DEFAULT'}`);

  console.log('\n🧪 Validating Configuration Schema...');

  try {
    const validatedConfig = configSchema.parse(envConfig);
    console.log('✅ SUCCESS: All required environment variables are valid!');

    console.log('\n📊 Validated Configuration:');
    console.log(`   API Key: ${validatedConfig.greptileApiKey.substring(0, 8)}...`);
    console.log(`   GitHub Token: ${validatedConfig.githubToken.substring(0, 8)}...`);
    console.log(`   Base URL: ${validatedConfig.greptileBaseUrl}`);
    console.log(`   Transport: ${validatedConfig.transport}`);
    console.log(`   Host: ${validatedConfig.host}`);
    console.log(`   Port: ${validatedConfig.port}`);

    console.log('\n🚀 Ready for Smithery deployment!');
    console.log('   Run: smithery deploy');

    return true;

  } catch (error) {
    console.log('❌ VALIDATION FAILED: Missing required environment variables');
    console.log('\n🔧 Setup Instructions:');

    if (!envConfig.greptileApiKey) {
      console.log('   1. Get your Greptile API key from: https://app.greptile.com/settings/api');
      console.log('      export GREPTILE_API_KEY="your_api_key_here"');
    }

    if (!envConfig.githubToken) {
      console.log('   2. Generate a GitHub token at: https://github.com/settings/tokens');
      console.log('      export GITHUB_TOKEN="your_github_token_here"');
    }

    console.log('\n   Optional environment variables:');
    console.log('      export GREPTILE_BASE_URL="https://api.greptile.com/v2"  # Custom API URL');
    console.log('      export TRANSPORT="stdio"                               # Transport method');
    console.log('      export HOST="0.0.0.0"                                  # Host binding');
    console.log('      export PORT="8080"                                     # Port number');

    console.log('\n   After setting environment variables, run this script again to validate.');

    return false;
  }
}

// Show help if requested
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log('Smithery Environment Validation Script');
  console.log('');
  console.log('This script validates that all required environment variables');
  console.log('for Smithery deployment are properly configured.');
  console.log('');
  console.log('Usage: node scripts/test-smithery.js');
  console.log('');
  console.log('Required Environment Variables:');
  console.log('  GREPTILE_API_KEY - Your Greptile API key');
  console.log('  GITHUB_TOKEN     - GitHub personal access token');
  console.log('');
  console.log('Optional Environment Variables:');
  console.log('  GREPTILE_BASE_URL - Custom API base URL');
  console.log('  TRANSPORT         - Transport method (stdio/sse)');
  console.log('  HOST              - Host binding');
  console.log('  PORT              - Port number');
  process.exit(0);
}

// Run validation
const isValid = validateSmitheryEnvironment();
process.exit(isValid ? 0 : 1);