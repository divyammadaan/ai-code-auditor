"""Save CWE-190 batch 1 (image parsers) — 10 valid samples extracted from mixed batch."""
import json

cwe190_samples = [
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-201",
        "cvss_score": "7.8",
        "vulnerable_code": "void* process_bmp_header(int width, int height, int bpp) {\n    int stride = width * (bpp / 8);\n    int total_size = stride * height;\n    if (total_size > 0x1000000) return NULL;\n    unsigned char* buffer = (unsigned char*)malloc(total_size);\n    if (!buffer) return NULL;\n    for (int i = 0; i < height; i++) {\n        read_row(buffer + (i * stride), stride);\n    }\n    return buffer;\n}",
        "secure_code": "void* process_bmp_header(int width, int height, int bpp) {\n    if (width <= 0 || height <= 0 || bpp <= 0) return NULL;\n    long long stride = (long long)width * (bpp / 8);\n    long long total_size = stride * height;\n    if (total_size <= 0 || total_size > 0x1000000) return NULL;\n    unsigned char* buffer = (unsigned char*)malloc((size_t)total_size);\n    if (!buffer) return NULL;\n    for (int i = 0; i < height; i++) {\n        read_row(buffer + (i * (size_t)stride), (size_t)stride);\n    }\n    return buffer;\n}",
        "explanation": "Integer overflow in total_size at line 3. stride * height wraps around to a small positive value, bypassing the size check at line 4 and causing heap buffer overflow during the loop at line 8."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-203",
        "cvss_score": "7.5",
        "vulnerable_code": "int handle_png_chunk(unsigned int len, unsigned int offset) {\n    unsigned int total_needed = len + offset + 8;\n    if (total_needed > MAX_BUFFER_SIZE) return -1;\n    char* data = (char*)malloc(total_needed);\n    if (!data) return -1;\n    memcpy(data + offset, get_raw_stream(), len);\n    return 0;\n}",
        "secure_code": "int handle_png_chunk(unsigned int len, unsigned int offset) {\n    if (len > MAX_BUFFER_SIZE || offset > MAX_BUFFER_SIZE) return -1;\n    unsigned long long total_needed = (unsigned long long)len + offset + 8;\n    if (total_needed > MAX_BUFFER_SIZE) return -1;\n    char* data = (char*)malloc((size_t)total_needed);\n    if (!data) return -1;\n    memcpy(data + offset, get_raw_stream(), len);\n    return 0;\n}",
        "explanation": "Integer overflow in total_needed at line 2. len and offset can sum to a value slightly larger than UINT_MAX, wrapping to a small allocation and causing out-of-bounds memcpy at line 6."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-205",
        "cvss_score": "7.2",
        "vulnerable_code": "size_t calc_jpeg_buffer(int components, short width) {\n    short stride = width * components;\n    size_t sz = stride * 8;\n    return sz;\n}",
        "secure_code": "size_t calc_jpeg_buffer(int components, short width) {\n    if (width <= 0 || components <= 0) return 0;\n    int stride = (int)width * components;\n    if (stride > 32767) return 0;\n    size_t sz = (size_t)stride * 8;\n    return sz;\n}",
        "explanation": "Integer overflow at line 2. stride is a signed short. Large width values cause stride to wrap to a negative or small value, leading to undersized buffer allocations downstream."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-207",
        "cvss_score": "6.8",
        "vulnerable_code": "void process_ws_frame(unsigned short payload_len) {\n    unsigned short header_size = 4;\n    unsigned short total = payload_len + header_size;\n    char* frame = malloc(total);\n    fill_header(frame);\n    read_socket(frame + header_size, payload_len);\n}",
        "secure_code": "void process_ws_frame(unsigned short payload_len) {\n    unsigned int header_size = 4;\n    unsigned int total = (unsigned int)payload_len + header_size;\n    char* frame = malloc(total);\n    if (!frame) return;\n    fill_header(frame);\n    read_socket(frame + header_size, payload_len);\n}",
        "explanation": "Integer overflow at line 3. Adding header_size to payload_len when payload_len is near 65535 wraps the unsigned short total, causing an undersized malloc."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-209",
        "cvss_score": "7.4",
        "vulnerable_code": "int compute_stride(int width, int bpp) {\n    int bits = width * bpp;\n    int stride = (bits + 7) / 8;\n    return stride;\n}",
        "secure_code": "int compute_stride(int width, int bpp) {\n    if (width <= 0 || bpp <= 0 || width > 0x3FFFFFFF) return -1;\n    long long bits = (long long)width * bpp;\n    int stride = (int)((bits + 7) / 8);\n    return stride;\n}",
        "explanation": "Integer overflow at line 2. width * bpp overflows a 32-bit signed integer for large width values, resulting in a negative or incorrect stride used for buffer indexing."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-211",
        "cvss_score": "7.9",
        "vulnerable_code": "char* build_bmp_path(const char* dir, int id) {\n    int len = strlen(dir) + 12;\n    char* path = malloc(len);\n    sprintf(path, \"%s/img_%d.bmp\", dir, id);\n    return path;\n}",
        "secure_code": "char* build_bmp_path(const char* dir, int id) {\n    size_t dir_len = strlen(dir);\n    if (dir_len > 0x7FFFFFFF - 12) return NULL;\n    size_t len = dir_len + 12;\n    char* path = malloc(len);\n    if (!path) return NULL;\n    snprintf(path, len, \"%s/img_%d.bmp\", dir, id);\n    return path;\n}",
        "explanation": "Integer overflow at line 2. If strlen(dir) is near INT_MAX, adding 12 wraps len to a small value, causing heap buffer overflow in sprintf at line 4."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-213",
        "cvss_score": "8.3",
        "vulnerable_code": "void scale_image(int w, int h, int factor) {\n    int new_sz = w * h * factor;\n    char* img = malloc(new_sz);\n    for (int i = 0; i < new_sz; i++) img[i] = 0;\n}",
        "secure_code": "void scale_image(int w, int h, int factor) {\n    if (w <= 0 || h <= 0 || factor <= 0) return;\n    long long check = (long long)w * h * factor;\n    if (check > 0x7FFFFFFF) return;\n    int new_sz = (int)check;\n    char* img = malloc(new_sz);\n    if (!img) return;\n    memset(img, 0, new_sz);\n}",
        "explanation": "Integer overflow at line 2. w * h * factor exceeds INT_MAX and wraps to a small positive number. malloc succeeds but the loop at line 4 writes out of bounds."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-215",
        "cvss_score": "6.9",
        "vulnerable_code": "unsigned int get_bmp_size(unsigned short w, unsigned short h) {\n    return (w * h * 3) + 54;\n}",
        "secure_code": "unsigned int get_bmp_size(unsigned short w, unsigned short h) {\n    unsigned int total = (unsigned int)w * h * 3;\n    if (total > 0xFFFFFFC1) return 0;\n    return total + 54;\n}",
        "explanation": "Integer overflow at line 2. The intermediate w * h * 3 can overflow if the compiler uses 16-bit arithmetic, producing a wrong size that causes undersized allocations downstream."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-217",
        "cvss_score": "7.3",
        "vulnerable_code": "void* alloc_pixels(int width, int height) {\n    int total = width * height;\n    if (total < 1024) total = 1024;\n    return malloc(total * sizeof(int));\n}",
        "secure_code": "void* alloc_pixels(int width, int height) {\n    if (width <= 0 || height <= 0) return NULL;\n    size_t total = (size_t)width * height;\n    if (total > (SIZE_MAX / sizeof(int))) return NULL;\n    size_t bytes = total * sizeof(int);\n    if (bytes < 1024) bytes = 1024;\n    return malloc(bytes);\n}",
        "explanation": "Integer overflow at line 4. total * sizeof(int) overflows if total is large, leading to a small allocation for what should be a large pixel array."
    },
    {
        "cwe": "CWE-190",
        "cve_id": "CVE-2023-SYNTH-219",
        "cvss_score": "6.7",
        "vulnerable_code": "void set_rect(struct rect* r, short w, short h) {\n    r->area = w * h;\n    r->data = malloc(r->area);\n}",
        "secure_code": "void set_rect(struct rect* r, short w, short h) {\n    if (w < 0 || h < 0) return;\n    int area = (int)w * h;\n    r->area = area;\n    r->data = malloc((size_t)area);\n}",
        "explanation": "Integer overflow at line 2. Product of two shorts can exceed signed short capacity, wrapping r->area to a negative or small value before malloc is called."
    }
]

