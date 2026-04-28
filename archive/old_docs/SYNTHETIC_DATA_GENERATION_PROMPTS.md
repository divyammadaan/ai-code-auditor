# Synthetic Data Generation Prompts

## 📊 **Analysis Summary**

After saving batches 4-8, you'll have:
- ✅ CWE-190: Well-balanced (295 samples)
- ✅ CWE-416: Well-balanced (270 samples)
- ⚠️ **CWE-189: Still low (109 samples)** - Need +132
- ⚠️ **CWE-362: Still low (114 samples)** - Need +127

---

## 🎯 **Priority 1: CWE-189 (Numeric Errors)**

**Current:** 109 samples  
**Target:** 240 samples  
**Need:** +130 samples (6-7 batches of 20)

### **Batch 9: CWE-189 - Integer Truncation & Sign Conversion**

```
Generate 20 CWE-189 (Numeric Error) synthetic vulnerabilities focusing on integer truncation and sign conversion issues. Include:

1. Integer truncation (64-bit to 32-bit, 32-bit to 16-bit, 16-bit to 8-bit)
2. Sign conversion errors (signed to unsigned, unsigned to signed)
3. Type casting issues in arithmetic operations
4. Loss of precision in floating-point conversions
5. Implicit type conversions in function arguments
6. Mixed-type arithmetic (int + unsigned, short + long)
7. Bitfield truncation
8. Enum value overflow
9. Character encoding conversions
10. Size_t to int conversions

Domains: File I/O, network protocols, memory allocation, array indexing, loop counters

Format: JSON array with:
- cwe: "CWE-189"
- cve_id: "CVE-2023-SYNTH-361" to "CVE-2023-SYNTH-380"
- cvss_score: "6.5" to "8.5"
- vulnerable_code: C/C++ code with numeric error
- secure_code: Fixed version with proper type handling
- explanation: Detailed explanation of the numeric error and its security impact

Each example should be 10-30 lines of realistic C/C++ code.
```

### **Batch 10: CWE-189 - Wraparound & Boundary Conditions**

```
Generate 20 CWE-189 (Numeric Error) synthetic vulnerabilities focusing on wraparound and boundary conditions. Include:

1. Counter wraparound (loop counters, timestamps, sequence numbers)
2. Boundary condition errors (off-by-one in type limits)
3. Modulo arithmetic errors
4. Negative number handling
5. Zero-crossing issues
6. Maximum value assumptions
7. Minimum value assumptions
8. Range validation failures
9. Comparison operator errors with mixed types
10. Increment/decrement boundary issues

Domains: Timers, counters, pagination, indexing, state machines, protocol sequence numbers

Format: JSON array with:
- cwe: "CWE-189"
- cve_id: "CVE-2023-SYNTH-381" to "CVE-2023-SYNTH-400"
- cvss_score: "6.5" to "8.5"
- vulnerable_code: C/C++ code with wraparound/boundary error
- secure_code: Fixed version with proper boundary checks
- explanation: Detailed explanation of the error and security impact

Each example should be 10-30 lines of realistic C/C++ code.
```

### **Batch 11: CWE-189 - Floating Point & Precision Loss**

```
Generate 20 CWE-189 (Numeric Error) synthetic vulnerabilities focusing on floating-point and precision loss issues. Include:

1. Float to integer conversions
2. Double to float precision loss
3. Rounding errors in security calculations
4. Comparison of floating-point values
5. Accumulation errors in loops
6. Division by near-zero values
7. Denormalized number handling
8. NaN and infinity propagation
9. Fixed-point arithmetic errors
10. Currency/financial calculation precision

Domains: Financial systems, scientific computing, graphics, physics engines, cryptographic timing

Format: JSON array with:
- cwe: "CWE-189"
- cve_id: "CVE-2023-SYNTH-401" to "CVE-2023-SYNTH-420"
- cvss_score: "6.5" to "8.5"
- vulnerable_code: C/C++ code with precision/floating-point error
- secure_code: Fixed version with proper precision handling
- explanation: Detailed explanation of the precision error and security impact

Each example should be 10-30 lines of realistic C/C++ code.
```

