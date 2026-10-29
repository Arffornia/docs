#!/usr/bin/env bash
# Render the Arffornia overlays from the infra repo and turn them into Noodle fragments.
# Each directory is rendered as Argo CD does (kustomize + helm) and discovered with the
# Application's destination namespace: chart objects that name none (the website chart)
# would otherwise land in `default`.
set -euo pipefail
# Portable (bash 3.2, BSD tools): no `realpath -m`, which macOS does not have.
INFRA=${1:?path to the infra repo}; OUT=${2:?output dir}
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd); TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
REF=$(git -C "$INFRA" rev-parse --short HEAD 2>/dev/null || echo unknown)
# dir:destination-namespace, as in k8s/apps/arffornia/**
for entry in server/overlays/arcane:arffornia-server-arcane proxy:arffornia-proxy-velocity \
             website:arffornia-website bluemap-web:arffornia-bluemap-web \
             ../gateway-infra:gateway-infra; do
  d=${entry%%:*}; ns=${entry##*:}; name=${d#../}; name=${name//\//-}
  kustomize build --enable-helm --load-restrictor=LoadRestrictionsNone \
    "$INFRA/k8s/config/arffornia/$d" > "$TMP/$name.yaml"
  # relative input path, so every `src` reads "<name>.yaml", not a temp dir
  (cd "$TMP" && noodle discover k8s "$name.yaml" -namespace "$ns" -ref "infra@$REF" -o "$OUT/k8s-$name.yaml")
done
