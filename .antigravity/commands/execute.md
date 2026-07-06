# Execute Code Changes Command

This command dictates how to apply code changes using the chunked-replace tools.

## Rules for Editing Code

1. Use `replace_file_content` for editing a single contiguous block of code.
2. Use `multi_replace_file_content` for editing multiple, non-adjacent blocks of code in a single file.
3. NEVER overwrite a whole file unless it is a newly created file.
4. Verify code changes by running tests or compilation checks after each change.
