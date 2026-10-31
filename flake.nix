{
  # Development shells for every Arffornia repo, on Linux (x86_64, arm64) and Apple Silicon Macs.
  # From any clone:  nix develop github:Arffornia/docs#<shell>     (or `.#<shell>` inside this repo)
  # Shells: node (launcher, Nexus libs, provisioning, keycloak theme), java (mod, proxy),
  # php (website), docs (this site, Noodle), infra (kustomize, helm, kubeconform), default (all).
  # See docs/contributing/dev-setup.md.
  description = "Arffornia development shells";

  # Official channel tarball (same content as github:NixOS/nixpkgs/nixos-26.05); `nix flake update` bumps it.
  inputs.nixpkgs.url = "https://channels.nixos.org/nixos-26.05/nixexprs.tar.xz";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs:
        let
          inherit (pkgs) lib stdenv;

          common = with pkgs; [ git gnumake shellcheck actionlint ];

          node = with pkgs; [ nodejs_22 ];

          # Gradle itself comes from each repo's ./gradlew; the foojay toolchain resolver finds this JDK.
          java = with pkgs; [ jdk21 ];

          # Keep in line with composer.json `config.platform.php` in Arffornia_Website.
          php = pkgs.php83.buildEnv {
            extensions = { enabled, all }: enabled ++ (with all; [ pdo_pgsql pgsql zip intl ]);
            extraConfig = "memory_limit = 1G";
          };
          website = [ php pkgs.php83Packages.composer ] ++ node;

          # mkdocs comes from requirements.txt (pip, pinned like CI); Noodle from `go install`.
          # draw.io desktop is Linux-only in nixpkgs: on macOS, `brew install --cask drawio`.
          # kustomize + helm are for `make discover`.
          docs = with pkgs; [ python313 go kustomize kubernetes-helm ] ++ lib.optionals stdenv.isLinux [ drawio ];

          infra = with pkgs; [ kubectl kustomize kubernetes-helm kubeconform ];

          mkShell = name: packages: extraHook: pkgs.mkShell {
            inherit packages;
            shellHook = ''
              export ARFFORNIA_SHELL=${name}
              ${extraHook}
            '';
          };

          javaHook = ''export JAVA_HOME=${pkgs.jdk21.home}'';
          goHook = ''
            export GOPATH="''${GOPATH:-$HOME/go}"
            export PATH="$GOPATH/bin:$PATH"
          '';
        in
        {
          node = mkShell "node" (common ++ node) "";
          java = mkShell "java" (common ++ java) javaHook;
          php = mkShell "php" (common ++ website) "";
          docs = mkShell "docs" (common ++ docs) goHook;
          infra = mkShell "infra" (common ++ infra) "";
          default = mkShell "default" (common ++ node ++ java ++ website ++ docs ++ infra) (javaHook + goHook);
        });
    };
}
