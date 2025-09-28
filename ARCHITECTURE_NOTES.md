# Architecture Notes

## Code Quality Concerns

### HIGH Priority: Code Duplication Issue

**Problem**: The files `src/smithery.ts` and `src/index.ts` contain significant duplication:
- Similar MCP server initialization logic
- Duplicate tool registration (but using different APIs: `.tool()` vs `.registerTool()`)
- Nearly identical configuration schemas
- Same imports and client setup

**Impact**:
- Maintenance burden - changes must be made in multiple places
- Risk of divergence and bugs
- Confusion about which file to modify
- Inconsistent API usage patterns

**Recommended Solution** (Future Work):
```typescript
// Create src/server-factory.ts
export function createMcpServer(config: ServerConfig, apiStyle: 'modern' | 'legacy' = 'modern') {
  // Single source of truth for server creation
  // Conditionally use .tool() or .registerTool() based on apiStyle
}

// Then simplify both entry points:
// src/smithery.ts -> uses createMcpServer(config, 'modern')
// src/index.ts -> uses createMcpServer(config, 'legacy')
```

**Current Mitigation**:
- Configuration schemas have been standardized to use the same validation rules
- Both files now export their config types for external use
- Terminal compatibility improved by removing emojis

### Technical Debt Items

1. **API Inconsistency**: Standardize on either `.tool()` or `.registerTool()` pattern
2. **Configuration Validation**: Add runtime validation helpers with user-friendly error messages
3. **Type Safety**: Consider extracting common interfaces for server configuration
4. **Testing**: Add unit tests for configuration validation logic

### Immediate Fixes Applied (2024-01-28)

✅ **Fixed**: Removed emoji characters that could cause terminal compatibility issues
✅ **Fixed**: Standardized configuration validation between smithery.ts and index.ts
✅ **Fixed**: Added explicit exports for configuration types
✅ **Fixed**: Replaced 'any' type with proper StreamingChunk interface

### Next Steps

1. **Short-term**: Monitor for any issues with the standardized configuration
2. **Medium-term**: Create comprehensive unit tests for configuration validation
3. **Long-term**: Refactor to eliminate code duplication with server-factory pattern