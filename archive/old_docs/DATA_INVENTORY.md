# AI Code Auditor - Complete Data Inventory

## 📊 Current Data Summary

### Total Dataset: **8,108 entries**

---

## 🔢 Synthetic Vulnerability Data (180 entries)

### CWE-190: Integer Overflow (50 entries) ✅

| Batch | Theme | File | Entries | Status |
|-------|-------|------|---------|--------|
| 1 | Images | `cwe190_batch1_images.json` | 10 | ✅ Exists |
| 2 | Network | `cwe190_batch2_network.json` | 20 | ✅ Created |
| 3 | Allocators | `cwe190_batch3_allocators.json` | 20 | ✅ Created |
| **4** | **Archives** | `cwe190_batch4_archives.json` | **20** | ⏳ **Pending** |
| **5** | **Crypto** | `cwe190_batch5_crypto.json` | **20** | ⏳ **Pending** |
| **6** | **Video Codecs** | `cwe190_batch6_codecs.json` | **20** | ⏳ **Pending** |
| **7** | **Kernel** | `cwe190_batch7_kernel.json` | **20** | ⏳ **Pending** |
| **8** | **Databases** | `cwe190_batch8_databases.json` | **20** | ⏳ **Pending** |

**Current:** 50 entries | **Potential:** 150 entries (+100 pending)

### CWE-416: Use After Free (130 entries) ✅

| Batch | Theme | File | Entries | Status |
|-------|-------|------|---------|--------|
| 1 | Network | `cwe416_batch1_network.json` | 20 | ✅ Valid |
| 2 | Kernel | `cwe416_batch2_kernel.json` | ? | ⚠️ Invalid JSON |
| 3 | Browser | `cwe416_batch3_browser.json` | ? | ⚠️ Invalid JSON |
| 4 | Allocators | `cwe416_batch4_allocators.json` | 20 | ✅ Valid |
| 5 | Codecs | `cwe416_batch5_codecs.json` | 20 | ✅ Valid |
| 6 | Databases | `cwe416_batch6_databases.json` | 20 | ✅ Valid |
| 7 | Crypto | `cwe416_batch7_crypto.json` | 20 | ✅ Valid |
| 8 | Graphics | `cwe416_batch8_graphics.json` | 20 | ✅ Valid |
| 9 | Bonus | `cwe416_batch9_bonus.json` | 10 | ✅ Valid |

**Total:** 130 valid entries (2 files have JSON errors)

---

## 📚 Processed Training Data

### Version 1 (4,624 entries) ✅

| Split | File | Entries |
|-------|------|---------|
| Train | `data/processed/train.jsonl` | 3,162 |
| Validation | `data/processed/val.jsonl` | 731 |
| Test | `data/processed/test.jsonl` | 731 |

**Total:** 4,624 entries

### Version 2 (3,304 entries) ✅

| Split | File | Entries |
|-------|------|---------|
| Train | `data/processed_v2/train.jsonl` | 2,137 |
| Validation | `data/processed_v2/val.jsonl` | 583 |
| Test | `data/processed_v2/test.jsonl` | 584 |

**Total:** 3,304 entries

---

## 📈 Data Breakdown

```
Total Dataset: 8,108 entries
├── Synthetic Data: 180 entries (2.2%)
│   ├── CWE-190 (Integer Overflow): 50 entries
│   └── CWE-416 (Use After Free): 130 entries
│
├── Processed v1: 4,624 entries (57.0%)
│   ├── Train: 3,162 (68.4%)
│   ├── Val: 731 (15.8%)
│   └── Test: 731 (15.8%)
│
└── Processed v2: 3,304 entries (40.8%)
    ├── Train: 2,137 (64.7%)
    ├── Val: 583 (17.6%)
    └── Test: 584 (17.7%)
```

---

## 🎯 What You Have

### ✅ **Ready to Use**
- **50 CWE-190 synthetic vulnerabilities** (Images, Network, Allocators)
- **130 CWE-416 synthetic vulnerabilities** (9 batches across various domains)
- **4,624 processed training examples (v1)** - ready for model training
- **3,304 processed training examples (v2)** - updated dataset
- **Dataset statistics** and metadata

### ⏳ **Pending (Data Provided, Not Yet Saved)**
- **100 additional CWE-190 vulnerabilities** across 5 batches:
  - Batch 4: Archives (ZIP, TAR, RAR, 7z, GZIP)
  - Batch 5: Crypto (RSA, AES, HMAC, DH, ECC)
  - Batch 6: Video Codecs (H.264, VP9, HEVC, AV1)
  - Batch 7: Kernel (Linux drivers, DMA, ioctl)
  - Batch 8: Databases (DB engines, WAL, B-trees)

### ⚠️ **Issues to Fix**
- 2 CWE-416 files have invalid JSON:
  - `cwe416_batch2_kernel.json`
  - `cwe416_batch3_browser.json`

---

## 🚀 Next Actions

### Priority 1: Complete CWE-190 Dataset
Save the 5 pending batches (100 entries) to reach 150 total CWE-190 examples.

### Priority 2: Fix CWE-416 JSON Errors
Repair the 2 invalid JSON files to ensure all CWE-416 data is usable.

### Priority 3: Integrate New Data
Run preprocessing to incorporate new synthetic data into training datasets.

---

## 📁 File Locations

### Synthetic Data
`data/synthetic/` - All raw synthetic vulnerability examples

### Processed Data
- `data/processed/` - Version 1 training data (4,624 entries)
- `data/processed_v2/` - Version 2 training data (3,304 entries)

### Models
- `models/lora_adapter/` - Version 1 fine-tuned model
- `models/lora_adapter_v2/` - Version 2 fine-tuned model

### Results
`results/` - Evaluation metrics, charts, and comparison data

---

## 💡 Key Insights

1. **Strong CWE-416 Coverage**: 130 Use-After-Free examples across 9 domains
2. **Growing CWE-190 Coverage**: 50 current, 150 potential Integer Overflow examples
3. **Dual Training Datasets**: Both v1 and v2 processed data available
4. **Production Ready**: Multiple trained models with evaluation results
5. **Expansion Ready**: Infrastructure in place to add 100 more CWE-190 examples

---

**Last Updated:** Current Session  
**Status:** 3/8 CWE-190 batches complete, 5 batches ready to save  
**Total Potential:** 8,208 entries (with pending CWE-190 data)
