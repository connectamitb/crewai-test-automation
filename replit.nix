{pkgs}: {
  deps = [
    pkgs.libyaml
    pkgs.libxcrypt
    pkgs.bash
    pkgs.postgresql
    pkgs.openssl
  ];
}