# Bonus CWE-416 samples extracted from the mixed batch
cwe416_bonus = [
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-202",
        "cvss_score": "8.1",
        "vulnerable_code": "void cleanup_connection_pool(struct pool_t* pool) {\n    struct connection* conn = pool->head;\n    while (conn) {\n        struct connection* next = conn->next;\n        if (conn->idle_time > MAX_IDLE) {\n            close(conn->fd);\n            free(conn);\n            log_event(\"Closed idle connection: %d\", conn->fd);\n        }\n        conn = next;\n    }\n}",
        "secure_code": "void cleanup_connection_pool(struct pool_t* pool) {\n    struct connection* conn = pool->head;\n    while (conn) {\n        struct connection* next = conn->next;\n        if (conn->idle_time > MAX_IDLE) {\n            int fd_copy = conn->fd;\n            close(fd_copy);\n            free(conn);\n            log_event(\"Closed idle connection: %d\", fd_copy);\n        }\n        conn = next;\n    }\n}",
        "explanation": "free(conn) at line 7 frees the connection. log_event accesses conn->fd at line 8 on freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-204",
        "cvss_score": "8.2",
        "vulnerable_code": "void http_request_handler(struct http_req* req) {\n    if (req->is_malformed) {\n        free_request(req);\n    }\n    if (req && !req->is_malformed) {\n        process_valid_request(req);\n    } else {\n        log_error(\"Request failed for ID: %d\", req->id);\n    }\n}",
        "secure_code": "void http_request_handler(struct http_req* req) {\n    if (req->is_malformed) {\n        int id = req->id;\n        free_request(req);\n        log_error(\"Request failed for ID: %d\", id);\n        return;\n    }\n    process_valid_request(req);\n}",
        "explanation": "free_request(req) at line 3 frees the request. req->id access in log_error at line 8 then dereferences freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-206",
        "cvss_score": "8.5",
        "vulnerable_code": "void invalidate_session(struct session* s) {\n    hash_remove(session_table, s->token);\n    free(s->user_data);\n    free(s);\n    if (s->type == PERSISTENT) {\n        update_db_session_status(s->token, 0);\n    }\n}",
        "secure_code": "void invalidate_session(struct session* s) {\n    char token_backup[64];\n    strncpy(token_backup, s->token, 63);\n    int type = s->type;\n    hash_remove(session_table, s->token);\n    free(s->user_data);\n    free(s);\n    if (type == PERSISTENT) {\n        update_db_session_status(token_backup, 0);\n    }\n}",
        "explanation": "free(s) at line 4 frees the session. s->type and s->token accesses at lines 5-6 then dereference freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-208",
        "cvss_score": "7.7",
        "vulnerable_code": "void recycle_keep_alive(struct conn_node* node) {\n    if (node->usage_count > MAX_USES) {\n        remove_from_list(node);\n        free(node);\n    }\n    node->last_active = time(NULL);\n    add_to_idle_queue(node);\n}",
        "secure_code": "void recycle_keep_alive(struct conn_node* node) {\n    if (node->usage_count > MAX_USES) {\n        remove_from_list(node);\n        free(node);\n        return;\n    }\n    node->last_active = time(NULL);\n    add_to_idle_queue(node);\n}",
        "explanation": "free(node) at line 4 frees the node. node->last_active write and add_to_idle_queue(node) at lines 6-7 then use freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-210",
        "cvss_score": "8.0",
        "vulnerable_code": "void tls_teardown(struct tls_session* ctx) {\n    tls_send_alert(ctx, CLOSE_NOTIFY);\n    if (ctx->cache_ref) {\n        release_cache(ctx->cache_ref);\n    }\n    free(ctx);\n    cleanup_crypto_backend(ctx->cipher_suite);\n}",
        "secure_code": "void tls_teardown(struct tls_session* ctx) {\n    tls_send_alert(ctx, CLOSE_NOTIFY);\n    int suite = ctx->cipher_suite;\n    if (ctx->cache_ref) {\n        release_cache(ctx->cache_ref);\n    }\n    free(ctx);\n    cleanup_crypto_backend(suite);\n}",
        "explanation": "free(ctx) at line 6 frees the TLS context. ctx->cipher_suite access at line 7 then dereferences freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-212",
        "cvss_score": "7.1",
        "vulnerable_code": "void remove_bmp_from_list(struct list* l, struct node* n) {\n    free(n->data);\n    free(n);\n    if (l->tail == n) {\n        l->tail = NULL;\n    }\n}",
        "secure_code": "void remove_bmp_from_list(struct list* l, struct node* n) {\n    if (l->tail == n) {\n        l->tail = NULL;\n    }\n    free(n->data);\n    free(n);\n}",
        "explanation": "free(n) at line 3 frees the node. l->tail == n comparison at line 4 then uses freed pointer."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-214",
        "cvss_score": "7.6",
        "vulnerable_code": "void process_metadata(struct meta* m) {\n    if (m->version < 2) {\n        upgrade_meta(m);\n        free(m);\n    }\n    printf(\"Processing version: %d\\n\", m->version);\n}",
        "secure_code": "void process_metadata(struct meta* m) {\n    if (m->version < 2) {\n        upgrade_meta(m);\n        free(m);\n        return;\n    }\n    printf(\"Processing version: %d\\n\", m->version);\n}",
        "explanation": "free(m) at line 4 frees the metadata. m->version access in printf at line 6 then dereferences freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-216",
        "cvss_score": "8.4",
        "vulnerable_code": "void handle_client_disconnect(struct client* c) {\n    for (int i = 0; i < c->num_subs; i++) {\n        unsubscribe(c->subs[i]);\n    }\n    free(c->subs);\n    free(c);\n    notify_monitors(c->id, \"disconnected\");\n}",
        "secure_code": "void handle_client_disconnect(struct client* c) {\n    int cid = c->id;\n    for (int i = 0; i < c->num_subs; i++) {\n        unsubscribe(c->subs[i]);\n    }\n    free(c->subs);\n    free(c);\n    notify_monitors(cid, \"disconnected\");\n}",
        "explanation": "free(c) at line 6 frees the client. c->id access in notify_monitors at line 7 then dereferences freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-218",
        "cvss_score": "8.0",
        "vulnerable_code": "void close_session_safe(struct session_t* s) {\n    if (s->is_active) {\n        s->is_active = 0;\n        shutdown_socket(s->sock);\n        free(s);\n    }\n    if (s->log_handle) {\n        close_log(s->log_handle);\n    }\n}",
        "secure_code": "void close_session_safe(struct session_t* s) {\n    if (s->is_active) {\n        s->is_active = 0;\n        shutdown_socket(s->sock);\n        if (s->log_handle) { close_log(s->log_handle); s->log_handle = NULL; }\n        free(s);\n    } else if (s->log_handle) {\n        close_log(s->log_handle);\n        s->log_handle = NULL;\n    }\n}",
        "explanation": "free(s) at line 5 frees the session. s->log_handle access at line 7 then dereferences freed memory."
    },
    {
        "cwe": "CWE-416",
        "cve_id": "CVE-2023-SYNTH-220",
        "cvss_score": "8.2",
        "vulnerable_code": "void cleanup_request_context(struct ctx* c) {\n    free(c->headers);\n    if (c->auth_token) {\n        revoke_token(c->auth_token);\n        free(c->auth_token);\n    }\n    free(c);\n    if (debug_enabled) {\n        syslog(LOG_DEBUG, \"Cleaned ctx %p for user %s\", c, c->user);\n    }\n}",
        "secure_code": "void cleanup_request_context(struct ctx* c) {\n    char user_name[32];\n    strncpy(user_name, c->user, 31);\n    void* old_ptr = c;\n    free(c->headers);\n    if (c->auth_token) { revoke_token(c->auth_token); free(c->auth_token); }\n    free(c);\n    if (debug_enabled) {\n        syslog(LOG_DEBUG, \"Cleaned ctx %p for user %s\", old_ptr, user_name);\n    }\n}",
        "explanation": "free(c) at line 7 frees the context. c->user access in syslog at line 9 then dereferences freed memory."
    }
]

with open("data/synthetic/cwe190_batch1_images.json", "w", encoding="utf-8") as f:
    json.dump(cwe190_samples, f, indent=2)
print(f"CWE-190 batch 1 saved: {len(cwe190_samples)} samples")

with open("data/synthetic/cwe416_batch9_bonus.json", "w", encoding="utf-8") as f:
    json.dump(cwe416_bonus, f, indent=2)
print(f"CWE-416 bonus batch saved: {len(cwe416_bonus)} samples (repurposed from mixed batch)")
print(f"\nTotal CWE-416 so far: 160 + 10 = 170 samples")
print(f"Total CWE-190 so far: 10 samples")
