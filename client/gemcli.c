#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <psa/crypto.h>
#include <mbedtls/net_sockets.h>
#include <mbedtls/ssl.h>
#include <mbedtls/error.h>

static void die_mbedtls(const char *msg, int ret) {
    char buf[256];
    mbedtls_strerror(ret, buf, sizeof(buf));
    fprintf(stderr, "%s: -0x%04x: %s\n", msg, -ret, buf);
    exit(1);
}

static void die_psa(const char *msg, psa_status_t st) {
    fprintf(stderr, "%s: %d\n", msg, (int)st);
    exit(1);
}

int main(int argc, char **argv) {
    const char *host = "geopeedees.org";
    const char *path = "/";
    const char *port = "1965";

    if (argc >= 2) host = argv[1];
    if (argc >= 3) path = argv[2];

    int ret;
    char req[1024];
    unsigned char buf[2048];

    mbedtls_net_context server_fd;
    mbedtls_ssl_context ssl;
    mbedtls_ssl_config conf;

    mbedtls_net_init(&server_fd);
    mbedtls_ssl_init(&ssl);
    mbedtls_ssl_config_init(&conf);

    psa_status_t st = psa_crypto_init();
    if (st != PSA_SUCCESS) die_psa("psa_crypto_init", st);

    ret = mbedtls_net_connect(&server_fd, host, port, MBEDTLS_NET_PROTO_TCP);
    if (ret != 0) die_mbedtls("net_connect", ret);

    ret = mbedtls_ssl_config_defaults(
        &conf,
        MBEDTLS_SSL_IS_CLIENT,
        MBEDTLS_SSL_TRANSPORT_STREAM,
        MBEDTLS_SSL_PRESET_DEFAULT);
    if (ret != 0) die_mbedtls("ssl_config_defaults", ret);

    mbedtls_ssl_conf_authmode(&conf, MBEDTLS_SSL_VERIFY_NONE);

    mbedtls_ssl_conf_min_tls_version(&conf, MBEDTLS_SSL_VERSION_TLS1_2);
    mbedtls_ssl_conf_max_tls_version(&conf, MBEDTLS_SSL_VERSION_TLS1_2);

    ret = mbedtls_ssl_setup(&ssl, &conf);
    if (ret != 0) die_mbedtls("ssl_setup", ret);

    ret = mbedtls_ssl_set_hostname(&ssl, host);
    if (ret != 0) die_mbedtls("ssl_set_hostname", ret);

    mbedtls_ssl_set_bio(&ssl, &server_fd,
                        mbedtls_net_send, mbedtls_net_recv, NULL);

    while ((ret = mbedtls_ssl_handshake(&ssl)) != 0) {
        if (ret != MBEDTLS_ERR_SSL_WANT_READ &&
            ret != MBEDTLS_ERR_SSL_WANT_WRITE) {
            die_mbedtls("ssl_handshake", ret);
        }
    }
    printf("TLS version: %s\n", mbedtls_ssl_get_version(&ssl));
    printf("Cipher: %s\n", mbedtls_ssl_get_ciphersuite(&ssl));

    snprintf(req, sizeof(req), "gemini://%s%s\r\n", host, path);
    fprintf(stderr, ">>> %s", req);

    size_t req_len = strlen(req);
    size_t off = 0;
    while (off < req_len) {
        ret = mbedtls_ssl_write(&ssl,
                                (const unsigned char *)req + off,
                                req_len - off);
        if (ret > 0) {
            off += (size_t)ret;
            continue;
        }
        if (ret != MBEDTLS_ERR_SSL_WANT_READ &&
            ret != MBEDTLS_ERR_SSL_WANT_WRITE) {
            die_mbedtls("ssl_write", ret);
        }
    }

    for (;;) {
        ret = mbedtls_ssl_read(&ssl, buf, sizeof(buf));
        if (ret > 0) {
            fwrite(buf, 1, (size_t)ret, stdout);
            fflush(stdout);
            continue;
        }
        if (ret == 0 || ret == MBEDTLS_ERR_SSL_PEER_CLOSE_NOTIFY) break;
        if (ret == MBEDTLS_ERR_SSL_WANT_READ ||
            ret == MBEDTLS_ERR_SSL_WANT_WRITE) continue;
        die_mbedtls("ssl_read", ret);
    }

    mbedtls_ssl_close_notify(&ssl);
    mbedtls_net_free(&server_fd);
    mbedtls_ssl_free(&ssl);
    mbedtls_ssl_config_free(&conf);
    return 0;
}
