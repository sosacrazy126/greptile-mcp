#!/usr/bin/env node

// Test script to verify configSchema export for Smithery

console.log('Testing configSchema export...\n');

try {
  // Test importing from the built file
  const { configSchema, default: createServer } = await import('./dist/index.js');

  console.log('✅ Successfully imported from ./dist/index.js');

  // Check if configSchema exists
  if (configSchema) {
    console.log('✅ configSchema is exported');
    console.log('📋 configSchema type:', typeof configSchema);

    // Check if it's a Zod schema
    if (configSchema._def) {
      console.log('✅ configSchema appears to be a Zod schema');

      // Try to get schema shape
      const shape = configSchema.shape;
      if (shape) {
        console.log('✅ Schema shape available');
        console.log('🔧 Available fields:', Object.keys(shape));

        // Test each field for descriptions
        for (const [key, field] of Object.entries(shape)) {
          const description = field.description || field._def?.description;
          console.log(`   - ${key}: ${description || 'No description'}`);
        }
      }
    }
  } else {
    console.log('❌ configSchema is not exported');
  }

  // Check if createServer exists
  if (createServer) {
    console.log('✅ createServer (default export) is available');
    console.log('📋 createServer type:', typeof createServer);
  } else {
    console.log('❌ createServer (default export) is missing');
  }

  console.log('\n🎯 Export test completed successfully!');

} catch (error) {
  console.error('❌ Error testing exports:', error.message);
  process.exit(1);
}