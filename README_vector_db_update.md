# Vector Database Multi-Tenant Metadata Update Scripts

This directory contains scripts to update existing documents in your ChromaDB vector store with the new multi-tenant metadata fields required for the admin console RBAC functionality.

## Overview

The multi-tenant admin console requires all documents to have these metadata fields:
- `tenant_id`: Unique identifier for the tenant
- `access_roles`: List of roles that can access the document
- `document_visibility`: Visibility level (Public, Private, Restricted)

## Scripts Included

### 1. 🔍 `inspect_vector_db_metadata.py`
**Purpose**: Analyze your current vector database to see what metadata exists

**Usage**:
```bash
# Quick overview
python inspect_vector_db_metadata.py

# Show field examples
python inspect_vector_db_metadata.py --show_examples

# Analyze more documents (or all with --sample_size 0)
python inspect_vector_db_metadata.py --sample_size 20 --show_examples

# Show sample documents with full metadata
python inspect_vector_db_metadata.py --show_sample_docs
```

### 2. 💾 `backup_vector_db.py`
**Purpose**: Create a backup of your vector database before making changes

**Usage**:
```bash
# Create backup with auto-generated filename
python backup_vector_db.py

# Create backup with custom filename
python backup_vector_db.py --output_file my_backup_2025_01_15.json
```

### 3. 🔧 `update_existing_docs_metadata.py`
**Purpose**: Update existing documents with multi-tenant metadata

**Usage**:
```bash
# ALWAYS do a dry run first to see what would change
python update_existing_docs_metadata.py \
  --tenant_id "your_tenant_id" \
  --access_role "customer" \
  --dry_run

# Apply the updates (remove --dry_run)
python update_existing_docs_metadata.py \
  --tenant_id "your_tenant_id" \
  --access_role "customer"

# With custom document visibility
python update_existing_docs_metadata.py \
  --tenant_id "acme_corp" \
  --access_role "vendor" \
  --document_visibility "Private"
```

## Step-by-Step Update Process

### Step 1: Inspect Your Current Database
```bash
python inspect_vector_db_metadata.py --show_examples
```

This will show you:
- How many documents you have
- Which documents already have tenant metadata
- What metadata fields currently exist

### Step 2: Create a Backup
```bash
python backup_vector_db.py
```

This creates a JSON backup file that you can use to restore your database if needed.

### Step 3: Test the Update (Dry Run)
```bash
python update_existing_docs_metadata.py \
  --tenant_id "your_company" \
  --access_role "customer" \
  --dry_run
```

This shows you exactly what would be changed without making any actual changes.

### Step 4: Apply the Updates
```bash
python update_existing_docs_metadata.py \
  --tenant_id "your_company" \
  --access_role "customer"
```

### Step 5: Verify the Updates
```bash
python inspect_vector_db_metadata.py
```

Check that all documents now have the required tenant metadata fields.

## Parameter Options

### Tenant ID (`--tenant_id`)
- **Required**: Yes
- **Example**: `"rentomojo_main"`, `"acme_corp"`, `"client_123"`
- **Description**: Unique identifier for your tenant/organization

### Access Role (`--access_role`)
- **Required**: Yes
- **Options**: `customer`, `vendor`, `associate`, `leadership`, `hr`
- **Description**: The role that will have access to all existing documents

### Document Visibility (`--document_visibility`)
- **Required**: No (default: `Public`)
- **Options**: `Public`, `Private`, `Restricted`
- **Description**: Visibility level for all existing documents

## Example Scenarios

### Scenario 1: Company with Customer Documents
```bash
# All existing docs are customer-facing and public
python update_existing_docs_metadata.py \
  --tenant_id "rentomojo_prod" \
  --access_role "customer" \
  --document_visibility "Public"
```

### Scenario 2: Internal Company Documents
```bash
# All existing docs are internal and restricted
python update_existing_docs_metadata.py \
  --tenant_id "internal_ops" \
  --access_role "associate" \
  --document_visibility "Restricted"
```

### Scenario 3: Vendor-Specific Documents
```bash
# All existing docs are for vendors
python update_existing_docs_metadata.py \
  --tenant_id "vendor_portal" \
  --access_role "vendor" \
  --document_visibility "Private"
```

## Safety Features

### ✅ Dry Run Mode
Always test with `--dry_run` first to see what would change

### ✅ Input Validation
- Validates tenant_id is not empty
- Validates access_role is a valid enum value
- Validates document_visibility is a valid enum value

### ✅ Update Verification
After updates, the script automatically verifies a sample of documents to ensure changes were applied correctly

### ✅ Detailed Logging
All operations are logged with clear status messages and progress indicators

### ✅ Backup Support
Easy backup creation to restore if needed

## Troubleshooting

### Issue: "No documents found"
**Cause**: Vector database is empty or connection issue
**Solution**: Check that your vector store has documents and ChromaDB is accessible

### Issue: "Invalid access role"
**Cause**: Typo in role name
**Solution**: Use exact values: `customer`, `vendor`, `associate`, `leadership`, `hr`

### Issue: "Update verification failed"
**Cause**: ChromaDB write issue or connection problem
**Solution**: Check ChromaDB logs and try again. Use backup to restore if needed

### Issue: Script hangs or is slow
**Cause**: Large number of documents
**Solution**: This is normal for large databases. The script processes in batches for efficiency

## Recovery

If you need to restore from backup:

1. The backup file contains all document IDs, content, metadata, and embeddings
2. You can write a custom restoration script using the backup JSON file
3. Contact support if you need help with restoration

## Support

For issues with these scripts:
1. Check the logs (increase verbosity with `--log_level DEBUG`)
2. Ensure all dependencies are installed
3. Verify ChromaDB connection and permissions
4. Create an issue in the project repository

---

**⚠️ Important**: Always create a backup before running updates on production data!