---

## 🎯 **Priority 2: CWE-362 (Race Conditions)**

**Current:** 114 samples  
**Target:** 240 samples  
**Need:** +126 samples (6-7 batches of 20)

### **Batch 12: CWE-362 - TOCTOU (Time-of-Check Time-of-Use)**

```
Generate 20 CWE-362 (Race Condition) synthetic vulnerabilities focusing on TOCTOU issues. Include:

1. File access TOCTOU (check existence, then open)
2. Permission check TOCTOU
3. Symbolic link TOCTOU
4. Directory traversal TOCTOU
5. Resource availability TOCTOU
6. Authentication state TOCTOU
7. Configuration file TOCTOU
8. Temporary file TOCTOU
9. Lock file TOCTOU
10. Shared memory TOCTOU

Domains: File systems, authentication, privilege escalation, resource management

Format: JSON array with:
- cwe: "CWE-362"
- cve_id: "CVE-2023-SYNTH-421" to "CVE-2023-SYNTH-440"
- cvss_score: "7.0" to "8.8"
- vulnerable_code: C/C++ code with TOCTOU vulnerability
- secure_code: Fixed version with atomic operations or proper locking
- explanation: Detailed explanation of the race window and security impact

Each example should be 15-35 lines of realistic C/C++ code.
```

### **Batch 13: CWE-362 - Shared Resource Race Conditions**

```
Generate 20 CWE-362 (Race Condition) synthetic vulnerabilities focusing on shared resource races. Include:

1. Global variable races (multiple threads)
2. Static variable races
3. Shared buffer races
4. Reference counter races
5. Flag/state variable races
6. Linked list races (insert/delete)
7. Hash table races
8. Queue races (producer-consumer)
9. Cache coherency races
10. Memory-mapped file races

Domains: Multi-threaded applications, concurrent data structures, caching systems

Format: JSON array with:
- cwe: "CWE-362"
- cve_id: "CVE-2023-SYNTH-441" to "CVE-2023-SYNTH-460"
- cvss_score: "7.0" to "8.8"
- vulnerable_code: C/C++ code with shared resource race
- secure_code: Fixed version with mutexes, atomic operations, or lock-free algorithms
- explanation: Detailed explanation of the race condition and security impact

Each example should be 15-35 lines of realistic C/C++ code with pthread or C++11 threading.
```

### **Batch 14: CWE-362 - Signal Handler & Async Races**

```
Generate 20 CWE-362 (Race Condition) synthetic vulnerabilities focusing on signal handlers and asynchronous races. Include:

1. Signal handler races (non-reentrant functions)
2. Async signal-unsafe function calls
3. Signal handler data corruption
4. Interrupt handler races
5. Callback function races
6. Event handler races
7. Timer callback races
8. I/O completion races
9. Deferred work races
10. Async I/O races

Domains: Signal handling, interrupt handlers, event-driven systems, async I/O

Format: JSON array with:
- cwe: "CWE-362"
- cve_id: "CVE-2023-SYNTH-461" to "CVE-2023-SYNTH-480"
- cvss_score: "7.0" to "8.8"
- vulnerable_code: C/C++ code with signal/async race
- secure_code: Fixed version with signal-safe functions or proper synchronization
- explanation: Detailed explanation of the async race and security impact

Each example should be 15-35 lines of realistic C/C++ code with signal handling.
```

---

## 📋 **Optional: Additional CWEs for Perfect Balance**

### **Batch 15: CWE-125 - Out-of-Bounds Read**

