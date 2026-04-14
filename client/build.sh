cc -Os -s gemcli.c -o gemcli   -I"$HOME/opt/mbedtls/include"   -L"$HOME/opt/mbedtls/lib64"   -lmbedtls -lmbedx509 -lmbedcrypto
