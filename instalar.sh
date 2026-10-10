#!/usr/bin/env bash
# Instala os mods deste repositorio no Claude Code (macOS, Linux ou Git Bash).
# Uso:  bash instalar.sh
set -euo pipefail
MARKETPLACE="Victormartinsilva/MODS-CLAUDECODE"
MARKET_NAME="mods-victor"
PLUGINS=(mod-store flightdeck skins pokemon)
MIN="2.1.287"

CLAUDE="${CLAUDE:-claude}"
ver=$("$CLAUDE" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
if [ -z "$ver" ] || [ "$(printf '%s\n%s\n' "$MIN" "$ver" | sort -V | head -1)" != "$MIN" ]; then
  echo "Precisa do Claude Code $MIN ou superior (encontrado: ${ver:-nenhum})."
  echo "Rode 'claude update', ou aponte para outro binario: CLAUDE=/caminho/claude bash instalar.sh"
  exit 1
fi
echo "Usando $CLAUDE ($ver)"

"$CLAUDE" plugin marketplace add "$MARKETPLACE"

list=$("$CLAUDE" plugin list 2>&1 || true)
fd_id=""
for p in "${PLUGINS[@]}"; do
  id=$(grep -oE "[[:space:]]${p}@[A-Za-z0-9._-]+" <<<"$list" | head -1 | tr -d '[:space:]' || true)
  if [ -n "$id" ]; then
    echo "$p ja instalado como $id"
  else
    id="$p@$MARKET_NAME"; "$CLAUDE" plugin install "$id"
  fi
  [ "$p" = flightdeck ] && fd_id=$id
done

# Ajustes: rotulos do flightdeck em portugues.
"$CLAUDE" plugin install "$fd_id" --config architectLabel=ARQUITETO --config "gateLabel=PERMISSÕES"

cat <<'EOF'

Pronto. No Claude Code, rode:
  /reload-plugins
  /skin dracula
  /skin band off
  /pokemon abra
EOF