```
Generate 20 CWE-125 (Out-of-Bounds Read) synthetic vulnerabilities. Include:

1. Array index out of bounds (positive overflow)
2. Negative array index
3. Buffer underflow reads
4. String length miscalculation
5. Pointer arithmetic errors
6. Structure member access beyond bounds
7. Vector/array access without bounds check
8. Loop boundary errors
9. Slice/substring errors
10. Memory-mapped region reads

Domains: Parsers, serialization, data processing, string handling

Format: JSON array with:
- cwe: "CWE-125"
- cve_id: "CVE-2023-SYNTH-481" to "CVE-2023-SYNTH-500"
- cvss_score: "6.5" to "8.0"
- vulnerable_code: C/C++ code with OOB read
- secure_code: Fixed version with bounds checking
- explanation: Detailed explanation of the OOB read and information disclosure risk

Each example should be 10-30 lines of realistic C/C++ code.
```

### **Batch 16: CWE-200 - Information Exposure**

```
Generate 20 CWE-200 (Information Exposure) synthetic vulnerabilities. Include:

1. Error message information leakage
2. Debug output in production
3. Stack trace exposure
4. Memory dump exposure
5. Log file sensitive data
6. Timing side-channels
7. Cache side-channels
8. Exception detail leakage
9. Directory listing exposure
10. Configuration file exposure

Domains: Web applications, logging systems, error handling, debugging

Format: JSON array with:
- cwe: "CWE-200"
- cve_id: "CVE-2023-SYNTH-501" to "CVE-2023-SYNTH-520"
- cvss_score: "5.5" to "7.5"
- vulnerable_code: C/C++ code with information exposure
- secure_code: Fixed version with proper sanitization
- explanation: Detailed explanation of what information is exposed and its security impact

Each example should be 10-30 lines of realistic C/C++ code.
```

---

## 🎯 **Recommendation**

### **Immediate (Do Now):**
1. ✅ **Save batches 4-8** (CWE-190) - You already have this data
2. ✅ **Train v3 model** with current data
3. ✅ **Evaluate** to see improvement

### **Phase 2 (After v3 evaluation):**
4. Generate **Batches 9-11** (CWE-189) - 60 samples
5. Generate **Batches 12-14** (CWE-362) - 60 samples
6. Train **v4 model** with fully balanced dataset

### **Phase 3 (Optional):**
7. Generate **Batches 15-16** (CWE-125, CWE-200) - 40 samples
8. Train **v5 model** with perfect balance

---

## 📊 **Expected Final Distribution (v4)**

```
After all recommended batches:

Total: ~2,600 samples

Distribution:
┌─────────┬─────────┬────────┬──────────────────────┐
│ CWE     │ Samples │ %      │ Balance              │
├─────────┼─────────┼────────┼──────────────────────┤
│ CWE-20  │ 350     │ 13.5%  │ ████████████████████ │
│ CWE-119 │ 350     │ 13.5%  │ ████████████████████ │
│ CWE-399 │ 328     │ 12.6%  │ ███████████████████  │
│ CWE-190 │ 295     │ 11.3%  │ █████████████████    │
│ CWE-416 │ 270     │ 10.4%  │ ████████████████     │
│ CWE-362 │ 240     │  9.2%  │ ██████████████       │ ← Balanced!
│ CWE-264 │ 228     │  8.8%  │ █████████████        │
│ CWE-189 │ 229     │  8.8%  │ █████████████        │ ← Balanced!
│ CWE-200 │ 197     │  7.6%  │ ████████████         │
│ CWE-125 │ 176     │  6.8%  │ ███████████          │
└─────────┴─────────┴────────┴──────────────────────┘

Imbalance Ratio: 2.0x (much better than 3.2x!)
```

---

## ✅ **My Recommendation**

**Start with batches 4-8 NOW**, then:

1. **Evaluate v3 performance** on CWE-190/416
2. **If good results**, generate CWE-189/362 batches
3. **If excellent results**, generate remaining batches

**Don't generate everything at once** - validate the approach first! 🎯
