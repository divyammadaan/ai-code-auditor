"""
Load CVE/CWE vulnerability patterns for ingestion into the vector store.

Sources:
  1. Embedded CWE descriptions (top 25 most dangerous CWEs — MITRE 2023)
  2. Secure coding pattern examples
  3. Optional: NVD CVE JSON feed (if downloaded)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger


@dataclass
class VulnerabilityPattern:
    """A single vulnerability pattern document for the vector store."""
    id: str                          # e.g. "CWE-79" or "CVE-2021-44228"
    title: str
    description: str
    category: str                    # "CWE" or "CVE"
    severity: Optional[str] = None   # "Critical", "High", "Medium", "Low"
    secure_pattern: Optional[str] = None  # Example of secure code pattern
    tags: list[str] = field(default_factory=list)

    def to_document(self) -> str:
        """Format as a rich text document for embedding."""
        parts = [
            f"ID: {self.id}",
            f"Title: {self.title}",
            f"Category: {self.category}",
        ]
        if self.severity:
            parts.append(f"Severity: {self.severity}")
        parts.append(f"Description: {self.description}")
        if self.secure_pattern:
            parts.append(f"Secure Pattern:\n{self.secure_pattern}")
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        return "\n".join(parts)

    def to_metadata(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity or "Unknown",
            "tags": ",".join(self.tags),
        }


# ---------------------------------------------------------------------------
# Top 25 CWE patterns (MITRE 2023 CWE Top 25)
# ---------------------------------------------------------------------------

CWE_PATTERNS: list[VulnerabilityPattern] = [
    VulnerabilityPattern(
        id="CWE-787",
        title="Out-of-bounds Write",
        description=(
            "The software writes data past the end, or before the beginning, of the intended buffer. "
            "This can corrupt data, crash the program, or allow execution of arbitrary code."
        ),
        category="CWE",
        severity="Critical",
        secure_pattern=(
            "// INSECURE: strcpy(dest, src);\n"
            "// SECURE: use strncpy with explicit size check\n"
            "if (strlen(src) < sizeof(dest)) {\n"
            "    strncpy(dest, src, sizeof(dest) - 1);\n"
            "    dest[sizeof(dest) - 1] = '\\0';\n"
            "}"
        ),
        tags=["buffer-overflow", "memory-safety", "C", "C++"],
    ),
    VulnerabilityPattern(
        id="CWE-79",
        title="Cross-site Scripting (XSS)",
        description=(
            "The software does not neutralize or incorrectly neutralizes user-controllable input "
            "before it is placed in output that is used as a web page served to other users."
        ),
        category="CWE",
        severity="High",
        secure_pattern=(
            "# INSECURE: return f'<div>{user_input}</div>'\n"
            "# SECURE: escape HTML entities\n"
            "import html\n"
            "return f'<div>{html.escape(user_input)}</div>'"
        ),
        tags=["xss", "injection", "web", "python", "javascript"],
    ),
    VulnerabilityPattern(
        id="CWE-89",
        title="SQL Injection",
        description=(
            "The software constructs all or part of an SQL command using externally-influenced input "
            "without neutralizing special elements that could modify the intended SQL command."
        ),
        category="CWE",
        severity="Critical",
        secure_pattern=(
            "# INSECURE: query = 'SELECT * FROM users WHERE id = ' + user_id\n"
            "# SECURE: use parameterized queries\n"
            "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
        ),
        tags=["sql-injection", "injection", "database"],
    ),
    VulnerabilityPattern(
        id="CWE-416",
        title="Use After Free",
        description=(
            "Referencing memory after it has been freed can cause a program to crash, use unexpected "
            "values, or execute code. Common in C/C++ when a pointer is used after free()."
        ),
        category="CWE",
        severity="Critical",
        secure_pattern=(
            "// INSECURE:\n"
            "// free(ptr);\n"
            "// use(ptr);  // undefined behavior\n"
            "// SECURE: set pointer to NULL after free\n"
            "free(ptr);\n"
            "ptr = NULL;"
        ),
        tags=["use-after-free", "memory-safety", "C", "C++"],
    ),
    VulnerabilityPattern(
        id="CWE-125",
        title="Out-of-bounds Read",
        description=(
            "The software reads data past the end, or before the beginning, of the intended buffer. "
            "This typically leads to information disclosure or crashes."
        ),
        category="CWE",
        severity="High",
        secure_pattern=(
            "// INSECURE: val = arr[user_index];\n"
            "// SECURE: bounds check before access\n"
            "if (user_index >= 0 && user_index < arr_size) {\n"
            "    val = arr[user_index];\n"
            "} else {\n"
            "    handle_error(\"Index out of bounds\");\n"
            "}"
        ),
        tags=["out-of-bounds", "memory-safety", "C", "C++"],
    ),
    VulnerabilityPattern(
        id="CWE-20",
        title="Improper Input Validation",
        description=(
            "The product receives input or data, but it does not validate or incorrectly validates "
            "that the input has the properties required for safe and correct processing."
        ),
        category="CWE",
        severity="High",
        secure_pattern=(
            "# INSECURE: process(user_data)\n"
            "# SECURE: validate before processing\n"
            "def process_safe(user_data):\n"
            "    if not isinstance(user_data, str):\n"
            "        raise ValueError('Expected string input')\n"
            "    if len(user_data) > MAX_LENGTH:\n"
            "        raise ValueError('Input too long')\n"
            "    sanitized = sanitize(user_data)\n"
            "    return process(sanitized)"
        ),
        tags=["input-validation", "injection"],
    ),
    VulnerabilityPattern(
        id="CWE-476",
        title="NULL Pointer Dereference",
        description=(
            "A NULL pointer dereference occurs when the application dereferences a pointer that it "
            "expects to be valid, but is NULL, typically causing a crash."
        ),
        category="CWE",
        severity="Medium",
        secure_pattern=(
            "// INSECURE: ptr->value = 42;\n"
            "// SECURE: check for NULL before dereferencing\n"
            "if (ptr != NULL) {\n"
            "    ptr->value = 42;\n"
            "} else {\n"
            "    log_error(\"Null pointer encountered\");\n"
            "}"
        ),
        tags=["null-pointer", "memory-safety", "C", "C++"],
    ),
    VulnerabilityPattern(
        id="CWE-119",
        title="Improper Restriction of Operations within Bounds of a Memory Buffer",
        description=(
            "The software performs operations on a memory buffer, but it can read from or write to "
            "a memory location that is outside of the intended boundary of the buffer."
        ),
        category="CWE",
        severity="Critical",
        secure_pattern=(
            "// INSECURE: gets(buffer);  // no bounds checking\n"
            "// SECURE: use fgets with explicit size\n"
            "fgets(buffer, sizeof(buffer), stdin);"
        ),
        tags=["buffer-overflow", "memory-safety", "C", "C++"],
    ),
    VulnerabilityPattern(
        id="CWE-22",
        title="Path Traversal",
        description=(
            "The software uses external input to construct a pathname intended to identify a file "
            "or directory, but does not neutralize sequences such as '../' that can resolve to "
            "a location outside the intended directory."
        ),
        category="CWE",
        severity="High",
        secure_pattern=(
            "import os\n"
            "# INSECURE: open(base_dir + user_path)\n"
            "# SECURE: resolve and validate path\n"
            "def safe_open(base_dir, user_path):\n"
            "    safe_path = os.path.realpath(os.path.join(base_dir, user_path))\n"
            "    if not safe_path.startswith(os.path.realpath(base_dir)):\n"
            "        raise ValueError('Path traversal detected')\n"
            "    return open(safe_path)"
        ),
        tags=["path-traversal", "file-system", "injection"],
    ),
    VulnerabilityPattern(
        id="CWE-190",
        title="Integer Overflow or Wraparound",
        description=(
            "The software performs a calculation that can produce an integer overflow or wraparound, "
            "when the logic assumes that the resulting value will always be larger than the original value."
        ),
        category="CWE",
        severity="High",
        secure_pattern=(
            "// INSECURE: size_t total = a * b;  // may overflow\n"
            "// SECURE: check for overflow before multiplication\n"
            "#include <limits.h>\n"
            "if (b != 0 && a > SIZE_MAX / b) {\n"
            "    handle_error(\"Integer overflow\");\n"
            "} else {\n"
            "    size_t total = a * b;\n"
            "}"
        ),
        tags=["integer-overflow", "arithmetic", "C", "C++"],
    ),
    VulnerabilityPattern(
        id="CWE-502",
        title="Deserialization of Untrusted Data",
        description=(
            "The application deserializes untrusted data without sufficiently verifying that the "
            "resulting data will be valid, leading to remote code execution or other attacks."
        ),
        category="CWE",
        severity="Critical",
        secure_pattern=(
            "# INSECURE: obj = pickle.loads(user_data)\n"
            "# SECURE: use safe serialization formats\n"
            "import json\n"
            "obj = json.loads(user_data)  # JSON is safe for data exchange\n"
            "# Or validate with a schema before deserializing"
        ),
        tags=["deserialization", "rce", "python", "java"],
    ),
    VulnerabilityPattern(
        id="CWE-798",
        title="Use of Hard-coded Credentials",
        description=(
            "The software contains hard-coded credentials, such as a password or cryptographic key, "
            "which it uses for its own inbound authentication or for outbound communication."
        ),
        category="CWE",
        severity="Critical",
        secure_pattern=(
            "# INSECURE: password = 'admin123'\n"
            "# SECURE: load from environment variables\n"
            "import os\n"
            "password = os.environ.get('DB_PASSWORD')\n"
            "if not password:\n"
            "    raise EnvironmentError('DB_PASSWORD not set')"
        ),
        tags=["hardcoded-credentials", "secrets", "authentication"],
    ),
]


# ---------------------------------------------------------------------------
# Secure coding patterns (style guide examples)
# ---------------------------------------------------------------------------

SECURE_PATTERNS: list[VulnerabilityPattern] = [
    VulnerabilityPattern(
        id="PATTERN-001",
        title="Parameterized Database Queries",
        description="Always use parameterized queries or prepared statements to prevent SQL injection.",
        category="SECURE_PATTERN",
        severity=None,
        secure_pattern=(
            "# Python (psycopg2)\n"
            "cursor.execute('SELECT * FROM users WHERE email = %s AND active = %s', (email, True))\n\n"
            "# Java (PreparedStatement)\n"
            "PreparedStatement stmt = conn.prepareStatement(\n"
            "    'SELECT * FROM users WHERE email = ? AND active = ?');\n"
            "stmt.setString(1, email);\n"
            "stmt.setBoolean(2, true);"
        ),
        tags=["sql", "database", "injection-prevention"],
    ),
    VulnerabilityPattern(
        id="PATTERN-002",
        title="Secure Password Hashing",
        description="Use bcrypt, scrypt, or Argon2 for password hashing. Never use MD5 or SHA1.",
        category="SECURE_PATTERN",
        secure_pattern=(
            "import bcrypt\n"
            "# Hash a password\n"
            "hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))\n"
            "# Verify a password\n"
            "is_valid = bcrypt.checkpw(password.encode(), hashed)"
        ),
        tags=["authentication", "passwords", "cryptography"],
    ),
    VulnerabilityPattern(
        id="PATTERN-003",
        title="Memory-Safe String Operations in C",
        description="Use strlcpy/strlcat or snprintf instead of strcpy/strcat/sprintf.",
        category="SECURE_PATTERN",
        secure_pattern=(
            "// Use snprintf for safe string formatting\n"
            "char buf[256];\n"
            "snprintf(buf, sizeof(buf), \"Hello, %s!\", username);\n\n"
            "// Use strnlen to safely get string length\n"
            "size_t len = strnlen(input, MAX_INPUT_LEN);"
        ),
        tags=["C", "C++", "memory-safety", "strings"],
    ),
]


# ---------------------------------------------------------------------------
# Loader functions
# ---------------------------------------------------------------------------

def load_all_patterns() -> list[VulnerabilityPattern]:
    """Return all built-in CWE and secure coding patterns."""
    return CWE_PATTERNS + SECURE_PATTERNS


def load_nvd_cves(nvd_json_path: Path) -> list[VulnerabilityPattern]:
    """
    Load CVE entries from an NVD JSON feed file.
    Download from: https://nvd.nist.gov/vuln/data-feeds
    """
    if not nvd_json_path.exists():
        logger.warning(f"NVD JSON file not found: {nvd_json_path}. Skipping.")
        return []

    logger.info(f"Loading NVD CVEs from {nvd_json_path}...")
    with open(nvd_json_path) as f:
        data = json.load(f)

    patterns = []
    for item in data.get("CVE_Items", []):
        try:
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            description = item["cve"]["description"]["description_data"][0]["value"]
            cvss_score = (
                item.get("impact", {})
                .get("baseMetricV3", {})
                .get("cvssV3", {})
                .get("baseScore", None)
            )
            severity = _cvss_to_severity(cvss_score)
            patterns.append(
                VulnerabilityPattern(
                    id=cve_id,
                    title=f"CVE: {cve_id}",
                    description=description,
                    category="CVE",
                    severity=severity,
                    tags=["cve", "nvd"],
                )
            )
        except (KeyError, IndexError):
            continue

    logger.info(f"Loaded {len(patterns):,} CVE patterns from NVD feed.")
    return patterns


def _cvss_to_severity(score: float | None) -> str:
    """Convert CVSS score to severity label."""
    if score is None:
        return "Unknown"
    if score >= 9.0:
        return "Critical"
    if score >= 7.0:
        return "High"
    if score >= 4.0:
        return "Medium"
    return "Low"
