# Session ID Format Fixes

This document summarizes the improvements made to session ID generation and validation in the Greptile MCP server.

## 🎯 Issues Fixed

### 1. **Inconsistent Session ID Generation**
- **Before**: Direct usage of `str(uuid.uuid4())` in multiple places
- **After**: Centralized `generate_session_id()` function used everywhere

### 2. **Case Sensitivity Issues**
- **Before**: Mixed case UUIDs could cause validation issues
- **After**: All session IDs normalized to lowercase for consistency

### 3. **Validation Inconsistencies**
- **Before**: Case-sensitive UUID validation
- **After**: Case-insensitive validation with proper normalization

### 4. **No Input Normalization**
- **Before**: Raw session IDs passed through without normalization
- **After**: `normalize_session_id()` function handles whitespace and case

## 🔧 Implementation Details

### Enhanced Functions

#### `generate_session_id()`
```python
def generate_session_id() -> str:
    """
    Generate a new unique session ID in proper UUID format.
    
    Returns:
        str: A properly formatted UUID string (e.g., '12345678-1234-1234-1234-123456789abc')
    """
    session_id = str(uuid.uuid4())
    # Ensure it's in lowercase for consistency
    return session_id.lower()
```

#### `normalize_session_id()`
```python
def normalize_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    Normalize a session ID to ensure consistent format.
    
    Args:
        session_id: The session ID to normalize
        
    Returns:
        str: Normalized session ID in lowercase, or None if input was None
    """
    if session_id is None:
        return None
    return session_id.lower().strip()
```

### Updated Validation

#### Enhanced UUID Pattern
```python
# Before: Only lowercase
SESSION_ID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

# After: Case-insensitive
SESSION_ID_PATTERN = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
```

#### Enhanced Validation Logic
```python
def validate_session_id(session_id: Optional[str]) -> ValidationResult:
    """Validate session ID format."""
    result = ValidationResult(True, [], [])
    
    if session_id is None:
        return result  # Optional field
    
    if not isinstance(session_id, str):
        result.add_error(f"Session ID must be a string, got {type(session_id).__name__}")
        return result
    
    # Normalize the session ID for validation (trim whitespace, normalize case)
    normalized_session_id = session_id.strip()
    
    if not InputValidator.SESSION_ID_PATTERN.match(normalized_session_id):
        result.add_error(
            f"Session ID must be a valid UUID format (e.g., '12345678-1234-1234-1234-123456789abc'). "
            f"Got: '{session_id}'"
        )
    
    return result
```

### Updated Usage in Main Functions

#### Before
```python
# Generate session ID if not provided
if session_id is None:
    session_id = str(uuid.uuid4())
    logger.debug(f"Generated new session ID: {session_id}")
```

#### After
```python
# Normalize and generate session ID if not provided
session_id = normalize_session_id(session_id)
if session_id is None:
    session_id = generate_session_id()
    logger.debug(f"Generated new session ID: {session_id}")
```

## ✅ Test Results

### Session ID Generation
- ✅ All generated UUIDs are in proper format
- ✅ All generated UUIDs are lowercase
- ✅ All generated UUIDs are unique
- ✅ Generated UUIDs pass validation

### Session ID Normalization
- ✅ Lowercase UUIDs pass through unchanged
- ✅ Uppercase UUIDs converted to lowercase
- ✅ Whitespace is trimmed properly
- ✅ None values handled correctly

### Session ID Validation
- ✅ Valid lowercase UUIDs accepted
- ✅ Valid uppercase UUIDs accepted
- ✅ UUIDs with whitespace accepted after normalization
- ✅ Invalid formats properly rejected
- ✅ Non-string types properly rejected
- ✅ None values accepted (optional parameter)

### Integration Testing
- ✅ Generated IDs pass validation
- ✅ All existing tests still pass
- ✅ Session lifecycle management works correctly

## 📊 Benefits

### 1. **Consistency**
- All session IDs are now consistently formatted
- Predictable behavior across all functions
- No more mixed case issues

### 2. **Robustness**
- Proper input validation and normalization
- Better error messages for invalid formats
- Handles edge cases gracefully

### 3. **User Experience**
- Users can provide session IDs in any case
- Whitespace is automatically handled
- Clear error messages for invalid formats

### 4. **Maintainability**
- Centralized session ID generation
- Single source of truth for UUID format
- Easier to modify format if needed

## 🚀 Usage Examples

### Generate New Session ID
```python
from src.utils import generate_session_id

session_id = generate_session_id()
print(session_id)  # Output: "12345678-1234-1234-1234-123456789abc"
```

### Normalize Existing Session ID
```python
from src.utils import normalize_session_id

# Handles various input formats
normalized = normalize_session_id("  12345678-1234-1234-1234-123456789ABC  ")
print(normalized)  # Output: "12345678-1234-1234-1234-123456789abc"
```

### Validate Session ID
```python
from src.validation import InputValidator

result = InputValidator.validate_session_id("12345678-1234-1234-1234-123456789abc")
print(result.is_valid)  # Output: True
```

### MCP Tool Usage
```python
# All these formats are now handled correctly:
result = await query_repository(
    query="What is this about?",
    repositories='[{"remote": "github", "repository": "owner/repo", "branch": "main"}]',
    session_id="12345678-1234-1234-1234-123456789ABC"  # Uppercase OK
)

result = await query_repository(
    query="Follow up question",
    repositories='[{"remote": "github", "repository": "owner/repo", "branch": "main"}]',
    session_id="  12345678-1234-1234-1234-123456789abc  "  # Whitespace OK
)
```

## 🔄 Migration Notes

### For Existing Code
- No breaking changes - all existing code continues to work
- Session IDs will be automatically normalized
- Generated session IDs are now consistently lowercase

### For New Development
- Use `generate_session_id()` for new session IDs
- Use `normalize_session_id()` when processing user input
- Validation is more robust and user-friendly

## 🧪 Test Coverage

The following test cases are now covered:
- Session ID generation uniqueness and format
- Normalization of various input formats
- Validation of valid and invalid session IDs
- Integration with existing MCP tools
- Edge cases and error handling

All tests pass, confirming the fixes work correctly and don't break existing functionality.

---

**Status**: ✅ Complete - Session ID handling is now robust, consistent, and user-friendly!