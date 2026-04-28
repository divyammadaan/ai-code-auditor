# CWE-190 Synthetic Data Batches Summary

## Completed Batches

### ✅ Batch 1: Images (Already existed)
- **File**: `data/synthetic/cwe190_batch1_images.json`
- **CVE Range**: CVE-2023-SYNTH-201 to CVE-2023-SYNTH-220
- **Theme**: Image processing (PNG, JPEG, BMP, GIF, TIFF)
- **Count**: 20 entries

### ✅ Batch 2: Network Protocols  
- **File**: `data/synthetic/cwe190_batch2_network.json`
- **CVE Range**: CVE-2023-SYNTH-221 to CVE-2023-SYNTH-240
- **Theme**: TCP, UDP, HTTP, DNS, TLS, WebSocket, IP, RPC
- **Count**: 20 entries
- **Status**: ✓ Saved

### ✅ Batch 3: Memory Allocators
- **File**: `data/synthetic/cwe190_batch3_allocators.json`
- **CVE Range**: CVE-2023-SYNTH-241 to CVE-2023-SYNTH-260
- **Theme**: calloc, realloc, malloc, pool allocators, arena allocators
- **Count**: 20 entries
- **Status**: ✓ Saved

## Remaining Batches (To Be Added)

### ⏳ Batch 4: Archive Formats
- **Target File**: `data/synthetic/cwe190_batch4_archives.json`
- **CVE Range**: CVE-2023-SYNTH-261 to CVE-2023-SYNTH-280
- **Theme**: ZIP, TAR, RAR, 7z, GZIP processing
- **Count**: 20 entries
- **Vulnerabilities Include**:
  - ZIP entry processing overflows
  - TAR header parsing issues
  - GZIP buffer allocation errors
  - 7z stream processing vulnerabilities
  - RAR volume seeking problems

### ⏳ Batch 5: Cryptographic Operations
- **Target File**: `data/synthetic/cwe190_batch5_crypto.json`
- **CVE Range**: CVE-2023-SYNTH-281 to CVE-2023-SYNTH-300
- **Theme**: RSA, AES, HMAC, DH, ECC, PKCS, key management
- **Count**: 20 entries
- **Vulnerabilities Include**:
  - RSA modulus buffer allocation
  - AES block encryption overflows
  - HMAC tag processing
  - Diffie-Hellman parameter generation
  - PKCS padding operations
  - Key derivation functions
  - Signature buffer calculations

## Total Statistics

- **Total Batches**: 5
- **Completed**: 3 (60%)
- **Remaining**: 2 (40%)
- **Total Entries**: 100 (60 saved, 40 pending)

## Next Steps

To complete the dataset:

1. **Create Batch 4 file**: Copy the archive-related vulnerabilities (CVE-2023-SYNTH-261 to 280) into a JSON array
2. **Create Batch 5 file**: Copy the crypto-related vulnerabilities (CVE-2023-SYNTH-281 to 300) into a JSON array
3. **Validate format**: Ensure each entry has all required fields (cwe, cve_id, cvss_score, vulnerable_code, secure_code, explanation)
4. **Update training data**: Run preprocessing scripts to incorporate new batches into the training dataset

## File Locations

All synthetic data files are stored in: `data/synthetic/`

Current CWE-190 files:
- cwe190_batch1_images.json (20 entries)
- cwe190_batch2_network.json (20 entries)  
- cwe190_batch3_allocators.json (20 entries)
- cwe190_batch4_archives.json (pending)
- cwe190_batch5_crypto.json (pending)
